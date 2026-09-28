from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import gettext_lazy as _

from .cms_menus import TechnologyMenu


@apphook_pool.register
class WatchApphook(CMSApp):
    name = _("Observatoire")
    app_name = "watch"

    def get_urls(self, page=None, language=None, **kwargs):
        return ["watch.urls"]

    def get_menus(self, page=None, language=None, **kwargs):
        return [TechnologyMenu]
