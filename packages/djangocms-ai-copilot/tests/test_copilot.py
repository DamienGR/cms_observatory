import pytest
from cms.models import CMSPlugin, PageContent
from cms.utils.urlutils import admin_reverse
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from djangocms_versioning.models import Version

from djangocms_ai_copilot.cms_config import CopilotCMSExtension
from djangocms_ai_copilot.models import CopilotLog
from djangocms_ai_copilot.providers import ProviderError
from djangocms_ai_copilot.providers.fake import FakeProvider
from djangocms_ai_copilot.services import CopilotError, ask, translate_page_content


def summary_url_and_data(content):
    return admin_reverse("copilot_summary_field"), {
        "content_type": ContentType.objects.get_for_model(content).pk,
        "object_id": content.pk,
    }


def test_ask_logs_every_call(db, monkeypatch):
    FakeProvider.responses = ["```html\n<p>ok</p>\n```"]
    assert ask("system", "prompt") == "<p>ok</p>"  # code fences stripped
    monkeypatch.setattr(FakeProvider, "complete", lambda self, **kw: (_ for _ in ()).throw(ProviderError("quota")))
    with pytest.raises(CopilotError):
        ask("system", "prompt")
    assert list(CopilotLog.objects.order_by("pk").values_list("status", flat=True)) == ["ok", "error"]


def test_summary_field_writes_the_draft(client, editor, page_content):
    FakeProvider.responses = ["A web agency building websites in Figeac."]
    client.force_login(editor)
    url, data = summary_url_and_data(page_content)
    response = client.post(url, data)
    assert response.status_code == 200
    page_content.refresh_from_db()
    assert page_content.meta_description == "A web agency building websites in Figeac."
    assert "We build websites" in FakeProvider.calls[0]["prompt"]


def test_published_content_is_read_only(client, editor, page_content):
    Version.objects.get_for_content(page_content).publish(editor)
    client.force_login(editor)
    url, data = summary_url_and_data(page_content)
    assert client.post(url, data).status_code == 403
    assert FakeProvider.calls == []  # no tokens spent


def test_copilot_permission_is_required(client, staff_without_copilot, page_content):
    client.force_login(staff_without_copilot)
    url, data = summary_url_and_data(page_content)
    assert client.post(url, data).status_code == 403


def test_rewrite_preview_then_apply(client, editor, page_content):
    plugin = CMSPlugin.objects.get(plugin_type="TextPlugin")
    url = admin_reverse("copilot_rewrite") + f"?plugin={plugin.pk}"
    client.force_login(editor)
    FakeProvider.responses = ["<p>We craft websites.</p><script>alert(1)</script>"]
    response = client.post(url, {"preset": "shorten", "_preview": "1"})
    assert b"We craft websites." in response.content
    assert b"<script>alert(1)" not in response.content  # model output is sanitized
    response = client.post(url, {"preset": "shorten", "proposal": "<p>We craft websites.</p>", "_apply": "1"})
    assert b'id="data-bridge"' in response.content  # structure board refreshed in place
    assert plugin.get_bound_plugin().body == "<p>We craft websites.</p>"


def test_translation_creates_a_translated_draft(editor, page_content):
    FakeProvider.responses = ["À propos", '<p>Nous créons des <a href="/cms/">sites</a>.</p>']
    french = translate_page_content(page_content, "fr", editor)
    assert french.title == "À propos"
    assert Version.objects.get_for_content(french).state == "draft"
    text = CMSPlugin.objects.get(placeholder__in=french.placeholders.all()).get_bound_plugin()
    assert text.body == '<p>Nous créons des <a href="/cms/">sites</a>.</p>'
    assert text.language == "fr"
    with pytest.raises(CopilotError):
        translate_page_content(page_content, "fr", editor)  # never overwrite an existing language


def test_extension_rejects_unknown_fields():
    class BrokenConfig:
        copilot_summary_fields = {PageContent: "does_not_exist"}

    with pytest.raises(Exception):
        CopilotCMSExtension().configure_app(BrokenConfig())
    with pytest.raises(ImproperlyConfigured):
        CopilotCMSExtension().configure_app(type("C", (), {"copilot_summary_fields": ["x"]})())


def test_toolbar_and_context_menu(client, editor, page_content):
    from cms.toolbar.utils import get_object_edit_url, get_object_structure_url

    client.force_login(editor)
    assert "Translate this page" in client.get(get_object_edit_url(page_content)).content.decode()
    assert "Rewrite with AI" in client.get(get_object_structure_url(page_content)).content.decode()
