"""API REST en lecture seule des données de l'observatoire (complète djangocms-rest)."""

from rest_framework import routers, serializers, viewsets

from .models import Advisory, Release, Technology


class TechnologySerializer(serializers.ModelSerializer):
    latest_version = serializers.SerializerMethodField()

    class Meta:
        model = Technology
        fields = ["slug", "name", "website", "registry", "package", "latest_version", "last_collected_at"]

    def get_latest_version(self, obj):
        release = obj.latest_release()
        return release.version if release else None


class ReleaseSerializer(serializers.ModelSerializer):
    technology = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Release
        fields = ["technology", "version", "published_at", "url", "is_security"]


class AdvisorySerializer(serializers.ModelSerializer):
    technology = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Advisory
        fields = [
            "technology", "identifier", "aliases", "title", "severity",
            "published_at", "fixed_versions", "url", "summary",
        ]


class TechnologyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Technology.objects.filter(is_tracked=True)
    serializer_class = TechnologySerializer
    lookup_field = "slug"


class ReleaseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReleaseSerializer

    def get_queryset(self):
        queryset = Release.objects.filter(is_prerelease=False).select_related("technology")
        if technology := self.request.query_params.get("technology"):
            queryset = queryset.filter(technology__slug=technology)
        return queryset


class AdvisoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AdvisorySerializer

    def get_queryset(self):
        queryset = Advisory.objects.select_related("technology")
        if technology := self.request.query_params.get("technology"):
            queryset = queryset.filter(technology__slug=technology)
        return queryset


router = routers.DefaultRouter()
router.register("technologies", TechnologyViewSet, basename="watch-technology")
router.register("releases", ReleaseViewSet, basename="watch-release")
router.register("advisories", AdvisoryViewSet, basename="watch-advisory")
urlpatterns = router.urls
