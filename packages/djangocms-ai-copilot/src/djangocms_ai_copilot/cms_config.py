from django.core.exceptions import ImproperlyConfigured

from cms.app_base import CMSAppConfig, CMSAppExtension
from cms.models import PageContent


class CopilotCMSExtension(CMSAppExtension):
    """Lets any django CMS app declare the "summary" fields the copilot may write.

    In the app's cms_config.py::

        class MyCMSConfig(CMSAppConfig):
            djangocms_ai_copilot_enabled = True
            copilot_summary_fields = {MyContent: "teaser"}
    """

    def __init__(self):
        self.summary_fields = {}

    def configure_app(self, cms_config):
        fields = getattr(cms_config, "copilot_summary_fields", None)
        if not isinstance(fields, dict):
            raise ImproperlyConfigured("copilot_summary_fields must be a dict {model: field_name}")
        for model, field_name in fields.items():
            model._meta.get_field(field_name)  # fails early on a typo
            self.summary_fields[model] = field_name


class CopilotCMSConfig(CMSAppConfig):
    # The package uses its own extension for the core page model.
    djangocms_ai_copilot_enabled = True
    copilot_summary_fields = {PageContent: "meta_description"}
