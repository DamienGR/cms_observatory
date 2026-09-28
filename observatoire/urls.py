from cms.sitemaps import CMSSitemap
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog

from watch.sitemaps import TechnologySitemap

admin.site.site_header = _("Observatoire des CMS")
admin.site.site_title = _("Observatoire des CMS")
admin.site.index_title = _("Administration")
sitemaps = {"pages": CMSSitemap, "technologies": TechnologySitemap}

# commencerait par « api » ne doit jamais masquer l'API.
urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]
urlpatterns += i18n_patterns(
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("admin/", admin.site.urls),
    path("filer/", include("filer.urls")),
    path("", include("cms.urls")),
)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
