import re

from django.conf import settings
from django.db import transaction
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.utils.translation import get_language, get_language_info

from cms.api import create_page_content
from cms.models import PageContent
from cms.utils.placeholder import get_placeholder_from_slot
from cms.utils.plugins import copy_plugins_to_placeholder, downcast_plugins

from . import prompts
from .conf import get_setting
from .models import CopilotLog
from .providers import ProviderError, get_provider

FENCE_RE = re.compile(r"^```[a-z]*\n?|\n?```$", re.IGNORECASE)


class CopilotError(Exception):
    pass


def language_name(code: str) -> str:
    try:
        return get_language_info(code)["name"]
    except KeyError:
        return code


def ask(system, prompt, *, action=CopilotLog.Action.CUSTOM, user=None, target=None, images=(), max_tokens=None):
    """Single entry point to the LLM: every call is logged, successful or not."""
    provider = get_provider()
    log = CopilotLog(
        action=action,
        user=user if user is not None and user.is_authenticated else None,
        model=provider.model,
        prompt=prompt[:4000],
    )
    if target is not None:
        log.target = target
    try:
        completion = provider.complete(system=system, prompt=prompt, images=images, max_tokens=max_tokens)
    except ProviderError as exc:
        log.status, log.error = CopilotLog.Status.ERROR, str(exc)[:4000]
        log.save()
        raise CopilotError(str(exc)) from exc
    text = FENCE_RE.sub("", completion.text.strip()).strip()
    log.result = text[:20000]
    log.model, log.input_tokens, log.output_tokens = completion.model, completion.input_tokens, completion.output_tokens
    log.save()
    return text


def extract_text(obj, limit=8000) -> str:
    """Plain text of an object: its title, then the text of the plugins in its placeholders."""
    chunks = [str(getattr(obj, "title", "") or obj)]
    placeholders = getattr(obj, "placeholders", None)
    if placeholders is not None:
        for placeholder in placeholders.all():
            for plugin in downcast_plugins(placeholder.get_plugins_list()):
                if body := getattr(plugin, "body", None):
                    chunks.append(strip_tags(body))
                config = getattr(plugin, "config", None)  # djangocms-frontend components
                if isinstance(config, dict):
                    chunks += [value for value in config.values() if isinstance(value, str)]
    return Truncator("\n".join(c.strip() for c in chunks if c.strip())).chars(limit)


def generate_summary_field(obj, field_name, *, user=None) -> str:
    field = obj._meta.get_field(field_name)
    max_length = min(field.max_length or 160, 160)
    language = getattr(obj, "language", None) or get_language()
    system = prompts.SUMMARY_FIELD.format(
        field=field.verbose_name, language=language_name(language), max_length=max_length
    )
    text = ask(system, extract_text(obj), action=CopilotLog.Action.SUMMARY, user=user, target=obj)
    return Truncator(text.strip('"« »')).chars(max_length)


def rewrite_html(html, instruction, *, user=None, target=None) -> str:
    prompt = f"Instruction: {instruction}\n\n{html}"
    return ask(prompts.REWRITE_HTML, prompt, action=CopilotLog.Action.REWRITE, user=user, target=target)


def translate_html(html, source, target_language, *, user=None, target=None) -> str:
    system = prompts.TRANSLATE_HTML.format(source=language_name(source), target=language_name(target_language))
    return ask(system, html, action=CopilotLog.Action.TRANSLATE, user=user, target=target)


def translate_text(text, source, target_language, *, user=None, target=None) -> str:
    system = prompts.TRANSLATE_TEXT.format(source=language_name(source), target=language_name(target_language))
    return ask(system, text, action=CopilotLog.Action.TRANSLATE, user=user, target=target)


def translate_page_content(source: PageContent, target_language: str, user) -> PageContent:
    """Create the ``target_language`` version of a page, translated, as a draft.

    The LLM calls happen first; the database is then written in one transaction.
    """
    page = source.page
    if PageContent.admin_manager.filter(page=page, language=target_language).exists():
        raise CopilotError(f"The page already has content in {target_language}.")

    lang = source.language
    title = translate_text(source.title, lang, target_language, user=user, target=source)
    meta = (
        translate_text(source.meta_description, lang, target_language, user=user, target=source)
        if source.meta_description
        else None
    )
    text_plugins = get_setting("TEXT_PLUGINS")
    placeholders = []
    for placeholder in source.get_placeholders():
        plugins = list(downcast_plugins(placeholder.get_plugins_list()))  # a generator: we iterate twice
        for plugin in plugins:
            if plugin.plugin_type in text_plugins and plugin.body:
                # In-memory change only: the translated body is what gets copied below.
                plugin.body = translate_html(plugin.body, lang, target_language, user=user, target=source)
                plugin.json, plugin.rte = None, ""  # the rich-text editor must re-read the HTML body
        placeholders.append((placeholder.slot, plugins))

    with transaction.atomic():
        target = create_page_content(
            target_language,
            title,
            page,
            meta_description=meta,
            created_by=user,
            template=source.template,
            in_navigation=source.in_navigation,
        )
        for slot, plugins in placeholders:
            copy_plugins_to_placeholder(
                plugins,
                placeholder=get_placeholder_from_slot(target.placeholders, slot),
                language=target_language,
                plugins_are_downcast=True,
            )
    return target


def suggest_alt_text(image, *, language=None, user=None) -> str:
    """Alt text for a django-filer image, using the model's vision capabilities."""
    language = language or settings.LANGUAGE_CODE
    with image.file.open("rb") as file:
        data = file.read()
    media_type = getattr(image, "mime_type", None) or "image/jpeg"
    system = prompts.ALT_TEXT.format(language=language_name(language))
    text = ask(
        system,
        f"File name: {image.original_filename}",
        action=CopilotLog.Action.ALT_TEXT,
        user=user,
        target=image,
        images=[(data, media_type)],
    )
    return Truncator(text).chars(125)
