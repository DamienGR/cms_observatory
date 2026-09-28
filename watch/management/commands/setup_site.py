from cms.api import add_plugin, create_page, create_page_content
from cms.models import Page
from cms.utils.apphook_reload import reload_urlconf
from cms.utils.placeholder import get_placeholder_from_slot
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from djangocms_versioning.models import Version

# Contenu initial des deux pages, par langue. Les éditeurs le reprennent ensuite dans le CMS.
HOME = {
    "fr": {
        "title": "Accueil",
        "hero_title": "Les versions et failles des CMS, suivies pour vous",
        "hero_subtitle": "Drupal, WordPress, django CMS et Wagtail : dernières releases et avis de "
        "sécurité, collectés automatiquement plusieurs fois par jour.",
        "sidebar_title": "<h2>Correctifs de sécurité</h2>",
        "text": "<p>L'observatoire interroge PyPI, Packagist et OSV.dev, puis résume chaque avis "
        "de sécurité pour que vous sachiez en un coup d'œil s'il faut mettre à jour.</p><h2>Dernières releases</h2>",
    },
    "en": {
        "title": "Home",
        "hero_title": "CMS releases and vulnerabilities, tracked for you",
        "hero_subtitle": "Drupal, WordPress, django CMS and Wagtail: latest releases and security "
        "advisories, collected automatically several times a day.",
        "sidebar_title": "<h2>Security fixes</h2>",
        "text": "<p>The observatory queries PyPI, Packagist and OSV.dev, then summarises each "
        "security advisory so you know at a glance whether to upgrade.</p><h2>Latest releases</h2>",
    },
}
WATCH = {"fr": ("Observatoire", "observatoire"), "en": ("Observatory", "observatory")}


class Command(BaseCommand):
    help = "Crée et publie les pages Accueil et Observatoire (FR et EN) d'un site vide."

    def add_arguments(self, parser):
        parser.add_argument("--user", help="Auteur des versions publiées (par défaut : premier superutilisateur)")

    def handle(self, *args, user=None, **options):
        if Page.objects.exists():
            self.stdout.write("Le site a déjà des pages : rien à faire.")
            return
        author = self.get_author(user)
        with transaction.atomic():
            home = self.create_home(author)
            self.create_watch_page(author)
        reload_urlconf()
        self.stdout.write(self.style.SUCCESS(f"Pages créées et publiées (accueil : {home.get_absolute_url('fr')})."))

    def get_author(self, username):
        users = get_user_model().objects
        author = users.filter(username=username).first() if username else users.filter(is_superuser=True).first()
        if author is None:
            raise CommandError("Aucun utilisateur trouvé : lancez d'abord createsuperuser ou passez --user.")
        return author

    def create_home(self, author):
        page = create_page(HOME["fr"]["title"], "landing.html", "fr", created_by=author, in_navigation=False)
        create_page_content("en", HOME["en"]["title"], page, created_by=author, template="landing.html")
        for language, copy in HOME.items():
            content = page.get_admin_content(language)
            hero = get_placeholder_from_slot(content.placeholders, "hero")
            add_plugin(
                hero, "ObservatoryHeroPlugin", language,
                config={"title": copy["hero_title"], "subtitle": copy["hero_subtitle"]},
            )
            main = get_placeholder_from_slot(content.placeholders, "content")
            add_plugin(main, "TextPlugin", language, body=copy["text"])
            add_plugin(main, "LatestReleasesPlugin", language, limit=8)
            sidebar = get_placeholder_from_slot(content.placeholders, "sidebar")
            add_plugin(sidebar, "TextPlugin", language, body=copy["sidebar_title"])
            add_plugin(sidebar, "LatestReleasesPlugin", language, limit=5, only_security=True)
            self.publish(content, author)
        page.set_as_homepage(author)
        return page

    def create_watch_page(self, author):
        title, slug = WATCH["fr"]
        page = create_page(
            title, "page.html", "fr", slug=slug, created_by=author, in_navigation=True,
            apphook="WatchApphook", apphook_namespace="watch",
        )
        title, slug = WATCH["en"]
        create_page_content("en", title, page, slug=slug, created_by=author, in_navigation=True)
        for language in WATCH:
            self.publish(page.get_admin_content(language), author)
        return page

    @staticmethod
    def publish(content, author):
        Version.objects.get_for_content(content).publish(author)
