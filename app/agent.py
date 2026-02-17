# agent.py
import json
from datetime import datetime,timedelta
import re
from typing import Dict, Any
import traceback
from dateutil import parser

from llm_clients import call_llm_json
from prompts import build_system_prompt
from reservations import (
    search_restaurants,
    create_reservation,
    cancel_reservation,
    check_availability,
    list_reservations,
)
from tools import TOOL_SPECS


def parse_llm_response(text: str) -> Dict[str, Any]:
    if not text or not isinstance(text, str):
        print("Error: Empty or invalid response from LLM")
        return {
            "intent": "clarify",
            "params": {
                "question": "I didn't get a valid response. Could you try again?"
            },
        }

    text = text.strip()
    print(f"Parsing LLM response (first 200 chars): {text[:200]!r}")

    try:
        result = json.loads(text)
        if isinstance(result, dict) and "intent" in result:
            return result
    except json.JSONDecodeError:
        pass

    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = text[start:end]
            print(f"Trying to parse extracted JSON: {json_str}")
            result = json.loads(json_str)
            if isinstance(result, dict) and "intent" in result:
                return result
    except Exception as e:
        print(f"Unexpected error parsing LLM response: {e}")
        traceback.print_exc()

    return {
        "intent": "clarify",
        "params": {
            "question": (
                "I'm having trouble understanding your request. Could you rephrase it? "
                "For example: 'Book a table for 2 at 7pm tomorrow' or "
                "'Find Italian restaurants for 4 people'."
            )
        },
    }


def resolve_reservation_datetime(user_text: str, dt_text: str | None) -> datetime:
    text = user_text.lower()
    now = datetime.now()

    if "tomorrow" in text or "today" in text or "tonight" in text:
        base = now
        if "tomorrow" in text:
            base = now + timedelta(days=1)

        hour = 19
        minute = 0

        m = re.search(r"(\d{1,2})\s*[:\.]\s*(\d{2})\s*(am|pm)?", text)
        if m:
            hour = int(m.group(1))
            minute = int(m.group(2))
            ampm = m.group(3)
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
        else:
            m = re.search(r"\b(\d{1,2})\s*(am|pm)\b", text)
            if m:
                hour = int(m.group(1))
                ampm = m.group(2)
                if ampm == "pm" and hour < 12:
                    hour += 12
                elif ampm == "am" and hour == 12:
                    hour = 0
            else:
                m = re.search(r"\bat\s+(\d{1,2})\b", text)
                if m:
                    h = int(m.group(1))
                    if 0 < h < 24:
                        hour = h

        return base.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if dt_text:
        try:
            return parser.parse(dt_text, default=now)
        except Exception:
            pass

    return now.replace(hour=19, minute=0, second=0, microsecond=0)


def handle_user_message(user_text: str) -> str:
    try:
        system_prompt = build_system_prompt()
        raw = call_llm_json(system_prompt, user_text)
        parsed = parse_llm_response(raw)

        intent = parsed.get("intent")
        params = parsed.get("params", {}) or {}

        print(f"LLM chose intent/tool: {intent}, params: {params}")

        if intent not in TOOL_SPECS:
            return (
                "I couldn't match your request to a known action. "
                "Please try again with a clearer request."
            )

        if intent == "search_restaurants":
            cuisine = params.get("cuisine")
            seats = params.get("seats")
            features = params.get("features")
            results = search_restaurants(
                cuisine=cuisine, seats=seats, feature_filters=features
            )
            if not results:
                return (
                    "No restaurants match your filters. "
                    "Try removing constraints or asking for general suggestions."
                )
            lines = [
                f"{r.id}: {r.name} — {r.cuisine} — capacity {r.capacity} — "
                f"features: {', '.join(r.features) or 'none'}"
                for r in results[:10]
            ]
            return "Here are some options:\n" + "\n".join(lines)

        # ==============================
        # UPDATED create_reservation LOGIC
        # ==============================
        if intent == "create_reservation":
            seats = int(params.get("seats", 2))
            cuisine = params.get("cuisine")
            # Always try catch restaurant name first even if LLM provides restaurant_id
            from reservations import RESTAURANTS
            lowered = user_text.lower()

            name_matches = [
                r for r in RESTAURANTS.values()
                if r.name.lower() in lowered
            ]

            if name_matches:
                rid = name_matches[0].id
            else:
                # fallback to provided restaurant_id
                if params.get("restaurant_id") is not None:
                    rid = int(params.get("restaurant_id"))
                else:
                    candidates = search_restaurants(cuisine=cuisine, seats=seats)
                    candidates = sorted(candidates, key=lambda r: r.capacity)
                    if not candidates:
                        return "No restaurant found that can handle your seating request."
                    rid = candidates[0].id


            dt_text = params.get("datetime")
            dt = resolve_reservation_datetime(user_text, dt_text)
            name = params.get("name", "Guest")
            phone = params.get("phone")
            email = params.get("email")

            if not check_availability(rid, dt, seats):
                return "That time is fully booked. Would you like alternate times or restaurants?"

            res = create_reservation(rid, dt, seats, name, phone, email)
            from reservations import RESTAURANTS
            rest = RESTAURANTS[rid]

            formatted_date = dt.strftime('%A, %d %B %Y at %I:%M %p')
            return (
                "🎉 **Reservation Confirmed!**\n\n"
                f"**Restaurant ID (Code):** {rest.id}\n\n"
                f"**Restaurant:** {rest.name} ({rest.cuisine})\n\n"
                f"**Address:** {rest.address}\n\n"
                f"**Date & Time:** {formatted_date}\n\n"
                f"**Seats Reserved:** {seats}\n\n"
                "🍽 Thank you for choosing **GoodFoods**!"
            )

        if intent == "cancel_reservation":
            rest_code = params.get("reservation_id")
            if not rest_code and user_text:
                match = re.search(r'(?:id[=: ]*|#)?(\d+)', user_text)
                if match:
                    rest_code = match.group(1)

            if not rest_code:
                reservations = list_reservations()
                if reservations:
                    reservations_list = "\n".join(
                        [
                            f"- Restaurant Code: {r['restaurant_id']} | Reservation ID: {r['id']} | "
                            f"{r['datetime']} | {r['seats']} seats | {r['status']}"
                            for r in reservations
                        ]
                    )
                    return (
                        "Please provide a Restaurant Code to cancel.\n\n"
                        "Your current reservations:\n" + reservations_list
                    )
                else:
                    return "You don't have any active reservations to cancel."

            try:
                rest_code = int(rest_code)
                reservations = list_reservations()

                target = None
                for r in reversed(reservations):
                    if r["restaurant_id"] == rest_code and r["status"] == "confirmed":
                        target = r
                        break

                if not target:
                    return (
                        f"❌ No active reservations found for Restaurant Code {rest_code}. "
                        "Please check and try again."
                    )

                success = cancel_reservation(target["id"])
                if success:
                    return (
                        f"🗑 Successfully cancelled reservation at restaurant code {rest_code}.\n"
                        f"(Reservation ID #{target['id']})"
                    )
                else:
                    return (
                        f"❌ Could not cancel reservation for restaurant code {rest_code}. "
                        "Please try again."
                    )

            except ValueError:
                return "❌ Invalid code. Please say something like: cancel reservation 16"

        if intent == "list_reservations":
            rows = list_reservations()
            if not rows:
                return "No reservations yet."
            lines = [
                f"#{r['id']} | Rest {r['restaurant_id']} | {r['datetime']} | "
                f"{r['seats']} seats | {r['name']} | {r['status']}"
                for r in rows
            ]
            return "\n".join(lines)

        if intent == "clarify":
            q = params.get("question", "Could you clarify your request?")
            return q

        return (
            "I understood your message but couldn't map it to a supported action. "
            "Please try again, for example: 'Book a table for 4 at 7pm tomorrow'."
        )

    except Exception as e:
        traceback.print_exc()
        return f"Error handling message: {str(e)}"
