"""
Placeholder user utility module.

⚠️ This is a stub awaiting Dev A's final implementation.
The actual `get_current_user_id` function should extract the user ID
from the request (e.g., from the X-User-ID header or auth token).
"""
from fastapi import Header


async def get_current_user_id(x_user_id: str = Header(...)) -> str:
    """Extract user ID from the X-User-ID request header.

    This is a minimal placeholder. Dev A may replace this with
    a token-based implementation.
    """
    return x_user_id
