from functools import lru_cache
from typing import Optional

from .config import Settings, get_settings
from .openai_client import OpenAIClient
from .openrouter_client import OpenRouterClient


@lru_cache
def get_app_settings() -> Settings:
    return get_settings()


@lru_cache
def get_openai_client() -> OpenAIClient:
    settings = get_app_settings()
    return OpenAIClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        chat_model=settings.openai_chat_model,
        embedding_model=settings.openai_embedding_model,
    )


def get_openrouter_client(model: Optional[str] = None) -> OpenRouterClient:
    """Get an OpenRouter client for multi-model evaluation."""
    settings = get_app_settings()
    return OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        default_model=model or "openai/gpt-4o",
    )



