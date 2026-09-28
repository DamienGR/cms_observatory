from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone

from .models import Advisory, Release, Technology
from .sources import RELEASE_FETCHERS, fetch_osv_advisories, http_client


@dataclass
class CollectReport:
    technology: str
    releases: int = 0
    advisories: int = 0
    new_advisory_ids: list = field(default_factory=list)

    def as_dict(self):
        return self.__dict__


def collect_technology(technology: Technology) -> CollectReport:
    """Récupère releases et avis, puis les enregistre en deux requêtes groupées (upsert)."""
    with http_client() as client:
        releases = RELEASE_FETCHERS[technology.registry](technology.package, client)
        advisories = fetch_osv_advisories(technology.osv_ecosystem, technology.package, client)

    fixed_versions = {version for advisory in advisories for version in advisory.fixed_versions}
    known = set(technology.advisories.values_list("identifier", flat=True))

    with transaction.atomic():
        Release.objects.bulk_create(
            [
                Release(
                    technology=technology,
                    version=r.version,
                    published_at=r.published_at,
                    url=r.url,
                    is_prerelease=r.is_prerelease,
                    is_security=r.version in fixed_versions,
                )
                for r in releases
            ],
            update_conflicts=True,
            unique_fields=["technology", "version"],
            update_fields=["published_at", "url", "is_prerelease", "is_security"],
        )
        Advisory.objects.bulk_create(
            [
                Advisory(
                    technology=technology,
                    identifier=a.identifier,
                    aliases=a.aliases,
                    title=a.title,
                    details=a.details,
                    severity=a.severity,
                    published_at=a.published_at,
                    fixed_versions=a.fixed_versions,
                    url=a.url,
                )
                for a in advisories
            ],
            update_conflicts=True,
            unique_fields=["technology", "identifier"],
            update_fields=["aliases", "title", "details", "severity", "fixed_versions", "url"],
        )
        technology.last_collected_at = timezone.now()
        technology.save(update_fields=["last_collected_at"])

    new_ids = list(
        technology.advisories.exclude(identifier__in=known).values_list("pk", flat=True)
    )
    return CollectReport(
        technology=technology.slug,
        releases=len(releases),
        advisories=len(advisories),
        new_advisory_ids=new_ids,
    )
