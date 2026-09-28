from django.core.management.base import BaseCommand

from watch.models import Technology
from watch.tasks import collect_technology_task


class Command(BaseCommand):
    help = "Met en file la collecte des releases et avis de sécurité des technologies suivies."

    def add_arguments(self, parser):
        parser.add_argument("slugs", nargs="*", help="Limiter à certaines technologies (slugs)")

    def handle(self, *args, slugs, **options):
        technologies = Technology.objects.filter(is_tracked=True)
        if slugs:
            technologies = technologies.filter(slug__in=slugs)
        for technology in technologies:
            result = collect_technology_task.enqueue(technology.pk)
            self.stdout.write(f"{technology.slug} : tâche {result.id} ({result.status})")
