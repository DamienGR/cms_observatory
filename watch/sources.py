"""Collecte des releases (PyPI, Packagist, GitHub) et des avis de sécurité (base OSV).

Fonctions pures : elles prennent un client HTTP et renvoient des dataclasses,
ce qui les rend faciles à tester avec des réponses simulées.
"""

import re
from dataclasses import dataclass
from datetime import datetime

import httpx
from django.conf import settings
from django.utils.dateparse import parse_datetime

PRERELEASE_RE = re.compile(r"(a|b|rc|alpha|beta|dev)\d*", re.IGNORECASE)
OSV_SEVERITIES = {"LOW": "low", "MODERATE": "moderate", "MEDIUM": "moderate", "HIGH": "high", "CRITICAL": "critical"}


@dataclass
class ReleaseData:
    version: str
    published_at: datetime
    url: str
    is_prerelease: bool


@dataclass
class AdvisoryData:
    identifier: str
    title: str
    details: str
    severity: str
    published_at: datetime
    aliases: list
    fixed_versions: list
    url: str


def http_client() -> httpx.Client:
    return httpx.Client(
        timeout=settings.WATCH_HTTP_TIMEOUT,
        headers={"User-Agent": settings.WATCH_USER_AGENT},
        follow_redirects=True,
    )


def fetch_pypi_releases(package: str, client: httpx.Client) -> list[ReleaseData]:
    response = client.get(f"https://pypi.org/pypi/{package}/json")
    response.raise_for_status()
    releases = []
    for version, files in response.json()["releases"].items():
        files = [f for f in files if not f.get("yanked")]
        if not files:
            continue
        releases.append(
            ReleaseData(
                version=version,
                published_at=min(parse_datetime(f["upload_time_iso_8601"]) for f in files),
                url=f"https://pypi.org/project/{package}/{version}/",
                is_prerelease=bool(PRERELEASE_RE.search(version)),
            )
        )
    return releases


def fetch_packagist_releases(package: str, client: httpx.Client) -> list[ReleaseData]:
    # Format « p2 » minifié : chaque entrée ne contient que les clés qui changent,
    # mais « version » et « time » changent à chaque release.
    response = client.get(f"https://repo.packagist.org/p2/{package}.json")
    response.raise_for_status()
    releases = []
    for entry in response.json()["packages"][package]:
        version, time = entry.get("version"), entry.get("time")
        if not version or not time:
            continue
        version = version.removeprefix("v")
        releases.append(
            ReleaseData(
                version=version,
                published_at=parse_datetime(time),
                url=f"https://packagist.org/packages/{package}#{version}",
                is_prerelease=bool(PRERELEASE_RE.search(version)),
            )
        )
    return releases


def fetch_github_releases(repository: str, client: httpx.Client) -> list[ReleaseData]:
    # Pour les projets absents des registres (Joomla). Sans jeton, GitHub autorise
    # 60 requêtes par heure : largement assez pour une collecte toutes les six heures.
    url = f"https://api.github.com/repos/{repository}/releases?per_page=100"
    releases = []
    while url:
        response = client.get(url, headers={"Accept": "application/vnd.github+json"})
        response.raise_for_status()
        for entry in response.json():
            if entry.get("draft") or not entry.get("published_at"):
                continue
            version = entry["tag_name"].removeprefix("v")
            releases.append(
                ReleaseData(
                    version=version,
                    published_at=parse_datetime(entry["published_at"]),
                    url=entry["html_url"],
                    is_prerelease=entry.get("prerelease", False) or bool(PRERELEASE_RE.search(version)),
                )
            )
        url = response.links.get("next", {}).get("url")
    return releases


def fetch_osv_advisories(ecosystem: str, package: str, client: httpx.Client) -> list[AdvisoryData]:
    query = {"package": {"name": package, "ecosystem": ecosystem}}
    advisories = []
    while True:
        response = client.post("https://api.osv.dev/v1/query", json=query)
        response.raise_for_status()
        data = response.json()
        advisories += [_parse_osv(vuln, package) for vuln in data.get("vulns", [])]
        if not data.get("next_page_token"):
            return advisories
        query["page_token"] = data["next_page_token"]


def _parse_osv(vuln: dict, package: str) -> AdvisoryData:
    fixed = sorted(
        {
            event["fixed"]
            for affected in vuln.get("affected", [])
            if affected.get("package", {}).get("name") == package
            for version_range in affected.get("ranges", [])
            for event in version_range.get("events", [])
            if "fixed" in event
        }
    )
    references = vuln.get("references", [])
    url = next(
        (ref["url"] for ref in references if ref.get("type") == "ADVISORY"),
        f"https://osv.dev/vulnerability/{vuln['id']}",
    )
    raw_severity = (vuln.get("database_specific") or {}).get("severity", "")
    return AdvisoryData(
        identifier=vuln["id"],
        title=(vuln.get("summary") or vuln["id"])[:500],
        details=vuln.get("details", ""),
        severity=OSV_SEVERITIES.get(str(raw_severity).upper(), "unknown"),
        published_at=parse_datetime(vuln.get("published") or vuln["modified"]),
        aliases=vuln.get("aliases", []),
        fixed_versions=fixed,
        url=url,
    )


RELEASE_FETCHERS = {
    "pypi": fetch_pypi_releases,
    "packagist": fetch_packagist_releases,
    "github": fetch_github_releases,
}
