from functools import wraps

from django.apps import apps
from django.core.exceptions import PermissionDenied

from cms.models import PageContent
from cms.utils.page_permissions import user_can_change_page
from cms.utils.permissions import get_model_permission_codename


def can_use_copilot(user) -> bool:
    return user.is_active and user.is_staff and user.has_perm("djangocms_ai_copilot.use_copilot")


def copilot_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not can_use_copilot(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


def content_is_editable(obj, user) -> bool:
    """True if ``obj`` may be changed now: a draft, not locked by someone else.

    Without djangocms-versioning (or for unversioned models) everything is editable.
    """
    if not apps.is_installed("djangocms_versioning"):
        return True
    from djangocms_versioning.helpers import get_version_for_content
    from djangocms_versioning.models import Version

    try:
        version = get_version_for_content(obj)
    except (KeyError, Version.DoesNotExist):
        return True
    return version.check_modify.as_bool(user)


def can_change_object(user, obj) -> bool:
    if not can_use_copilot(user) or not content_is_editable(obj, user):
        return False
    if isinstance(obj, PageContent):
        return user_can_change_page(user, obj.page)
    codename = get_model_permission_codename(type(obj), "change")
    return user.has_perm(codename) or user.has_perm(codename, obj)


def can_change_plugin(user, plugin) -> bool:
    """Same checks as the structure board: permissions, then source checks (draft, lock)."""
    placeholder = plugin.placeholder
    return (
        can_use_copilot(user)
        and placeholder.has_change_plugin_permission(user, plugin)
        and placeholder.check_source(user)
    )
