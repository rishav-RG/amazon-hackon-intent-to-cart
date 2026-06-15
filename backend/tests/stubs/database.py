"""
Async database session mock for testing.

Provides a mock AsyncSession factory that can be used as a dependency override
for `app.database.get_db`. Uses unittest.mock.AsyncMock so tests can configure
return values and assert calls without requiring aiosqlite or a real database.
"""

from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock


def create_mock_session() -> AsyncMock:
    """Create a mock AsyncSession with standard async ORM operations.

    The returned mock supports:
      - session.add(instance)        — synchronous, records the added object
      - session.commit()             — async no-op
      - session.refresh(instance)    — async no-op
      - session.flush()              — async no-op
      - session.rollback()           — async no-op
      - session.close()              — async no-op
      - session.execute(statement)   — async, returns a mock result
      - session.get(Model, pk)       — async, returns None by default

    Tests can override any of these via normal Mock configuration, e.g.:
        session.execute.return_value = mock_result
        session.get.return_value = some_model_instance
    """
    session = AsyncMock()

    # `add` is synchronous in SQLAlchemy — use a regular MagicMock
    session.add = MagicMock()

    # Provide a default execute result with scalars().first() / scalars().all()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_scalars.all.return_value = []
    mock_scalars.one_or_none.return_value = None

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = None

    session.execute.return_value = mock_result

    # session.get returns None by default (model not found)
    session.get.return_value = None

    return session


async def get_test_db() -> AsyncGenerator[AsyncMock, None]:
    """Async generator yielding a mock session — mirrors `app.database.get_db`.

    Usage as a FastAPI dependency override:
        from tests.stubs.database import get_test_db
        app.dependency_overrides[get_db] = get_test_db
    """
    session = create_mock_session()
    try:
        yield session
    finally:
        await session.close()


def make_session_with_data(execute_return=None, get_return=None) -> AsyncMock:
    """Create a pre-configured mock session with custom query results.

    Args:
        execute_return: Value to return from session.execute().scalars().first()
                        If a list, also populates scalars().all().
        get_return: Value to return from session.get().

    Returns:
        A configured AsyncMock session ready for injection into services.
    """
    session = create_mock_session()

    if execute_return is not None:
        mock_scalars = MagicMock()
        if isinstance(execute_return, list):
            mock_scalars.first.return_value = execute_return[0] if execute_return else None
            mock_scalars.all.return_value = execute_return
            mock_scalars.one_or_none.return_value = execute_return[0] if execute_return else None
        else:
            mock_scalars.first.return_value = execute_return
            mock_scalars.all.return_value = [execute_return]
            mock_scalars.one_or_none.return_value = execute_return

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_result.scalar_one_or_none.return_value = (
            execute_return[0] if isinstance(execute_return, list) and execute_return
            else execute_return
        )
        session.execute.return_value = mock_result

    if get_return is not None:
        session.get.return_value = get_return

    return session
