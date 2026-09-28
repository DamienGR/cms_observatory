"""Réglages de l'Observatoire des CMS — django CMS 5.1 sur Django 6.1."""

import os
from pathlib import Path

import dj_database_url
from django.utils.csp import CSP
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(int(default))).lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o]

INSTALLED_APPS = [
    "djangocms_simple_admin_style",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    # django CMS et son écosystème
    "cms",
    "menus",
    "treebeard",
    "sekizai",
    "djangocms_text",
    "djangocms_link",
    "djangocms_alias",
    "djangocms_versioning",
    "djangocms_moderation",
    "djangocms_stories",
    "taggit",
    "parler",
    "djangocms_form_builder",
    "djangocms_rest",
    "rest_framework",
    "filer",
    "easy_thumbnails",
    "djangocms_frontend",
    "djangocms_frontend.contrib.alert",
    "djangocms_frontend.contrib.badge",
    "djangocms_frontend.contrib.card",
    "djangocms_frontend.contrib.content",
    "djangocms_frontend.contrib.grid",
    "djangocms_frontend.contrib.icon",
    "djangocms_frontend.contrib.image",
    "djangocms_frontend.contrib.link",
    "djangocms_frontend.contrib.listgroup",
    "djangocms_frontend.contrib.tabs",
    "djangocms_frontend.contrib.utilities",
    # Tâches de fond (backend base de données pour django.tasks)
    "django_tasks_db",
    # Nos applications
    "djangocms_ai_copilot",
    "watch",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "cms.middleware.user.CurrentUserMiddleware",
    "cms.middleware.page.CurrentPageMiddleware",
    "cms.middleware.toolbar.ToolbarMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "cms.middleware.language.LanguageCookieMiddleware",
    "cms.middleware.utils.ApphookReloadMiddleware",
]

ROOT_URLCONF = "observatoire.urls"
WSGI_APPLICATION = "observatoire.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "observatoire" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.template.context_processors.csp",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sekizai.context_processors.sekizai",
                "cms.context_processors.cms_settings",
            ],
        },
    },
]

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "menus": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "menus"},
}
if os.environ.get("REDIS_URL"):
    CACHES = {
        alias: {"BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": os.environ["REDIS_URL"], "KEY_PREFIX": alias}
        for alias in ("default", "menus")
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Langues -----------------------------------------------------------------
LANGUAGE_CODE = "fr"
LANGUAGES = [("fr", _("Français")), ("en", _("English"))]
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

SITE_ID = 1

CMS_LANGUAGES = {
    1: [
        {"code": "fr", "name": _("Français"), "public": True, "fallbacks": ["en"]},
        {"code": "en", "name": _("English"), "public": True, "fallbacks": ["fr"]},
    ],
    "default": {"public": True, "hide_untranslated": False, "redirect_on_fallback": True},
}
PARLER_LANGUAGES = {
    1: ({"code": "fr"}, {"code": "en"}),
    "default": {"fallbacks": ["fr"], "hide_untranslated": False},
}

# --- django CMS --------------------------------------------------------------
CMS_TEMPLATES = [
    ("page.html", _("Standard")),
    ("landing.html", _("Accueil")),
]
CMS_PERMISSION = True
CMS_MENU_CACHE_BACKEND = "menus"
CMS_PLACEHOLDER_CONF = {
    "hero": {
        "name": _("Bandeau"),
        "plugins": ["ObservatoryHeroPlugin"],
        "limits": {"global": 1},
    },
}
X_FRAME_OPTIONS = "SAMEORIGIN"
CMS_LEGACY_STYLE = False  # thème 5.1 de l'admin, sans auto-détection
TEXT_INLINE_EDITING = True
CMS_TOOLBAR_ANONYMOUS_ON = False
DJANGOCMS_VERSIONING_ALLOW_DELETING_VERSIONS = True

THUMBNAIL_PROCESSORS = (
    "easy_thumbnails.processors.colorspace",
    "easy_thumbnails.processors.autocrop",
    "filer.thumbnail_processors.scale_and_crop_with_subject_location",
    "easy_thumbnails.processors.filters",
)

# --- Fichiers statiques et médias -------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "observatoire" / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# --- Sécurité : Content Security Policy à nonce (Django 6.1 + django CMS 5.1) --
_csp = {
    "default-src": [CSP.SELF],
    # Bootstrap, polices et thème sont servis par le site : aucun CDN autorisé.
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [CSP.SELF, CSP.NONCE],
    "img-src": [CSP.SELF, "data:"],
    "font-src": [CSP.SELF],
    "frame-ancestors": [CSP.SELF],
}
if env_bool("DJANGO_CSP_ENFORCE"):
    SECURE_CSP = _csp
else:
    SECURE_CSP_REPORT_ONLY = _csp

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
    "loggers": {"django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False}},
}

# --- Tâches de fond (django.tasks) ------------------------------------------
TASKS = {
    "default": {
        "BACKEND": os.environ.get("TASKS_BACKEND", "django.tasks.backends.immediate.ImmediateBackend"),
        "QUEUES": ["default", "llm"],
    }
}

# --- API ----------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
}

# --- Copilote IA (package djangocms-ai-copilot) ------------------------------
DJANGOCMS_AI_COPILOT = {
    "PROVIDER": os.environ.get("COPILOT_PROVIDER", "djangocms_ai_copilot.providers.anthropic.AnthropicProvider"),
    "MODEL": os.environ.get("COPILOT_MODEL", "claude-sonnet-5"),
    "API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
    "MAX_TOKENS": 2048,
}

# --- Observatoire -------------------------------------------------------------
WATCH_HTTP_TIMEOUT = 20
WATCH_USER_AGENT = "observatoire-cms/1.0 (+https://example.org)"
