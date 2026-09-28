from django.contrib.sitemaps import Sitemap

from .models import TechnologyContent


class TechnologySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        # Manager par défaut = contenus publiés ; on écarte ceux dont l'apphook n'est pas en ligne.
        return [c for c in TechnologyContent.objects.select_related("technology") if c.get_absolute_url()]

    def location(self, item):
        return item.get_absolute_url()
