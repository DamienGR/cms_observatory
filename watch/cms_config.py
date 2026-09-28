from cms.app_base import CMSAppConfig
from cms.utils.i18n import get_language_tuple
from djangocms_versioning.datastructures import VersionableItem

from .cms_wizards import technology_wizard
from .models import TechnologyContent
from .views import render_technology_content


class WatchCMSConfig(CMSAppConfig):
    cms_enabled = True
    # Rend le modèle éditable dans le frontend : endpoints d'aperçu et d'édition, toolbar.
    cms_toolbar_enabled_models = [(TechnologyContent, render_technology_content, "technology")]
    cms_wizards = [technology_wizard]

    djangocms_versioning_enabled = True
    versioning = [
        VersionableItem(
            content_model=TechnologyContent,
            grouper_field_name="technology",
            extra_grouping_fields=["language"],
            version_list_filter_lookups={"language": get_language_tuple},
            grouper_selector_option_label=lambda obj, language: obj.name,
            grouper_admin_mixin="__default__",
        )
    ]

    djangocms_moderation_enabled = True
    moderated_models = [TechnologyContent]

    # Extension fournie par notre package : le copilote peut rédiger l'accroche.
    djangocms_ai_copilot_enabled = True
    copilot_summary_fields = {TechnologyContent: "tagline"}
