from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from djangocms_text.html import clean_html

from cms.models import CMSPlugin, PageContent
from cms.utils.i18n import get_language_tuple

from .conf import get_setting
from .forms import RewriteForm, TranslateForm
from .permissions import can_change_object, can_change_plugin, copilot_required
from .services import CopilotError, generate_summary_field, rewrite_html
from .tasks import translate_page_task


def get_summary_fields():
    return apps.get_app_config("djangocms_ai_copilot").cms_extension.summary_fields


@require_POST
@copilot_required
def summary_field_view(request):
    """AJAX target of the toolbar item: fills a registered summary field of a draft."""
    content_type = get_object_or_404(ContentType, pk=request.POST.get("content_type"))
    model = content_type.model_class()
    field_name = get_summary_fields().get(model)
    if field_name is None:
        return HttpResponseBadRequest("This model is not enabled for the copilot.")
    manager = getattr(model, "admin_manager", model._default_manager)  # drafts included
    obj = get_object_or_404(manager, pk=request.POST.get("object_id"))
    if not can_change_object(request.user, obj):
        raise PermissionDenied
    try:
        value = generate_summary_field(obj, field_name, user=request.user)
    except CopilotError as exc:
        return JsonResponse({"error": str(exc)}, status=502)
    setattr(obj, field_name, value)
    obj.save(update_fields=[field_name])
    return JsonResponse({field_name: value})


@copilot_required
def rewrite_view(request):
    """Modal opened from a text plugin's context menu: preview, then apply."""
    plugin = get_object_or_404(CMSPlugin, pk=request.GET.get("plugin"))
    if plugin.plugin_type not in get_setting("TEXT_PLUGINS"):
        return HttpResponseBadRequest("Not a text plugin.")
    if not can_change_plugin(request.user, plugin):
        raise PermissionDenied
    text = plugin.get_bound_plugin()
    form = RewriteForm(request.POST or None)
    proposal = None
    if request.method == "POST" and form.is_valid():
        if "_apply" in request.POST and form.cleaned_data["proposal"]:
            text.body = form.cleaned_data["proposal"]
            text.json, text.rte = None, ""
            text.save()
            # Closes the modal and refreshes the structure board in place.
            return text.get_plugin_class_instance().render_close_frame(request, obj=text)
        try:
            proposal = rewrite_html(
                text.body, form.get_instruction(), user=request.user, target=plugin.placeholder.source
            )
        except CopilotError as exc:
            form.add_error(None, str(exc))
        else:
            form = RewriteForm(initial={**form.cleaned_data, "proposal": proposal})
    return render(
        request,
        "djangocms_ai_copilot/rewrite.html",
        {
            "form": form,
            "original": text.body,
            "proposal": clean_html(proposal) if proposal else None,  # model output: sanitize before display
            "title": _("AI rewrite"),
            "is_popup": True,
        },
    )


@copilot_required
def translate_view(request):
    """Modal opened from the toolbar: queue the translation of the current page."""
    source = get_object_or_404(PageContent.admin_manager.select_related("page"), pk=request.GET.get("content"))
    if not can_change_object(request.user, source):
        raise PermissionDenied
    existing = set(PageContent.admin_manager.filter(page=source.page).values_list("language", flat=True))
    languages = [(code, name) for code, name in get_language_tuple(source.page.site_id) if code not in existing]
    form = TranslateForm(request.POST or None, languages=languages)
    result = None
    if request.method == "POST" and form.is_valid():
        result = translate_page_task.enqueue(source.pk, form.cleaned_data["target_language"], request.user.pk)
    return render(
        request,
        "djangocms_ai_copilot/translate.html",
        {"form": form, "source": source, "languages": languages, "result": result, "title": _("AI translation"), "is_popup": True},
    )
