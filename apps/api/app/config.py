"""Settings loaded from environment variables. No external dependency
on pydantic_settings; we use plain pydantic BaseSettings alternative."""
from __future__ import annotations

import os
from functools import lru_cache
from pydantic import BaseModel


class Settings(BaseModel):
    supabase_url: str = os.getenv("SUPABASE_URL", "http://localhost")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "anon")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "service")
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "secret")

    agent_api_key: str = os.getenv("AGENT_API_KEY", "local-dev-shared-secret")
    cohere_api_key: str = os.getenv("COHERE_API_KEY", "")
    cohere_model: str = os.getenv("COHERE_MODEL", "command-r-plus")
    cohere_embed_model: str = os.getenv("COHERE_EMBED_MODEL", "embed-english-v3.0")

    enable_public_upload: bool = os.getenv("ENABLE_PUBLIC_UPLOAD", "false").lower() in ("1", "true", "yes")
    log_level: str = os.getenv("LOG_LEVEL", "info")

    docs_dir: str = os.getenv("SEED_DOCS_DIR", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
