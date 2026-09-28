from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WatchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "watch"
    verbose_name = _("Observatoire")
