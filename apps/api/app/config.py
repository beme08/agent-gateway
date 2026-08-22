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

    # OpenAI-compatible LLM provider (FreeLLMAPI / OpenRouter / any
    # /v1/chat/completions endpoint). When LLM_BASE_URL + LLM_API_KEY are set,
    # the orchestrator routes tool calls through here instead of Cohere.
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    # LLM_API_KEY falls back to OPENROUTER_API_KEY so the generic client
    # arms automatically with the key already configured for ox-alpha.
    llm_api_key: str = os.getenv("LLM_API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "")
    # "auto" = the upstream router picks the best free model (FreeLLMAPI).
    llm_model: str = os.getenv("LLM_MODEL", "auto")
    oai_timeout_s: int = int(os.getenv("OAI_TIMEOUT_S", "120"))

    # Explicit provider selection: "oxalpha" | "openai_compat" | "cohere" | "".
    # Empty = legacy auto-detect (openai_compat when configured, else Cohere).
    # The orchestrator builds a failover chain from this hint, so an expired
    # ox-alpha trial degrades to the next configured provider instead of failing.
    llm_provider: str = os.getenv("LLM_PROVIDER", "")

    # Ox-alpha via OpenRouter (OpenAI-compatible protocol).
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    oxalpha_model: str = os.getenv("OXALPHA_MODEL", "stealth/ox-alpha")

    enable_public_upload: bool = os.getenv("ENABLE_PUBLIC_UPLOAD", "false").lower() in ("1", "true", "yes")
    log_level: str = os.getenv("LOG_LEVEL", "info")

    docs_dir: str = os.getenv("SEED_DOCS_DIR", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
