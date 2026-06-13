"""
Application configuration settings.
Temporary stub - to be replaced by Dev A's implementation.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/intent_cart_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Developer B - Bundle Engine Configuration
    # Ranking Engine - Weighted Formula Weights (must sum to 1.0)
    RANKING_WEIGHT_INTENT_MATCH: float = 0.30
    RANKING_WEIGHT_INVENTORY: float = 0.25
    RANKING_WEIGHT_ETA: float = 0.15
    RANKING_WEIGHT_PERSONALIZATION: float = 0.20
    RANKING_WEIGHT_COMPLETENESS: float = 0.10
    
    # Mock Inventory Adapter
    MOCK_INVENTORY_OOS_RATE: float = 0.15  # 15% of products flagged as out-of-stock
    
    # Mock ETA Adapter
    MOCK_ETA_MIN_MINUTES: int = 20   # Minimum delivery time
    MOCK_ETA_MAX_MINUTES: int = 90   # Maximum delivery time
    
    # Bundle Cache
    BUNDLE_CACHE_TTL_SECONDS: int = 600  # 10 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = True


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
