# llm_clients.py  (Clean version: ONLY Llama, NO OpenAI)
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

LLAMA_CPP_MODEL_PATH = os.getenv("LLAMA_CPP_MODEL_PATH")
if LLAMA_CPP_MODEL_PATH:
    LLAMA_CPP_MODEL_PATH = os.path.abspath(LLAMA_CPP_MODEL_PATH)
    print(f"Using Llama model at: {LLAMA_CPP_MODEL_PATH}")
    if not os.path.exists(LLAMA_CPP_MODEL_PATH):
        print(f"Warning: Llama model not found at {LLAMA_CPP_MODEL_PATH}")
        LLAMA_CPP_MODEL_PATH = None


def _heuristic_stub(user_text: str) -> str:
    """
    Backup if Llama is not available.
    """
    t = user_text.lower()

    if 'book' in t or 'reserve' in t or 'table' in t:
        seats = 2
        for tok in t.split():
            if tok.isdigit():
                seats = int(tok)
                break

        dt = datetime.now()
        if 'tomorrow' in t:
            dt = dt + timedelta(days=1)

        return json.dumps({
            "intent": "create_reservation",
            "params": {
                "seats": seats,
                "datetime": dt.isoformat(),
                "name": "Guest"
            }
        })

    if 'cancel' in t:
        rid = None
        for tok in t.split():
            if tok.isdigit():
                rid = int(tok)
                break

        if rid:
            return json.dumps({"intent": "cancel_reservation", "params": {"reservation_id": rid}})
        return json.dumps({"intent": "clarify", "params": {"question": "Provide ID to cancel"}})

    if 'find' in t or 'suggest' in t or 'recommend' in t or 'where' in t:
        cuisine = None
        seats = None
        for cu in ['indian','italian','chinese','mexican','mediterranean','japanese','french','american','thai','korean']:
            if cu in t:
                cuisine = cu
        for tok in t.split():
            if tok.isdigit():
                seats = int(tok)
                break
        return json.dumps({"intent": "search_restaurants", "params": {"cuisine": cuisine, "seats": seats}})

    return json.dumps({
        "intent": "clarify",
        "params": {"question": "I didn't understand — do you want to book, cancel or search?"}
    })


def call_llama_cpp(system_prompt: str, user_text: str, max_tokens: int = 512) -> str:
    """
    Primary Llama-3.3-8b interaction using llama-cpp-python (local or server mode).
    """
    try:
        from llama_cpp import Llama

        if not LLAMA_CPP_MODEL_PATH or not os.path.exists(LLAMA_CPP_MODEL_PATH):
            print("Llama model missing, using stub fallback.")
            return _heuristic_stub(user_text)

        llm = Llama(
            model_path=LLAMA_CPP_MODEL_PATH,
            n_ctx=4096,
            n_threads=6,  # adjust based on CPU
            n_gpu_layers=0,
            verbose=False
        )

        enhanced_prompt = f"""{system_prompt}

Return only valid JSON tool call responses.
"""

        messages = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": user_text}
        ]

        result = llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1,
            top_p=0.9,
            stop=["User:"]
        )

        response_text = result["choices"][0]["message"]["content"].strip()

        if not (response_text.startswith("{") and response_text.endswith("}")):
            print("Model response not JSON — using stub fallback")
            return _heuristic_stub(user_text)

        return response_text

    except Exception as e:
        print(f"Error running Llama model: {e}")
        return _heuristic_stub(user_text)


def call_llm_json(system_prompt: str, user_text: str) -> str:
    """
    Single public entry for the agent.
    """
    print(f"\n=== USER MESSAGE: {user_text} ===")

    if LLAMA_CPP_MODEL_PATH and os.path.exists(LLAMA_CPP_MODEL_PATH):
        response = call_llama_cpp(system_prompt, user_text)
    else:
        print("No Llama available → using fallback heuristic.")
        response = _heuristic_stub(user_text)

    print(f"LLM Response: {response}")
    return response
