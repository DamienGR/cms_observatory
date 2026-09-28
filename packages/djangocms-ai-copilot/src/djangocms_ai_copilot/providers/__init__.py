from functools import lru_cache

from django.utils.module_loading import import_string

from ..conf import get_setting
from .base import Completion, LLMProvider, ProviderError

__all__ = ["Completion", "LLMProvider", "ProviderError", "get_provider", "reset_provider"]


@lru_cache(maxsize=1)
def get_provider() -> LLMProvider:
    provider_class = import_string(get_setting("PROVIDER"))
    return provider_class(
        model=get_setting("MODEL"),
        api_key=get_setting("API_KEY"),
        max_tokens=get_setting("MAX_TOKENS"),
        timeout=get_setting("TIMEOUT"),
    )


def reset_provider(*, setting=None, **kwargs):
    if setting in (None, "DJANGOCMS_AI_COPILOT"):
        get_provider.cache_clear()
