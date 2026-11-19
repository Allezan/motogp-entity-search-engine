from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from psycopg.conninfo import make_conninfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field

BASE_DIR = Path(__file__).resolve().parents[2]  # backend/

class Settings(BaseSettings):
    """All configuration comes from environment variables / backend/.env."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "MotoGP Entity-Aware Search Engine"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"
    admin_api_key: Optional[str] = None

    # --- Neon PostgreSQL (either DATABASE_URL, or the individual DB_* parameters) ---
    # --- Neon PostgreSQL ---
    database_url: Optional[str] = None

    db_host: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("DB_HOST", "PGHOST")
    )

    db_port: int = Field(
        default=5432,
        validation_alias=AliasChoices("DB_PORT", "PGPORT")
    )

    db_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("DB_NAME", "PGDATABASE")
    )

    db_user: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("DB_USER", "PGUSER")
    )

    db_password: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("DB_PASSWORD", "PGPASSWORD")
    )

    db_sslmode: str = Field(
        default="require",
        validation_alias=AliasChoices("DB_SSLMODE", "PGSSLMODE")
    )

    db_connect_timeout: int = 15
    db_pool_min_size: int = 1
    db_pool_max_size: int = 5

    # --- Retrieval ---
    artifacts_dir: Path = BASE_DIR / "artifacts"
    artifact_filename: str = "index.joblib"
    default_alpha: float = 0.7
    default_beta: float = 0.3
    entity_title_boost: float = 3.0
    snippet_length: int = 250
    # Use documents.processed_text from the DB instead of re-running the Sastrawi pipeline.
    # Only enable if it was produced by the same preprocessing as queries (see README).
    use_stored_processed_text: bool = False
    # Comma-separated entities.verification_status values to use (empty = all entities).
    entity_statuses: Optional[str] = None
    # Overwrite document_entities with the table computed by the indexer.
    persist_document_entities: bool = False

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def entity_status_list(self) -> List[str]:
        return [s.strip() for s in (self.entity_statuses or "").split(",") if s.strip()]

    @property
    def artifact_path(self) -> Path:
        return Path(self.artifacts_dir) / self.artifact_filename

    @property
    def conninfo(self) -> str:
        # Build the libpq connection string from parameters
        if self.database_url:
            return make_conninfo(self.database_url, connect_timeout=self.db_connect_timeout)
        missing = [
            name
            for name, value in (
                ("DB_HOST", self.db_host),
                ("DB_NAME", self.db_name),
                ("DB_USER", self.db_user),
                ("DB_PASSWORD", self.db_password),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Database is not configured. Set DATABASE_URL or all of: " + ", ".join(missing)
            )
        return make_conninfo(
            host=self.db_host,
            port=self.db_port,
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            sslmode=self.db_sslmode,
            connect_timeout=self.db_connect_timeout,
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()
