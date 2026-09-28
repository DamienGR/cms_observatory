from cms.api import add_plugin, create_page, create_page_content
from cms.models import Page
from cms.utils.apphook_reload import reload_urlconf
from cms.utils.placeholder import get_placeholder_from_slot
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from djangocms_versioning.models import Version

from watch.site_content import ABOUT, HOME, LEGAL, WATCH


class Command(BaseCommand):
    help = (
        "Crée et publie les pages Accueil et Observatoire (FR et EN) d'un site vide, "
        "puis les pages À propos et Mentions légales si elles manquent."
    )

    def add_arguments(self, parser):
        parser.add_argument("--user", help="Auteur des versions publiées (par défaut : premier superutilisateur)")

    def handle(self, *args, user=None, **options):
        author = self.get_author(user)
        created = []
        with transaction.atomic():
            if not Page.objects.exists():
                self.create_home(author)
                self.create_watch_page(author)
                created += ["Accueil", "Observatoire"]
            # Pages ajoutées après la première version du site : créées aussi sur un site existant.
            for reverse_id, copy, in_navigation in (("about", ABOUT, True), ("legal-notice", LEGAL, False)):
                if not Page.objects.filter(reverse_id=reverse_id).exists():
                    self.create_text_page(author, reverse_id, copy, in_navigation)
                    created.append(copy["fr"]["title"])
        if not created:
            self.stdout.write("Toutes les pages existent déjà : rien à faire.")
            return
        reload_urlconf()
        self.stdout.write(self.style.SUCCESS(f"Pages créées et publiées : {', '.join(created)}."))

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

    def create_text_page(self, author, reverse_id, copy, in_navigation):
        page = create_page(
            copy["fr"]["title"], "page.html", "fr", slug=copy["fr"]["slug"], created_by=author,
            in_navigation=in_navigation, reverse_id=reverse_id,
        )
        create_page_content(
            "en", copy["en"]["title"], page, slug=copy["en"]["slug"], created_by=author, in_navigation=in_navigation,
        )
        for language, text in copy.items():
            content = page.get_admin_content(language)
            main = get_placeholder_from_slot(content.placeholders, "content")
            add_plugin(main, "TextPlugin", language, body=text["body"])
            self.publish(content, author)
        return page

    @staticmethod
    def publish(content, author):
        Version.objects.get_for_content(content).publish(author)
