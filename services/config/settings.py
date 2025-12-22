from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import config

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-key-change-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "corsheaders",
    "drf_yasg",
    # Celery
    "django_celery_results",
    "django_celery_beat",
    # Local apps
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    "default": dj_database_url.config(default=config("DATABASE_URL", default="sqlite:///db.sqlite3"), conn_max_age=600)
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User Model
AUTH_USER_MODEL = "api.User"

# REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
}

# JWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS settings
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:5173,http://127.0.0.1:5173").split(",")
CORS_ALLOW_CREDENTIALS = True

# Gemini AI settings
GEMINI_API_KEY = config("GEMINI_API_KEY", default="")


# PRODUCTION INFRASTRUCTURE SETTINGS


# Redis Cache Configuration
# Used for: Translation cache, RAG query cache, session storage
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/1")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "medical_translation",
        "TIMEOUT": 300,  # 5 minutes default
    }
}

# Cache timeouts for different data types
CACHE_TIMEOUTS = {
    "translation": 3600,  # 1 hour for translations
    "rag_query": 1800,  # 30 minutes for RAG results
    "user_session": 86400,  # 24 hours for sessions
    "cultural_tips": 86400,  # 24 hours for cultural tips
}


# Celery Configuration

# Used for: Background tasks (audio transcription, RAG processing, etc.)

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")

# Serialization
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# Timezone
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True

# Task settings
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max per task
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # Soft limit at 25 minutes

# Task routing - different queues for different task types
CELERY_TASK_ROUTES = {
    "api.tasks.audio_tasks.*": {"queue": "audio"},
    "api.tasks.translation_tasks.*": {"queue": "translation"},
    "api.tasks.rag_tasks.*": {"queue": "rag"},
    "api.tasks.assistance_tasks.*": {"queue": "assistance"},
    "api.tasks.cleanup_tasks.*": {"queue": "maintenance"},
}

# Default queue
CELERY_TASK_DEFAULT_QUEUE = "default"

# Retry settings
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Beat schedule for periodic tasks
CELERY_BEAT_SCHEDULE = {
    "cleanup-old-audio-daily": {
        "task": "api.tasks.cleanup_tasks.cleanup_old_audio_files",
        "schedule": 86400.0,  # Daily
        "args": (30,),  # Delete files older than 30 days
    },
    "cleanup-orphaned-files-weekly": {
        "task": "api.tasks.cleanup_tasks.cleanup_orphaned_files",
        "schedule": 604800.0,  # Weekly
    },
    "database-maintenance-daily": {
        "task": "api.tasks.cleanup_tasks.database_maintenance",
        "schedule": 86400.0,  # Daily
    },
    "generate-usage-report-daily": {
        "task": "api.tasks.cleanup_tasks.generate_usage_report",
        "schedule": 86400.0,  # Daily
    },
}


# RabbitMQ Event Bus Configuration

# Used for: Event-driven communication between services

RABBITMQ_URL = config("RABBITMQ_URL", default="amqp://guest:guest@localhost:5672/")
RABBITMQ_EXCHANGE = "medical_translation_events"

# Message Bus Configuration (used by BusRegistry)
MESSAGE_BUS_CONFIG = {
    "backend": "rabbitmq",
    "rabbitmq": {
        "url": RABBITMQ_URL,
        "exchange_name": RABBITMQ_EXCHANGE,
        "impl": "threaded",
        "kwargs": {"heartbeat": 60, "prefetch_count": 1},
    },
}


# Ollama Configuration (Open Source AI)

# Used for: Local AI models (translation, embeddings, transcription)

AI_PROVIDER = config("AI_PROVIDER", default="gemini")  # gemini, ollama
OLLAMA_BASE_URL = config("OLLAMA_BASE_URL", default="http://localhost:11434")
OLLAMA_TRANSLATION_MODEL = config("OLLAMA_TRANSLATION_MODEL", default="granite:latest")
OLLAMA_EMBEDDING_MODEL = config("OLLAMA_EMBEDDING_MODEL", default="nomic-embed-text:latest")


# Logging Configuration


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "api": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
