import os
import json
import traceback
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not GROQ_API_KEY:
    print("⚠️ GROQ_API_KEY is missing. Add it in .env (local) or Streamlit secrets (cloud).")

client = Groq(api_key=GROQ_API_KEY)


def call_llm_json(system_prompt: str, user_text: str) -> str:
    """
    Calls Groq API and returns ONLY JSON text (string).
    This matches your agent.py pipeline which expects a JSON string.
    """
    print(f"\n=== USER MESSAGE: {user_text} ===")

    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0,
            # This forces the output to be valid JSON
            response_format={"type": "json_object"},
        )

        content = resp.choices[0].message.content.strip()
        print(f"LLM Response: {content}")
        return content

    except Exception as e:
        print("❌ Groq API call failed.")
        traceback.print_exc()

        # fallback response (so your app never hard-crashes)
        return json.dumps({
            "intent": "clarify",
            "params": {
                "question": "I couldn't reach the AI service. Please try again in a moment."
            }
        })
