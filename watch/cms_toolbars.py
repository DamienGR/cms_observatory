from cms.extensions.toolbar import ExtensionToolbar
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.urlutils import admin_reverse
from django.utils.translation import gettext_lazy as _

from .models import PageTechnologyExtension


@toolbar_pool.register
class WatchToolbar(CMSToolbar):
    def populate(self):
        user = self.request.user
        if not user.has_perm("watch.view_release"):
            return
        menu = self.toolbar.get_or_create_menu("watch-menu", _("Observatoire"))
        menu.add_sideframe_item(_("Technologies"), url=admin_reverse("watch_technology_changelist"))
        menu.add_sideframe_item(_("Releases"), url=admin_reverse("watch_release_changelist"))
        menu.add_sideframe_item(_("Avis de sécurité"), url=admin_reverse("watch_advisory_changelist"))
        if user.has_perm("watch.change_technology"):
            menu.add_break("watch-actions")
            menu.add_ajax_item(
                _("Lancer la collecte"),
                action=admin_reverse("watch_technology_collect"),
                question=_("Collecter maintenant les releases et les avis de sécurité ?"),
                on_success=self.toolbar.REFRESH_PAGE,
            )


@toolbar_pool.register
class PageTechnologyToolbar(ExtensionToolbar):
    model = PageTechnologyExtension

    def populate(self):
        current_page_menu = self._setup_extension_toolbar()
        if current_page_menu:
            _extension, url = self.get_page_extension_admin()
            if url:
                current_page_menu.add_modal_item(
                    _("Technologie de la page"),
                    url=url,
                    disabled=not self.toolbar.edit_mode_active,
                    position=0,
                )
