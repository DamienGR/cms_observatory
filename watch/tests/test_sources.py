import httpx
import pytest
import respx

from watch.sources import (
    expand_minified,
    fetch_github_advisories,
    fetch_github_releases,
    fetch_joomla_advisories,
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
def test_packagist_minified_entries_inherit_unchanged_keys():
    """Une release publiée à la même date que la précédente n'a pas de clé « time »."""
    respx.get("https://repo.packagist.org/p2/roots/wordpress-no-content.json").respond(json={
        "minified": "composer/2.0",
        "packages": {"roots/wordpress-no-content": [
            {"name": "roots/wordpress-no-content", "version": "7.1.2", "time": "2026-09-22T18:00:00+00:00"},
            {"version": "7.0.6"},
            {"version": "7.0.5", "time": "2026-09-17T18:00:00+00:00", "extra": "__unset"},
        ]},
    })
    with httpx.Client() as client:
        releases = fetch_packagist_releases("roots/wordpress-no-content", client)
    assert [(r.version, r.published_at.day) for r in releases] == [("7.1.2", 22), ("7.0.6", 22), ("7.0.5", 17)]


def test_expand_minified_unsets_keys():
    entries = expand_minified([{"version": "1", "extra": {"a": 1}}, {"version": "2", "extra": "__unset"}])
    assert entries == [{"version": "1", "extra": {"a": 1}}, {"version": "2"}]


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


@respx.mock
def test_github_repository_advisories():
    respx.get(
        "https://api.github.com/repos/WordPress/wordpress-develop/security-advisories",
        params={"state": "published", "per_page": "100"},
    ).respond(json=[
        {
            "ghsa_id": "GHSA-7hp8-65ch-5whp", "cve_id": "CVE-2026-87902", "severity": "critical",
            "summary": "Unauthenticated path traversal", "description": "An unauthenticated attacker…",
            "published_at": "2026-09-22T18:00:00Z", "withdrawn_at": None,
            "html_url": "https://github.com/WordPress/wordpress-develop/security/advisories/GHSA-7hp8-65ch-5whp",
            "vulnerabilities": [
                {"package": {"ecosystem": "other", "name": "WordPress"}, "patched_versions": "7.1.2"},
                {"package": {"ecosystem": "other", "name": "WordPress"}, "patched_versions": "7.0.6, 6.9.10"},
            ],
        },
        {
            "ghsa_id": "GHSA-32m5-wc28-ghrr", "cve_id": None, "severity": "medium", "summary": "Comment reparenting",
            "description": "", "published_at": "2026-09-18T18:00:00Z", "withdrawn_at": None,
            "html_url": "https://github.com/WordPress/wordpress-develop/security/advisories/GHSA-32m5-wc28-ghrr",
            "vulnerabilities": [{"package": {"ecosystem": "other", "name": "WordPress"}, "patched_versions": None}],
        },
        {"ghsa_id": "GHSA-retiré", "withdrawn_at": "2026-01-01T00:00:00Z"},
    ])
    with httpx.Client() as client:
        advisories = fetch_github_advisories("WordPress/wordpress-develop", client)
    assert [a.identifier for a in advisories] == ["GHSA-7hp8-65ch-5whp", "GHSA-32m5-wc28-ghrr"]
    critical, medium = advisories
    assert critical.aliases == ["CVE-2026-87902"] and critical.severity == "critical"
    assert critical.fixed_versions == ["6.9.10", "7.0.6", "7.1.2"]
    assert medium.aliases == [] and medium.severity == "moderate" and medium.fixed_versions == []


JOOMLA_ITEM = """<item>
<title>{title}</title>
<link>https://developer.joomla.org/security-centre/{article}-{number}-core-issue.html</link>
<pubDate>Mon, 17 Aug 2026 14:00:10 +0000</pubDate>
<description><![CDATA[<ul>
<li><strong>Project:</strong> Joomla!</li>
<li><strong>Severity: </strong>{severity}</li>
<li><strong>Versions: </strong>1.0.0-5.4.7,6.0.0-6.1.2</li>
<li><strong>CVE Number:</strong> <a href="https://www.cve.org/CVERecord?id=CVE-2026-73373">CVE-2026-73373</a></li>
</ul>
<h3>Description</h3>
<div>The default list of dangerous files did not include <em>SHTML</em> files.</div>
<h3>Solution</h3>
<p>Upgrade to version 5.4.8, 6.1.3</p>
<h3>Contact</h3>
<p>The JSST at the Joomla! Security Centre 2.0.</p>]]></description>
</item>"""


def joomla_feed(*items):
    return f'<?xml version="1.0"?><rss version="2.0"><channel>{"".join(items)}</channel></rss>'


def joomla_item(number, article, title="Core - Unrestricted uploads", severity="Low"):
    return JOOMLA_ITEM.format(title=f"[{number}] - {title}", number=number, article=article, severity=severity)


@respx.mock
def test_joomla_security_feed_fields_and_pagination():
    route = respx.get("https://developer.joomla.org/security-centre.feed")
    route.side_effect = [
        httpx.Response(200, text=joomla_feed(
            joomla_item("20260810", 1077), joomla_item("20100423", 311, severity="Medium High"),
        )),
        httpx.Response(200, text=joomla_feed(
            joomla_item("20100423", 308), joomla_item("20131103", 400, title="Core XSS", severity=""),
        )),
        httpx.Response(200, text=joomla_feed()),
    ]
    with httpx.Client() as client:
        advisories = fetch_joomla_advisories(client)
    assert [a.identifier for a in advisories] == [
        "JOOMLA-20260810", "JOOMLA-20100423", "JOOMLA-20100423-308", "JOOMLA-20131103",
    ]
    first = advisories[0]
    assert first.title == "Core - Unrestricted uploads"
    assert first.severity == "low" and first.aliases == ["CVE-2026-73373"]
    assert first.fixed_versions == ["5.4.8", "6.1.3"]  # la section Contact est ignorée
    assert first.details == "The default list of dangerous files did not include SHTML files."
    assert first.url.endswith("/1077-20260810-core-issue.html") and first.published_at.day == 17
    assert advisories[1].severity == "high" and advisories[3].severity == "unknown"
    assert [dict(call.request.url.params)["limitstart"] for call in route.calls] == ["0", "2", "4"]


@respx.mock
def test_joomla_security_feed_stops_at_known_page():
    route = respx.get("https://developer.joomla.org/security-centre.feed")
    route.side_effect = [
        httpx.Response(200, text=joomla_feed(joomla_item("20260810", 1077))),
        httpx.Response(200, text=joomla_feed(joomla_item("20260701", 1070))),
    ]
    with httpx.Client() as client:
        advisories = fetch_joomla_advisories(client, known={"JOOMLA-20260810"})
    assert [a.identifier for a in advisories] == ["JOOMLA-20260810"] and route.call_count == 1
