from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Advisory


class LatestAdvisoriesFeed(Feed):
    title = _("Observatoire des CMS — avis de sécurité")
    description = _("Les derniers avis de sécurité des CMS suivis, résumés.")

    def link(self):
        return reverse("watch:advisories")

    def items(self):
        return Advisory.objects.select_related("technology")[:30]

    def item_title(self, item):
        return f"[{item.technology.name}] {item.title}"

    def item_description(self, item):
        return item.summary or item.title

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.published_at
