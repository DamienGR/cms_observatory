import respx
from django.utils import timezone

from watch.models import Advisory, Release
from watch.services import collect_technology, deduplicate
from watch.sources import AdvisoryData

PYPI = {"releases": {
    "5.0.9": [{"upload_time_iso_8601": "2026-07-10T10:00:00Z"}],
    "5.1.0": [{"upload_time_iso_8601": "2026-07-10T11:00:00Z"}],
}}
OSV = {"vulns": [{
    "id": "GHSA-aaaa", "summary": "XSS", "published": "2026-07-10T00:00:00Z", "modified": "2026-07-10T00:00:00Z",
    "affected": [{"package": {"name": "django-cms"}, "ranges": [{"events": [{"fixed": "5.0.9"}]}]}],
}]}


@respx.mock
def test_collect_is_idempotent_and_flags_security_releases(technology):
    respx.get("https://pypi.org/pypi/django-cms/json").respond(json=PYPI)
    respx.post("https://api.osv.dev/v1/query").respond(json=OSV)

    report = collect_technology(technology)
    assert report.releases == 2 and len(report.new_advisory_ids) == 1
    assert Release.objects.get(version="5.0.9").is_security
    assert not Release.objects.get(version="5.1.0").is_security

    report = collect_technology(technology)  # deuxième passage : rien de nouveau
    assert report.new_advisory_ids == []
    assert Release.objects.count() == 2 and Advisory.objects.count() == 1
    technology.refresh_from_db()
    assert technology.last_collected_at is not None


def advisory(identifier, *aliases):
    return AdvisoryData(
        identifier=identifier, title=identifier, details="", severity="low",
        published_at=timezone.now(), aliases=list(aliases), fixed_versions=[], url="",
    )


def test_deduplicate_keeps_first_advisory_per_cve():
    collected = [
        advisory("GHSA-1", "CVE-2026-1"),
        advisory("GHSA-2"),
        advisory("BIT-1", "CVE-2026-1"),  # même CVE qu'une source prioritaire
        advisory("BIT-2", "CVE-2026-2"),  # CVE déjà enregistré sous un autre avis
        advisory("OLD-3", "CVE-2026-3"),  # avis déjà enregistré : mis à jour
        advisory("GHSA-2"),  # identifiant en double dans la collecte
    ]
    existing = [("OLD-2", ["CVE-2026-2"]), ("OLD-3", ["CVE-2026-3"])]
    kept = deduplicate(collected, existing)
    assert [a.identifier for a in kept] == ["GHSA-1", "GHSA-2", "OLD-3"]


@respx.mock
def test_collect_merges_configured_sources(technology):
    technology.advisory_sources = [
        {"source": "github", "repository": "WordPress/wordpress-develop"},
        {"source": "osv", "ecosystem": "Bitnami", "package": "wordpress"},
    ]
    technology.save()
    respx.get("https://pypi.org/pypi/django-cms/json").respond(json=PYPI)
    respx.get("https://api.github.com/repos/WordPress/wordpress-develop/security-advisories").respond(json=[{
        "ghsa_id": "GHSA-wp", "cve_id": "CVE-2026-9", "severity": "high", "summary": "SQLi",
        "published_at": "2026-07-10T00:00:00Z", "html_url": "https://github.com/advisories/GHSA-wp",
        "vulnerabilities": [{"patched_versions": "5.1.0"}],
    }])
    osv = respx.post("https://api.osv.dev/v1/query").respond(json={"vulns": [
        {"id": "BIT-wordpress-9", "aliases": ["CVE-2026-9"], "published": "2026-07-20T00:00:00Z",
         "modified": "2026-07-20T00:00:00Z"},
        {"id": "BIT-wordpress-8", "aliases": ["CVE-2026-8"], "published": "2026-01-20T00:00:00Z",
         "modified": "2026-01-20T00:00:00Z"},
    ]})

    collect_technology(technology)
    assert b'"ecosystem":"Bitnami"' in osv.calls[0].request.content
    assert set(Advisory.objects.values_list("identifier", flat=True)) == {"GHSA-wp", "BIT-wordpress-8"}
    assert Release.objects.get(version="5.1.0").is_security


def test_default_advisory_source_is_the_package_in_osv(technology):
    assert technology.get_advisory_sources() == [{"source": "osv", "ecosystem": "PyPI", "package": "django-cms"}]
