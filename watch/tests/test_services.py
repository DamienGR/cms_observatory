import respx

from watch.models import Advisory, Release
from watch.services import collect_technology

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
