# src/omega_mcp/core/config.py
import os
from dataclasses import dataclass, field
from omega_mcp.core.logger import logger

@dataclass(frozen=True)
class GlobalSettings:
    """Core application level settings."""
    ENVIRONMENT: str = os.getenv("OMEGA_ENV", "dev")
    NETWORK_TIMEOUT: float = float(os.getenv("OMEGA_NETWORK_TIMEOUT", "15.0"))

@dataclass(frozen=True)
class WebSearchToolSettings:
    """Configuration grouped explicitly for the Web Search & Scraping tools."""
    MAX_RESULTS: int = int(os.getenv("OMEGA_SEARCH_MAX_RESULTS", "5"))
    # Add future key mappings here if you change providers
    # BRAVE_API_KEY: str | None = os.getenv("OMEGA_BRAVE_API_KEY")

    def validate(self) -> bool:
        if self.MAX_RESULTS <= 0:
            logger.error("OMEGA_SEARCH_MAX_RESULTS must be a positive integer.")
            return False
        return True

@dataclass(frozen=True)
class DatabaseToolSettings:
    """Configuration grouped explicitly for your future Database query tools."""
    DB_URI: str | None = os.getenv("OMEGA_DATABASE_URI")
    POOL_SIZE: int = int(os.getenv("OMEGA_DB_POOL_SIZE", "5"))

@dataclass(frozen=True)
class FileSystemToolSettings:
    """Configuration grouped explicitly for local filesystem operations."""
    ALLOWED_ROOT_DIR: str = os.getenv("OMEGA_ALLOWED_ROOT", "/")

# --- Master Settings Orchestrator ---

@dataclass(frozen=True)
class Settings:
    """The master settings registry holding tool-specific sub-configurations."""
    app: GlobalSettings = field(default_factory=GlobalSettings)
    web: WebSearchToolSettings = field(default_factory=WebSearchToolSettings)
    db: DatabaseToolSettings = field(default_factory=DatabaseToolSettings)
    fs: FileSystemToolSettings = field(default_factory=FileSystemToolSettings)

    def validate_all(self) -> bool:
        """Triggers component level validations at boot time."""
        return all([
            self.web.validate()
            # Add other tool validations here as you build them out
        ])

# Create a singleton instance to import across modules
settings = Settings()
settings.validate_all()