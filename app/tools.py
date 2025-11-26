# tools.py
"""
MCP-style tool registry and specs for the GoodFoods reservation agent.

This file defines:
- TOOL_SPECS: metadata & JSON schemas for tools
- list_tools_for_prompt(): renders tools in a format the LLM can use
"""

from typing import Dict, Any, List

TOOL_SPECS: Dict[str, Dict[str, Any]] = {
    "search_restaurants": {
        "description": "Search restaurants by cuisine, party size, and features.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cuisine": {"type": "string", "description": "Preferred cuisine, e.g. 'Italian'"},
                "seats": {"type": "integer", "description": "Number of people"},
                "features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Desired features, e.g. ['outdoor', 'parking']"
                }
            },
            "required": [],
            "additionalProperties": False
        }
    },
    "create_reservation": {
        "description": "Create a reservation at a restaurant for a specific date/time.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "restaurant_id": {"type": "integer", "description": "ID of the restaurant"},
                "cuisine": {"type": "string", "description": "Cuisine preference if restaurant_id is not provided"},
                "seats": {"type": "integer", "description": "Number of people"},
                "datetime": {
                    "type": "string",
                    "description": "ISO 8601 datetime string, e.g. '2025-11-26T19:00:00'"
                },
                "name": {"type": "string", "description": "Name for the reservation"},
                "phone": {"type": "string", "description": "Phone number"},
                "email": {"type": "string", "description": "Email address"}
            },
            "required": ["seats", "datetime"],
            "additionalProperties": False
        }
    },
    "cancel_reservation": {
        "description": "Cancel an existing reservation by its numeric ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "reservation_id": {"type": "integer", "description": "Reservation ID to cancel"}
            },
            "required": ["reservation_id"],
            "additionalProperties": False
        }
    },
    "list_reservations": {
        "description": "List recent reservations for admin/debug purposes.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        }
    },
    "clarify": {
        "description": "Ask the user for clarification when the request is ambiguous.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Clarifying question to ask the user"}
            },
            "required": ["question"],
            "additionalProperties": False
        }
    }
}


def list_tools_for_prompt() -> str:
    """
    Render the tools in a text format to inject into the system prompt,
    MCP-style: name, description, and JSON schema.
    """
    lines: List[str] = []
    lines.append("You have access to the following tools (MCP-style):")
    for name, spec in TOOL_SPECS.items():
        lines.append(f"- Tool name: {name}")
        lines.append(f"  Description: {spec['description']}")
        lines.append("  Input JSON schema:")
        lines.append(f"  {spec['inputSchema']}")
        lines.append("")
    lines.append(
        "When you decide what to do, respond with a SINGLE JSON object:\n"
        "{\n"
        '  "intent": "<tool_name>",\n'
        '  "params": { ... arguments according to the inputSchema ... }\n'
        "}\n"
        "Do NOT include any other text outside the JSON."
    )
    return "\n".join(lines)
