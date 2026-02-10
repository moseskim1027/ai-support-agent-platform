"""
Application configuration management with validation
Loads and validates environment variables for production-ready deployment
"""

import logging
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings with environment variable validation

    All settings are loaded from environment variables with defaults.
    Required variables will raise an error if not set.
    """

    # Application
    environment: str = Field(
        default="development", description="Environment: development, staging, production, test"
    )
    log_level: str = Field(default="info", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")

    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT and encryption",
    )
    cors_origins: str = Field(default="*", description="Comma-separated CORS origins")

    # API Keys (Required)
    openai_api_key: str = Field(..., description="OpenAI API key (required)")

    # Database
    postgres_url: str = Field(
        default="postgresql://postgres:postgres@postgres:5432/ai_support",
        description="PostgreSQL connection URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", description="Redis connection URL")

    # Vector Database
    qdrant_url: str = Field(default="http://qdrant:6333", description="Qdrant vector database URL")

    # Agent Configuration
    max_tokens: int = Field(default=2000, description="Max tokens for LLM responses")
    agent_temperature: float = Field(default=0.7, description="LLM temperature")
    rag_top_k: int = Field(default=5, description="Number of RAG results to retrieve")
    embedding_model: str = Field(
        default="text-embedding-ada-002", description="OpenAI embedding model"
    )

    # Observability
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    datadog_api_key: Optional[str] = Field(default=None, description="Datadog API key")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values"""
        allowed = ["development", "staging", "production", "test"]
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got {v}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid"""
        allowed = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got {v}")
        return v.lower()

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Warn if using default secret key in production"""
        environment = info.data.get("environment", "development")
        if environment == "production" and v == "dev-secret-key-change-in-production":
            raise ValueError(
                "SECRET_KEY must be changed in production! " "Generate with: openssl rand -hex 32"
            )
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, v: str) -> str:
        """Validate OpenAI API key format"""
        if not v or v == "your_openai_api_key_here" or v == "sk-your-openai-api-key-here":
            raise ValueError(
                "OPENAI_API_KEY is required! "
                "Get your API key from https://platform.openai.com/api-keys"
            )
        if not v.startswith("sk-"):
            logger.warning("OPENAI_API_KEY should start with 'sk-'")
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        """Check if running in test mode"""
        return self.environment == "test"

    def log_config(self):
        """Log configuration (hiding sensitive values)"""
        logger.info("=" * 50)
        logger.info("Application Configuration")
        logger.info("=" * 50)
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Log Level: {self.log_level}")
        logger.info(f"Debug Mode: {self.debug}")
        logger.info(f"API: {self.api_host}:{self.api_port}")
        logger.info(f"OpenAI API Key: {'*' * 10}{self.openai_api_key[-4:]}")
        logger.info(f"Postgres: {self._mask_url(self.postgres_url)}")
        logger.info(f"Redis: {self._mask_url(self.redis_url)}")
        logger.info(f"Qdrant: {self.qdrant_url}")
        logger.info(f"CORS Origins: {self.cors_origins_list}")
        logger.info("=" * 50)

    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask password in database URLs"""
        if "@" in url and "://" in url:
            protocol, rest = url.split("://", 1)
            if "@" in rest:
                auth, host = rest.split("@", 1)
                if ":" in auth:
                    user, _ = auth.split(":", 1)
                    return f"{protocol}://{user}:****@{host}"
        return url


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    logger.error("Please check your .env file and environment variables")
    raise


# Configure logging based on settings
def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Reduce noise from verbose libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)


# Setup logging on import
setup_logging()
