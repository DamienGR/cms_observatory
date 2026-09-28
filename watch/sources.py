"""Collecte des releases (PyPI, Packagist, GitHub) et des avis de sécurité (OSV,
avis GitHub d'un dépôt, Security Centre de Joomla).

Fonctions pures : elles prennent un client HTTP et renvoient des dataclasses,
ce qui les rend faciles à tester avec des réponses simulées.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags

PRERELEASE_RE = re.compile(r"(a|b|rc|alpha|beta|dev)\d*", re.IGNORECASE)
SEVERITIES = {"LOW": "low", "MODERATE": "moderate", "MEDIUM": "moderate", "HIGH": "high", "CRITICAL": "critical"}
GITHUB_HEADERS = {"Accept": "application/vnd.github+json"}
CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}")
VERSION_RE = re.compile(r"\d+\.\d+(?:\.\d+)*")


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


def expand_minified(entries: list[dict]) -> list[dict]:
    """Format « p2 » minifié de Composer : chaque entrée ne contient que les clés qui
    changent par rapport à la précédente ; « __unset » supprime une clé."""
    expanded, previous = [], {}
    for entry in entries:
        current = dict(previous)
        for key, value in entry.items():
            if value == "__unset":
                current.pop(key, None)
            else:
                current[key] = value
        expanded.append(current)
        previous = current
    return expanded


def fetch_packagist_releases(package: str, client: httpx.Client) -> list[ReleaseData]:
    response = client.get(f"https://repo.packagist.org/p2/{package}.json")
    response.raise_for_status()
    data = response.json()
    entries = data["packages"][package]
    if data.get("minified"):
        entries = expand_minified(entries)
    releases = []
    for entry in entries:
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
        response = client.get(url, headers=GITHUB_HEADERS)
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
        severity=SEVERITIES.get(str(raw_severity).upper(), "unknown"),
        published_at=parse_datetime(vuln.get("published") or vuln["modified"]),
        aliases=vuln.get("aliases", []),
        fixed_versions=fixed,
        url=url,
    )


def fetch_github_advisories(repository: str, client: httpx.Client) -> list[AdvisoryData]:
    """Avis publiés dans l'onglet « Security » d'un dépôt (WordPress/wordpress-develop).

    Ils n'entrent pas dans la base GitHub consultée par OSV : l'écosystème est « other ».
    """
    url = f"https://api.github.com/repos/{repository}/security-advisories?state=published&per_page=100"
    advisories = []
    while url:
        response = client.get(url, headers=GITHUB_HEADERS)
        response.raise_for_status()
        advisories += [_parse_github_advisory(entry) for entry in response.json() if not entry.get("withdrawn_at")]
        url = response.links.get("next", {}).get("url")
    return advisories


def _parse_github_advisory(entry: dict) -> AdvisoryData:
    fixed = {
        version.strip()
        for vulnerability in entry.get("vulnerabilities") or []
        for version in (vulnerability.get("patched_versions") or "").split(",")
        if version.strip()
    }
    return AdvisoryData(
        identifier=entry["ghsa_id"],
        title=(entry.get("summary") or entry["ghsa_id"])[:500],
        details=entry.get("description") or "",
        severity=SEVERITIES.get(str(entry.get("severity")).upper(), "unknown"),
        published_at=parse_datetime(entry["published_at"]),
        aliases=[entry["cve_id"]] if entry.get("cve_id") else [],
        fixed_versions=sorted(fixed),
        url=entry["html_url"],
    )


JOOMLA_FEED_URL = "https://developer.joomla.org/security-centre.feed?type=rss"
JOOMLA_TITLE_RE = re.compile(r"^\[(\d+)\]\s*-?\s*(.+)$")
JOOMLA_ARTICLE_RE = re.compile(r"/security-centre/(\d+)-")
JOOMLA_FIELD_RE = re.compile(r"<strong>\s*([^<:]+?)\s*:\s*</strong>(.*?)</li>", re.DOTALL)


def fetch_joomla_advisories(client: httpx.Client, known=frozenset()) -> list[AdvisoryData]:
    """Flux RSS du Joomla! Security Centre, 25 avis par page, du plus récent au plus ancien.

    La pagination s'arrête à la première page qui contient un avis déjà connu :
    l'historique complet (plus de 15 pages) n'est lu qu'à la première collecte.
    """
    advisories, identifiers, start = [], set(), 0
    while True:
        response = client.get(JOOMLA_FEED_URL, params={"limitstart": start})
        response.raise_for_status()
        items = ElementTree.fromstring(response.content).findall("./channel/item")
        page = [advisory for item in items if (advisory := _parse_joomla_item(item))]
        for advisory in page:
            # En 2009-2010, plusieurs avis partagent le même numéro : on les distingue
            # par leur numéro d'article (le plus récent garde le numéro seul).
            if advisory.identifier in identifiers and (article := JOOMLA_ARTICLE_RE.search(advisory.url)):
                advisory.identifier += f"-{article[1]}"
            identifiers.add(advisory.identifier)
        advisories += page
        if not items or any(advisory.identifier in known for advisory in page):
            return advisories
        start += len(items)


def _parse_joomla_item(item) -> AdvisoryData | None:
    match = JOOMLA_TITLE_RE.match(item.findtext("title", "").strip())
    if not match:
        return None
    description = item.findtext("description", "")
    # En-tête en liste « Champ : valeur », puis des sections <h3> (Description, Solution…).
    header, *parts = re.split(r"<h3>\s*(.*?)\s*</h3>", description)
    sections = dict(zip(parts[::2], parts[1::2]))
    fields = {name: strip_tags(value).strip() for name, value in JOOMLA_FIELD_RE.findall(header)}
    solution = strip_tags(sections.get("Solution", ""))
    # Quelques anciens avis cumulent deux niveaux (« Medium High ») : le dernier prime.
    severity = (fields.get("Severity") or "unknown").split()[-1].upper()
    return AdvisoryData(
        identifier=f"JOOMLA-{match[1]}",
        title=match[2][:500],
        details=strip_tags(sections.get("Description", "")).strip(),
        severity=SEVERITIES.get(severity, "unknown"),
        published_at=parsedate_to_datetime(item.findtext("pubDate")),
        aliases=sorted(set(CVE_RE.findall(description))),
        fixed_versions=list(dict.fromkeys(VERSION_RE.findall(solution))),
        url=item.findtext("link", ""),
    )


RELEASE_FETCHERS = {
    "pypi": fetch_pypi_releases,
    "packagist": fetch_packagist_releases,
    "github": fetch_github_releases,
}
