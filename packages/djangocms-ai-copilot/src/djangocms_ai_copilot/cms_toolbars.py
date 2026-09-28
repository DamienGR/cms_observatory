from urllib.parse import urlencode

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from cms.models import PageContent
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.urlutils import admin_reverse

from .permissions import can_use_copilot
from .views import get_summary_fields


@toolbar_pool.register
class CopilotToolbar(CMSToolbar):
    def populate(self):
        if not self.toolbar.edit_mode_active or not can_use_copilot(self.request.user):
            return
        obj = self.toolbar.get_object()
        field_name = get_summary_fields().get(type(obj))
        if field_name is None:
            return
        menu = self.toolbar.get_or_create_menu("djangocms-ai-copilot", _("Copilot"))
        menu.add_ajax_item(
            _("Write “%(field)s”") % {"field": obj._meta.get_field(field_name).verbose_name},
            action=admin_reverse("copilot_summary_field"),
            data={"content_type": ContentType.objects.get_for_model(obj).pk, "object_id": obj.pk},
            on_success=self.toolbar.REFRESH_PAGE,
        )
        if isinstance(obj, PageContent):
            menu.add_modal_item(
                _("Translate this page…"),
                url=admin_reverse("copilot_translate") + "?" + urlencode({"content": obj.pk}),
            )
        menu.add_break("copilot-log")
        menu.add_sideframe_item(_("Copilot log"), url=admin_reverse("djangocms_ai_copilot_copilotlog_changelist"))
