from django.contrib.auth import get_user_model

from cms.models import PageContent

from .compat import task
from .services import suggest_alt_text, translate_page_content


@task(queue_name="llm")
def translate_page_task(content_id: int, target_language: str, user_id: int) -> int:
    source = PageContent.admin_manager.select_related("page").get(pk=content_id)
    user = get_user_model().objects.get(pk=user_id)
    return translate_page_content(source, target_language, user).pk


@task(queue_name="llm", priority=-20)
def alt_text_task(image_id: int, language: str) -> str:
    from filer.models import Image

    image = Image.objects.get(pk=image_id)
    image.default_alt_text = suggest_alt_text(image, language=language)
    image.save(update_fields=["default_alt_text"])
    return image.default_alt_text
