"""Environment-var settings. Config (non-secret, tunable) lives in TOML
under config/ instead — see rubric.py and ingest/ted_client.py for how
those files get loaded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"

# Must match the vector(...) column width in migrations/0001_init.sql.
EMBEDDING_DIM = 256


@dataclass(frozen=True)
class Settings:
    database_url: str
    anthropic_api_key: str
    anthropic_model: str
    ted_api_base_url: str
    digest_output_dir: Path
    log_level: str


def load_settings() -> Settings:
    return Settings(
        database_url=_require("DATABASE_URL"),
        # Not required here: only scoring/classifier.py needs it, and it
        # should raise there if missing so `ingest-ted` works without an
        # Anthropic key configured.
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
        ted_api_base_url=os.environ.get("TED_API_BASE_URL", "https://api.ted.europa.eu/v3"),
        digest_output_dir=Path(os.environ.get("DIGEST_OUTPUT_DIR", "./data/digests")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
