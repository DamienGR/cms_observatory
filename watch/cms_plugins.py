from datetime import timedelta

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Comparison, ComparisonItem, LatestReleasesPluginModel, Release


@plugin_pool.register_plugin
class LatestReleasesPlugin(CMSPluginBase):
    model = LatestReleasesPluginModel
    name = _("Dernières releases")
    module = _("Observatoire")
    render_template = "watch/plugins/latest_releases.html"

    def render(self, context, instance, placeholder):
        context = super().render(context, instance, placeholder)
        releases = Release.objects.filter(is_prerelease=False).select_related("technology")
        if instance.technology_id:
            releases = releases.filter(technology_id=instance.technology_id)
        if instance.only_security:
            releases = releases.filter(is_security=True)
        context["releases"] = releases[: instance.limit]
        return context

    def get_cache_expiration(self, request, instance, placeholder):
        return 15 * 60  # secondes : le cache de page ne gardera pas ce plugin plus de 15 min


@plugin_pool.register_plugin
class ComparisonPlugin(CMSPluginBase):
    model = Comparison
    name = _("Comparatif")
    module = _("Observatoire")
    render_template = "watch/plugins/comparison.html"
    allow_children = True
    child_classes = "auto"  # 5.1 : n'accepte que les plugins qui le désignent comme parent


@plugin_pool.register_plugin
class ComparisonItemPlugin(CMSPluginBase):
    model = ComparisonItem
    name = _("Colonne de comparatif")
    module = _("Observatoire")
    render_template = "watch/plugins/comparison_item.html"
    require_parent = True
    parent_classes = ["ComparisonPlugin"]


@plugin_pool.register_plugin
class TechnologyFactsPlugin(CMSPluginBase):
    name = _("Chiffres clés")
    module = _("Observatoire")
    render_template = "watch/plugins/technology_facts.html"
    show_add_form = False
    # 5.1 : ce plugin n'est proposé que dans les placeholders des fiches technologie.
    allowed_models = ["watch.technologycontent"]

    def render(self, context, instance, placeholder):
        technology = instance.placeholder.source.technology
        since = timezone.now() - timedelta(days=365)
        context.update(
            {
                "instance": instance,
                "technology": technology,
                "latest": technology.latest_release(),
                "advisories_last_year": technology.advisories.filter(published_at__gte=since).count(),
            }
        )
        return context

    def get_cache_expiration(self, request, instance, placeholder):
        return 15 * 60
