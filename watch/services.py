from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone

from .models import Advisory, Release, Technology
from .sources import RELEASE_FETCHERS, AdvisoryData, fetch_advisories, http_client


def cve_ids(identifier, aliases):
    return {name for name in (identifier, *aliases) if name.startswith("CVE-")}


def deduplicate(advisories: list[AdvisoryData], existing) -> list[AdvisoryData]:
    """Un même CVE peut venir de plusieurs sources : chaque CVE reste à l'avis déjà
    enregistré qui le cite, sinon au premier avis collecté (ordre des sources)."""
    owners = {}
    for identifier, aliases in existing:
        for cve in cve_ids(identifier, aliases):
            owners.setdefault(cve, identifier)
    kept, seen = [], set()
    for advisory in advisories:
        cves = cve_ids(advisory.identifier, advisory.aliases)
        taken = any(owners.get(cve, advisory.identifier) != advisory.identifier for cve in cves)
        if taken or advisory.identifier in seen:
            continue
        for cve in cves:
            owners[cve] = advisory.identifier
        seen.add(advisory.identifier)
        kept.append(advisory)
    return kept


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
    known = set(technology.advisories.values_list("identifier", flat=True))
    with http_client() as client:
        releases = RELEASE_FETCHERS[technology.registry](technology.package, client)
        collected = [
            advisory
            for source in technology.get_advisory_sources()
            for advisory in fetch_advisories(source, client, known)
        ]
    advisories = deduplicate(collected, technology.advisories.values_list("identifier", "aliases"))

    fixed_versions = {version for advisory in advisories for version in advisory.fixed_versions}

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
