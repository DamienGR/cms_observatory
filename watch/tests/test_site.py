from datetime import date, datetime

from cms.models import Page
from django.core.management import call_command
from django.template.loader import render_to_string
from django.utils import timezone

from watch.board import build_board, month_starts
from watch.models import Advisory


def test_welcome_page_replaced_for_visitors(client, db):
    """Site sans page : ni version du CMS, ni redirection vers la connexion à l'admin."""
    response = client.get("/fr/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "ouvre bientôt" in content
    assert "django CMS installation" not in content and "cms-welcome-config" not in content


def test_welcome_page_guides_staff(admin_client):
    content = admin_client.get("/fr/").content.decode()
    assert "setup_site" in content and "cms-welcome-config" in content


def test_error_pages_use_site_design(client, watch_page):
    response = client.get("/fr/page-qui-n-existe-pas/")
    assert response.status_code == 404
    assert b"Cette page n'existe pas" in response.content
    assert "Observatoire des CMS" in render_to_string("500.html")


def test_robots_txt(client, db):
    response = client.get("/robots.txt")
    assert response["Content-Type"].startswith("text/plain")
    assert b"Sitemap: http://testserver/sitemap.xml" in response.content


def test_month_starts_crosses_year():
    starts = month_starts(date(2026, 2, 15))
    assert starts[0] == date(2025, 3, 1) and starts[-1] == date(2026, 2, 1) and len(starts) == 12


def test_board_keeps_worst_severity_per_month(technology):
    def advisory(identifier, severity, day):
        Advisory.objects.create(
            technology=technology, identifier=identifier, title=identifier, severity=severity,
            published_at=timezone.make_aware(datetime(2026, 9, day)),
        )

    advisory("A", Advisory.Severity.LOW, 2)
    advisory("B", Advisory.Severity.CRITICAL, 3)
    advisory("C", Advisory.Severity.UNKNOWN, 4)
    advisory("OLD", Advisory.Severity.HIGH, 1)
    Advisory.objects.filter(identifier="OLD").update(published_at=timezone.make_aware(datetime(2024, 1, 1)))

    [row] = build_board([technology], today=date(2026, 9, 28))
    assert row.months[-1].count == 3 and row.months[-1].severity == "critical"
    assert row.advisory_count == 3


def test_setup_site_creates_published_pages(client, admin_user):
    call_command("setup_site")
    assert Page.objects.count() == 2
    response = client.get("/fr/")
    assert response.status_code == 200 and "Les versions et failles des CMS".encode() in response.content
    home_en = client.get("/en/").content
    assert b"CMS releases and vulnerabilities" in home_en and b'href="/en/observatory/"' in home_en
    assert client.get("/en/observatory/").status_code == 200
    call_command("setup_site")  # idempotente
    assert Page.objects.count() == 2
