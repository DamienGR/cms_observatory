from datetime import timedelta

import pytest
from cms.api import add_plugin
from cms.models import PageContent
from cms.plugin_pool import plugin_pool
from cms.utils.placeholder import get_placeholder_from_slot
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils import timezone
from menus.menu_pool import menu_pool

from watch.cms_plugins import ComparisonPlugin
from watch.models import Advisory, Release, TechnologyContent


def plugin_names(model):
    return {plugin.__name__ for plugin in plugin_pool.get_all_plugins_for_model(model)}


def test_model_specific_plugins(db):
    # allowed_models (sur le plugin) et allowed_plugins (sur le modèle) — django CMS 5.1
    assert {"TechnologyFactsPlugin", "TextPlugin", "Alias"} <= plugin_names(TechnologyContent)
    assert "TechnologyFactsPlugin" not in plugin_names(PageContent)
    assert "AlertPlugin" not in plugin_names(TechnologyContent)


def test_comparison_accepts_only_its_items(db):
    assert ComparisonPlugin.get_child_classes("content") == ["ComparisonItemPlugin"]


def test_dashboard_and_detail(client, technology_content):
    Release.objects.create(technology=technology_content.technology, version="5.1.3", published_at=timezone.now())
    response = client.get(reverse("watch:dashboard"))
    assert response.status_code == 200 and b"5.1.3" in response.content

    url = technology_content.get_absolute_url()
    assert url == "/fr/observatoire/django-cms/"
    placeholder = get_placeholder_from_slot(technology_content.placeholders, "content")
    add_plugin(placeholder, "TechnologyFactsPlugin", "fr")
    response = client.get(url)
    assert response.status_code == 200
    assert b"Le CMS Python" in response.content and b"5.1.3" in response.content


def test_menu_nodes_and_security_badge(rf, technology_content):
    Advisory.objects.create(
        technology=technology_content.technology, identifier="GHSA-1", title="XSS",
        published_at=timezone.now() - timedelta(days=3),
    )
    request = rf.get("/fr/")
    request.user = AnonymousUser()
    request.session = {}
    renderer = menu_pool.get_renderer(request)
    nodes = [n for n in renderer.get_nodes() if n.attr.get("technology_id")]
    assert [n.title for n in nodes] == ["django CMS"]
    assert nodes[0].attr["recent_advisories"] == 1


@pytest.mark.parametrize("path", ["/api/watch/technologies/", "/api/cms/"])
def test_no_public_api(client, db, path):
    assert client.get(path, follow=True).status_code == 404


def test_toolbar_collect_requires_post(admin_client, technology):
    url = reverse("admin:watch_technology_collect")
    assert admin_client.get(url).status_code == 405


def test_apphook_root_placeholder_in_edit_mode(admin_client, admin_user):
    """Apphook ajouté après coup (comme dans l'admin) : « intro » doit apparaître dans le brouillon."""
    from cms.api import create_page
    from cms.toolbar.utils import get_object_edit_url
    from cms.utils.apphook_reload import reload_urlconf
    from djangocms_versioning.models import Version

    page = create_page("Observatoire", "page.html", "fr", created_by=admin_user)
    page.application_urls, page.application_namespace = "WatchApphook", "watch"
    page.save()
    published = page.get_admin_content("fr")
    Version.objects.get_for_content(published).publish(admin_user)
    reload_urlconf()
    draft = Version.objects.get_for_content(published).copy(admin_user).content  # bouton « Modifier »
    assert not draft.placeholders.filter(slot="intro").exists()

    response = admin_client.get(get_object_edit_url(draft))
    assert response.status_code == 200
    assert draft.placeholders.filter(slot="intro").exists()
