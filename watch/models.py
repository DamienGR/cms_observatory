from django.db import models
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from packaging.version import InvalidVersion, Version

from cms.extensions import PageExtension
from cms.extensions.extension_pool import extension_pool
from cms.models import CMSPlugin
from cms.models.fields import PlaceholderRelationField


class Technology(models.Model):
    """Grouper : les données qui ne dépendent ni de la langue ni d'une version éditoriale."""

    class Registry(models.TextChoices):
        PYPI = "pypi", "PyPI"
        PACKAGIST = "packagist", "Packagist"
        GITHUB = "github", "GitHub"

    name = models.CharField(_("nom"), max_length=100)
    slug = models.SlugField(unique=True)
    website = models.URLField(_("site officiel"), blank=True)
    registry = models.CharField(_("registre"), max_length=20, choices=Registry.choices)
    package = models.CharField(
        _("paquet"), max_length=200,
        help_text=_("Ex. django-cms (PyPI), drupal/core (Packagist) ou joomla/joomla-cms (dépôt GitHub)"),
    )
    is_tracked = models.BooleanField(_("collecte active"), default=True)
    last_collected_at = models.DateTimeField(_("dernière collecte"), null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("technologie")
        verbose_name_plural = _("technologies")

    def __str__(self):
        return self.name

    @property
    def osv_ecosystem(self):
        # Les projets PHP publiés seulement sur GitHub (Joomla) sont référencés dans
        # OSV sous l'écosystème Packagist, avec le nom de leur dépôt.
        return {"pypi": "PyPI", "packagist": "Packagist", "github": "Packagist"}[self.registry]

    def latest_release(self):
        """Plus haute version parmi les 50 dernières publiées (les branches LTS se chevauchent)."""

        def key(release):
            try:
                return Version(release.version)
            except InvalidVersion:
                return Version("0")

        return max(self.releases.filter(is_prerelease=False)[:50], key=key, default=None)


class TechnologyContent(models.Model):
    """Contenu éditorial, versionné et traduisible, d'une fiche technologie."""

    technology = models.ForeignKey(Technology, on_delete=models.CASCADE, related_name="contents")
    language = models.CharField(_("langue"), max_length=10)
    tagline = models.CharField(_("accroche"), max_length=200)
    verdict = models.TextField(_("notre avis"), blank=True)
    placeholders = PlaceholderRelationField()

    # django CMS 5.1 : seuls ces plugins sont proposés dans les placeholders de la fiche.
    allowed_plugins = [
        "TextPlugin",
        "TechnologyFactsPlugin",
        "LatestReleasesPlugin",
        "ImagePlugin",
        "LinkPlugin",
        "Alias",  # le plugin de djangocms-alias s'appelle simplement « Alias »
    ]

    class Meta:
        verbose_name = _("fiche technologie")
        verbose_name_plural = _("fiches technologie")

    def __str__(self):
        return f"{self.technology} ({self.language})"

    def get_template(self):
        return "watch/technology_detail.html"

    def get_absolute_url(self):
        with override(self.language):
            try:
                return reverse("watch:technology-detail", kwargs={"slug": self.technology.slug})
            except NoReverseMatch:  # l'apphook n'est pas (encore) publié
                return None


class Release(models.Model):
    technology = models.ForeignKey(Technology, on_delete=models.CASCADE, related_name="releases")
    version = models.CharField(max_length=50)
    published_at = models.DateTimeField(_("publiée le"))
    url = models.URLField(blank=True)
    is_prerelease = models.BooleanField(_("pré-version"), default=False)
    is_security = models.BooleanField(_("corrige une faille"), default=False)

    class Meta:
        ordering = ["-published_at"]
        constraints = [
            models.UniqueConstraint(fields=["technology", "version"], name="unique_release_per_technology")
        ]
        verbose_name = _("release")

    def __str__(self):
        return f"{self.technology} {self.version}"


class Advisory(models.Model):
    class Severity(models.TextChoices):
        LOW = "low", _("faible")
        MODERATE = "moderate", _("modérée")
        HIGH = "high", _("élevée")
        CRITICAL = "critical", _("critique")
        UNKNOWN = "unknown", _("inconnue")

    technology = models.ForeignKey(Technology, on_delete=models.CASCADE, related_name="advisories")
    identifier = models.CharField(_("identifiant"), max_length=100)
    aliases = models.JSONField(default=list, blank=True)
    title = models.CharField(_("titre"), max_length=500)
    details = models.TextField(blank=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.UNKNOWN)
    published_at = models.DateTimeField(_("publié le"))
    fixed_versions = models.JSONField(_("versions correctives"), default=list, blank=True)
    url = models.URLField(blank=True)
    summary = models.TextField(_("résumé IA"), blank=True)

    class Meta:
        ordering = ["-published_at"]
        constraints = [
            models.UniqueConstraint(fields=["technology", "identifier"], name="unique_advisory_per_technology")
        ]
        verbose_name = _("avis de sécurité")
        verbose_name_plural = _("avis de sécurité")

    def __str__(self):
        return self.identifier


# --- Plugins -----------------------------------------------------------------


class LatestReleasesPluginModel(CMSPlugin):
    technology = models.ForeignKey(
        Technology, on_delete=models.CASCADE, null=True, blank=True,
        help_text=_("Vide = toutes les technologies"),
    )
    limit = models.PositiveSmallIntegerField(_("nombre"), default=5)
    only_security = models.BooleanField(_("seulement les correctifs de sécurité"), default=False)

    def __str__(self):
        return str(self.technology or _("toutes"))


class Comparison(CMSPlugin):
    title = models.CharField(_("titre"), max_length=200)

    def __str__(self):
        return self.title


class ComparisonItem(CMSPlugin):
    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField(_("note /5"), default=3)
    pros = models.TextField(_("points forts"), blank=True)
    cons = models.TextField(_("points faibles"), blank=True)

    def __str__(self):
        return f"{self.technology} ({self.score}/5)"


# --- Extension de page --------------------------------------------------------


class PageTechnologyExtension(PageExtension):
    """Relie une page CMS à la technologie dont elle parle (même valeur pour toutes les langues)."""

    technology = models.ForeignKey(
        Technology, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        verbose_name = _("technologie de la page")


extension_pool.register(PageTechnologyExtension)
