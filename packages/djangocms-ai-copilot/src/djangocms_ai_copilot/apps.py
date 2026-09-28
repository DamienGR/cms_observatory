from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CopilotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "djangocms_ai_copilot"
    verbose_name = _("AI copilot")

    def ready(self):
        from django.core.signals import setting_changed

        from .providers import reset_provider

        # Tests use override_settings(): make sure the cached provider follows.
        setting_changed.connect(reset_provider, dispatch_uid="djangocms_ai_copilot_reset_provider")
