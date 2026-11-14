"""Django settings for 蛇記冰室 Snake Kee Café."""
import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key

from snakekee import lakebase

lakebase.load_dotenv()  # read .env (LAKEBASE_PROJECT, DATABRICKS_CONFIG_PROFILE, DJANGO_DEBUG, ...)

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"  # .env.example turns it on for local development
# The demo has no logins or sessions. Without DJANGO_SECRET_KEY we use a random key per process.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or ("dev-only-not-secret" if DEBUG else get_random_secret_key())
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "shop",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "snakekee.urls"
WSGI_APPLICATION = "snakekee.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "frontend" / "dist"],  # the built React app's index.html
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    },
]

# ---------------------------------------------------------------- database: Lakebase (it's just Postgres)
DATABASES = {
    "default": {
        # Stock Django PostgreSQL backend + a fresh OAuth token per connection (see snakekee/db/base.py).
        # Host and branch are resolved from your git branch (see snakekee/lakebase.py).
        "ENGINE": "snakekee.db",
        "NAME": "databricks_postgres",
        "OPTIONS": {"sslmode": "require"},
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }
}

# LAKEBASE=1 python manage.py test
#   -> run the test suite against THIS branch's data (a copy of production) instead of
#      Django's brand-new empty test database. See snakekee/testrunner.py.
TEST_ON_BRANCH = os.environ.get("LAKEBASE") == "1"
if TEST_ON_BRANCH:
    DATABASES["default"]["TEST"] = {"NAME": DATABASES["default"]["NAME"]}  # "the test database IS the branch"

TEST_RUNNER = "snakekee.testrunner.BranchAwareTestRunner"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Hong_Kong"
USE_I18N = False
USE_TZ = True

STATIC_URL = "/static/"
WHITENOISE_ROOT = BASE_DIR / "frontend" / "dist"  # serves the built React app: /assets/*, /menu/*.svg, /logo.svg

LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.db.backends": {"level": os.environ.get("SQL_LOG_LEVEL", "INFO")},
        "databricks": {"level": "WARNING"},
    },
}
