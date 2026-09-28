from cms.admin.utils import GrouperModelAdmin
from cms.extensions import PageExtensionAdmin
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .models import Advisory, PageTechnologyExtension, Release, Technology, TechnologyContent
from .tasks import collect_technology_task


@admin.register(Technology)
class TechnologyAdmin(GrouperModelAdmin):
    content_model = TechnologyContent
    extra_grouping_fields = ("language",)
    list_display = ("name", "content__tagline", "registry", "package", "last_collected_at", "admin_list_actions")
    list_display_links = None
    fields = (
        "name", "slug", "registry", "package", "website", "is_tracked",
        "content__tagline", "content__verdict", "content__language",
    )
    prepopulated_fields = {"slug": ("name",)}
    actions = ["collect_selected"]

    def get_urls(self):
        return [
            path("collect/", self.admin_site.admin_view(self.collect_view), name="watch_technology_collect"),
            *super().get_urls(),
        ]

    @admin.action(description=_("Collecter les technologies sélectionnées"))
    def collect_selected(self, request, queryset):
        for technology in queryset:
            collect_technology_task.enqueue(technology.pk)
        self.message_user(request, _("%d collecte(s) mise(s) en file.") % queryset.count(), messages.SUCCESS)

    def collect_view(self, request):
        """Cible de l'item AJAX « Lancer la collecte » de la toolbar."""
        if not self.has_change_permission(request):
            raise PermissionDenied
        return require_POST(self._collect_all)(request)

    def _collect_all(self, request):
        ids = [
            collect_technology_task.enqueue(pk).id
            for pk in Technology.objects.filter(is_tracked=True).values_list("pk", flat=True)
        ]
        return JsonResponse({"enqueued": ids})


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ("technology", "version", "published_at", "is_security", "is_prerelease")
    list_filter = ("technology", "is_security", "is_prerelease")
    search_fields = ("version",)
    date_hierarchy = "published_at"
    list_select_related = ("technology",)


@admin.register(Advisory)
class AdvisoryAdmin(admin.ModelAdmin):
    list_display = ("identifier", "technology", "severity", "published_at", "has_summary")
    list_filter = ("technology", "severity")
    search_fields = ("identifier", "title", "aliases")
    date_hierarchy = "published_at"
    list_select_related = ("technology",)
    readonly_fields = ("aliases", "fixed_versions")

    @admin.display(boolean=True, description=_("résumé IA"))
    def has_summary(self, obj):
        return bool(obj.summary)


admin.site.register(PageTechnologyExtension, PageExtensionAdmin)
