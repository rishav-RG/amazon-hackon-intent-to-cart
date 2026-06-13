"""
Async database connectivity module.

Provides SQLAlchemy async engine, session factory, and FastAPI dependency
for database session injection.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.exceptions import AppException, DB_CONNECTION_ERROR

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Wraps connection failures in AppException with DB_CONNECTION_ERROR code.
    """
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            error_code=DB_CONNECTION_ERROR[0],
            message=f"Database connection failed: {exc}",
            status_code=DB_CONNECTION_ERROR[1],
        ) from exc


async def dispose_engine() -> None:
    """Dispose of the async engine, closing all pooled connections.

    Should be called during application shutdown.
    """
    await engine.dispose()
