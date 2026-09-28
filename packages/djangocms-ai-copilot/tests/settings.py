SECRET_KEY = "tests"
DEBUG = False
ALLOWED_HOSTS = ["*"]
SITE_ID = 1
ROOT_URLCONF = "tests.urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.sites", "django.contrib.staticfiles",
    "cms", "menus", "treebeard", "sekizai", "djangocms_text", "djangocms_versioning",
    "djangocms_ai_copilot",
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "cms.middleware.user.CurrentUserMiddleware",
    "cms.middleware.page.CurrentPageMiddleware",
    "cms.middleware.toolbar.ToolbarMiddleware",
    "cms.middleware.language.LanguageCookieMiddleware",
]
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": ["tests/templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "sekizai.context_processors.sekizai",
        "cms.context_processors.cms_settings",
    ]},
}]
LANGUAGE_CODE = "en"
LANGUAGES = [("en", "English"), ("fr", "French")]
CMS_TEMPLATES = [("page.html", "Page")]
STATIC_URL = "/static/"
USE_TZ = True
TASKS = {"default": {"BACKEND": "django.tasks.backends.immediate.ImmediateBackend", "QUEUES": ["default", "llm"]}}
DJANGOCMS_AI_COPILOT = {"PROVIDER": "djangocms_ai_copilot.providers.fake.FakeProvider"}
