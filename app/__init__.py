"""
GoodFoods Reservation Assistant package.

This exposes the main agent entrypoint so it can be imported as:
    from app import handle_user_message
"""

from .agent import handle_user_message

__all__ = ["handle_user_message"]
