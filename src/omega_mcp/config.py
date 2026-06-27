# filepath: src/omega_mcp/config.py
import os
from dataclasses import dataclass, field
from omega_mcp.logger import logger  # Clean root-level import now

@dataclass(frozen=True)
class GlobalSettings:
    """Core application level settings."""
    ENVIRONMENT: str = os.getenv("OMEGA_ENV", "dev")
    NETWORK_TIMEOUT: float = float(os.getenv("OMEGA_NETWORK_TIMEOUT", "15.0"))

@dataclass(frozen=True)
class WebSearchToolSettings:
    """Configuration grouped explicitly for the Web Search & Scraping tools."""
    MAX_RESULTS: int = int(os.getenv("OMEGA_SEARCH_MAX_RESULTS", "5"))

    def validate(self) -> bool:
        if self.MAX_RESULTS <= 0:
            logger.error("OMEGA_SEARCH_MAX_RESULTS must be a positive integer.")
            return False
        return True

@dataclass(frozen=True)
class DatabaseToolSettings:
    """Configuration grouped explicitly for your Neo4j and ChromaDB network services."""
    # Neo4j Parameters
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "your_secure_password")
    
    # ChromaDB Network Client Parameters
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION","nexus_knowledge_pool")

    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:11434")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

    def validate(self) -> bool:
        if not self.NEO4J_URI or not self.NEO4J_PASSWORD:
            logger.warning("⚠️ Database credentials missing or unassigned in environment definitions.")
        return True

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
            self.web.validate(),
            self.db.validate()
        ])

# Create a singleton instance to import across modules
settings = Settings()
settings.validate_all()