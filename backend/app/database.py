"""
Placeholder database module.

⚠️ This is a stub awaiting Dev A's final implementation.
The actual `get_db()` function should yield an AsyncSession
from SQLAlchemy's async session factory.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session.

    Raises:
        NotImplementedError: This is a placeholder — Dev A will provide the real implementation.
    """
    raise NotImplementedError(
        "get_db() is a placeholder. Dev A must provide the actual database session factory."
    )
    yield  # noqa: unreachable — keeps this as an async generator for type-checking
