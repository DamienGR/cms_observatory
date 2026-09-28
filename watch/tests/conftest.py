import pytest
from cms.api import create_page
from cms.utils.apphook_reload import reload_urlconf
from django.core.cache import caches
from djangocms_versioning.models import Version

from watch.models import Technology, TechnologyContent


def publish(content, user):
    Version.objects.get_for_content(content).publish(user)


@pytest.fixture(autouse=True)
def clear_caches():
    """Les caches locmem survivent aux tests alors que les identifiants de page sont réutilisés."""
    for cache in caches.all():
        cache.clear()
@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_superuser("admin", "admin@example.com", "password")


@pytest.fixture
def technology(db):
    return Technology.objects.create(name="django CMS", slug="django-cms", registry="pypi", package="django-cms")


@pytest.fixture
def watch_page(admin_user):
    page = create_page(
        "Observatoire", "page.html", "fr", created_by=admin_user,
        apphook="WatchApphook", apphook_namespace="watch", in_navigation=True,
    )
    publish(page.get_admin_content("fr"), admin_user)
    reload_urlconf()  # l'apphook ajoute ses URL au resolver
    return page


@pytest.fixture
def technology_content(technology, admin_user, watch_page):
    content = TechnologyContent.objects.with_user(admin_user).create(
        technology=technology, language="fr", tagline="Le CMS Python"
    )
    publish(content, admin_user)
    return content
