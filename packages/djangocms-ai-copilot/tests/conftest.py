import pytest
from cms.api import add_plugin, create_page
from django.contrib.auth.models import Permission

from djangocms_ai_copilot.providers.fake import FakeProvider


@pytest.fixture(autouse=True)
def fake_provider():
    FakeProvider.reset()
    yield FakeProvider


@pytest.fixture
def editor(django_user_model):
    user = django_user_model.objects.create_superuser("editor", "editor@example.com", "password")
    return user


@pytest.fixture
def staff_without_copilot(django_user_model):
    user = django_user_model.objects.create_user("staff", "staff@example.com", "password", is_staff=True)
    user.user_permissions.add(*Permission.objects.filter(codename__in=["change_page", "change_pagecontent"]))
    return user


@pytest.fixture
def page_content(editor):
    """A draft page (djangocms-versioning) with one text plugin."""
    page = create_page("About us", "page.html", "en", created_by=editor)
    content = page.get_admin_content("en")
    placeholder = content.get_placeholders().get(slot="content")
    add_plugin(placeholder, "TextPlugin", "en", body='<p>We build <a href="/cms/">websites</a>.</p>')
    return content
