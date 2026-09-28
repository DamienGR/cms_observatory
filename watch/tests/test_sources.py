import httpx
import pytest
import respx

from watch.sources import (
    fetch_github_releases,
    fetch_osv_advisories,
    fetch_packagist_releases,
    fetch_pypi_releases,
)


@respx.mock
def test_pypi_skips_yanked_and_flags_prereleases():
    respx.get("https://pypi.org/pypi/django-cms/json").respond(json={"releases": {
        "5.1.3": [{"upload_time_iso_8601": "2026-09-24T14:37:20Z", "yanked": False}],
        "5.2.0rc1": [{"upload_time_iso_8601": "2026-09-01T10:00:00Z", "yanked": False}],
        "5.0.0": [{"upload_time_iso_8601": "2025-05-01T10:00:00Z", "yanked": True}],
    }})
    with httpx.Client() as client:
        releases = {r.version: r for r in fetch_pypi_releases("django-cms", client)}
    assert set(releases) == {"5.1.3", "5.2.0rc1"}
    assert releases["5.2.0rc1"].is_prerelease and not releases["5.1.3"].is_prerelease


@respx.mock
def test_packagist_minified_format():
    respx.get("https://repo.packagist.org/p2/drupal/core.json").respond(json={
        "minified": "composer/2.0",
        "packages": {"drupal/core": [
            {"name": "drupal/core", "version": "11.2.4", "time": "2025-09-03T15:22:17+00:00", "require": {}},
            {"version": "11.2.3", "time": "2025-08-06T10:00:00+00:00"},
            {"version": "11.3.0-beta1", "time": "2025-10-01T10:00:00+00:00"},
        ]},
    })
    with httpx.Client() as client:
        releases = fetch_packagist_releases("drupal/core", client)
    assert [r.version for r in releases] == ["11.2.4", "11.2.3", "11.3.0-beta1"]
    assert releases[2].is_prerelease


@respx.mock
def test_osv_pagination_and_fixed_versions():
    route = respx.post("https://api.osv.dev/v1/query")
    route.side_effect = [
        httpx.Response(200, json={"vulns": [{
            "id": "GHSA-aaaa", "summary": "XSS in admin", "published": "2026-07-10T00:00:00Z",
            "modified": "2026-07-11T00:00:00Z", "aliases": ["CVE-2026-1"],
            "database_specific": {"severity": "MODERATE"},
            "affected": [
                {"package": {"name": "django-cms", "ecosystem": "PyPI"},
                 "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": "5.0.9"}]}]},
                {"package": {"name": "other-package", "ecosystem": "PyPI"},
                 "ranges": [{"type": "ECOSYSTEM", "events": [{"fixed": "9.9.9"}]}]},
            ],
            "references": [{"type": "ADVISORY", "url": "https://github.com/advisories/GHSA-aaaa"}],
        }], "next_page_token": "p2"}),
        httpx.Response(200, json={"vulns": [{"id": "PYSEC-2", "modified": "2026-01-01T00:00:00Z"}]}),
    ]
    with httpx.Client() as client:
        advisories = fetch_osv_advisories("PyPI", "django-cms", client)
    assert [a.identifier for a in advisories] == ["GHSA-aaaa", "PYSEC-2"]
    first = advisories[0]
    assert first.fixed_versions == ["5.0.9"]  # l'autre paquet est ignoré
    assert first.severity == "moderate"
    assert first.url == "https://github.com/advisories/GHSA-aaaa"
    assert b'"page_token"' in route.calls[1].request.content


@respx.mock
def test_github_follows_pages_and_skips_drafts():
    first = "https://api.github.com/repos/joomla/joomla-cms/releases?per_page=100"
    second = "https://api.github.com/repos/joomla/joomla-cms/releases?per_page=100&page=2"
    respx.get(first).respond(
        headers={"Link": f'<{second}>; rel="next"'},
        json=[
            {"tag_name": "6.1.3", "published_at": "2026-09-02T16:00:00Z", "prerelease": False,
             "draft": False, "html_url": "https://github.com/joomla/joomla-cms/releases/tag/6.1.3"},
            {"tag_name": "6.2.0-beta3", "published_at": "2026-09-15T16:00:00Z", "prerelease": True,
             "draft": False, "html_url": "https://github.com/joomla/joomla-cms/releases/tag/6.2.0-beta3"},
            {"tag_name": "6.2.0", "published_at": None, "prerelease": False, "draft": True, "html_url": ""},
        ],
    )
    respx.get(second).respond(json=[
        {"tag_name": "v5.4.8", "published_at": "2026-09-02T15:00:00Z", "prerelease": False,
         "draft": False, "html_url": "https://github.com/joomla/joomla-cms/releases/tag/v5.4.8"},
    ])
    with httpx.Client() as client:
        releases = fetch_github_releases("joomla/joomla-cms", client)
    assert [r.version for r in releases] == ["6.1.3", "6.2.0-beta3", "5.4.8"]
    assert [r.is_prerelease for r in releases] == [False, True, False]
