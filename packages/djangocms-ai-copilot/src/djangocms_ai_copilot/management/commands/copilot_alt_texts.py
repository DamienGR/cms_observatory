from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from djangocms_ai_copilot.tasks import alt_text_task


class Command(BaseCommand):
    help = "Queue alt text generation for django-filer images that have none."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--language", default=settings.LANGUAGE_CODE)

    def handle(self, *args, limit, language, **options):
        from filer.models import Image

        missing = Q(default_alt_text="") | Q(default_alt_text__isnull=True)
        images = Image.objects.filter(missing)[:limit]
        for image in images:
            alt_text_task.enqueue(image.pk, language)
        self.stdout.write(f"{len(images)} image(s) queued.")
