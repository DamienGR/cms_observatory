from urllib.parse import urlencode

from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _

from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool
from cms.utils.urlutils import admin_reverse

from . import views
from .conf import get_setting
from .permissions import can_use_copilot


@plugin_pool.register_plugin
class CopilotPlugin(CMSPluginBase):
    """Invisible "system" plugin: it only provides admin URLs and context-menu entries.

    Same pattern as djangocms-transfer: nothing to add to the project's urls.py.
    """

    name = _("AI copilot")
    system = True
    render_plugin = False

    def get_plugin_urls(self):
        # Plugin URLs are mounted in the admin but not wrapped: admin_view() adds
        # the login redirect, CSRF protection and never_cache.
        admin_view = admin.site.admin_view
        return [
            path("summary/", admin_view(views.summary_field_view), name="copilot_summary_field"),
            path("rewrite/", admin_view(views.rewrite_view), name="copilot_rewrite"),
            path("translate/", admin_view(views.translate_view), name="copilot_translate"),
        ]

    @classmethod
    def get_extra_plugin_menu_items(cls, request, plugin):
        if plugin.plugin_type not in get_setting("TEXT_PLUGINS") or not can_use_copilot(request.user):
            return None
        return [
            PluginMenuItem(
                _("Rewrite with AI…"),
                admin_reverse("copilot_rewrite") + "?" + urlencode({"plugin": plugin.pk}),
                data={},
                action="modal",
            )
        ]
