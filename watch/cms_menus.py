from datetime import timedelta

from cms.menu_bases import CMSAttachMenu
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from menus.base import Modifier, NavigationNode
from menus.menu_pool import menu_pool

from .models import Advisory, TechnologyContent


class TechnologyMenu(CMSAttachMenu):
    """Une entrée de menu par fiche technologie publiée dans la langue courante."""

    name = _("Technologies suivies")

    def get_nodes(self, request):
        # Avec djangocms-versioning, le manager par défaut ne renvoie que le contenu publié.
        contents = TechnologyContent.objects.filter(language=get_language()).select_related("technology")
        nodes = []
        for content in contents.order_by("technology__name"):
            url = content.get_absolute_url()
            if url:
                nodes.append(
                    NavigationNode(
                        title=content.technology.name,
                        url=url,
                        id=content.technology_id,
                        attr={"technology_id": content.technology_id},
                    )
                )
        return nodes


class SecurityBadgeModifier(Modifier):
    """Ajoute aux nœuds le nombre d'avis de sécurité des 30 derniers jours (non mis en cache)."""

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if post_cut or breadcrumb:
            return nodes
        since = timezone.now() - timedelta(days=30)
        counts = dict(
            Advisory.objects.filter(published_at__gte=since)
            .values("technology")
            .annotate(total=Count("id"))
            .values_list("technology", "total")
        )
        for node in nodes:
            technology_id = node.attr.get("technology_id")
            if technology_id:
                node.attr["recent_advisories"] = counts.get(technology_id, 0)
        return nodes


menu_pool.register_menu(TechnologyMenu)
menu_pool.register_modifier(SecurityBadgeModifier)
