from django.conf import settings

DEFAULTS = {
    "PROVIDER": "djangocms_ai_copilot.providers.anthropic.AnthropicProvider",
    "MODEL": "claude-sonnet-5",
    "API_KEY": None,  # None: the SDK reads ANTHROPIC_API_KEY
    "MAX_TOKENS": 1024,
    "TIMEOUT": 60,
    "TEXT_PLUGINS": ["TextPlugin"],
}


def get_setting(name):
    return getattr(settings, "DJANGOCMS_AI_COPILOT", {}).get(name, DEFAULTS[name])
