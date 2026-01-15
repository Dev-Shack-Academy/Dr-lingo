# Logging setup
import logging
from pathlib import Path

import dj_database_url
from decouple import config

logger = logging.getLogger(__name__)

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
    # WebSocket Support
    "channels",
    # Celery
    "django_celery_results",
    "django_celery_beat",
    # Two-Factor Authentication
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_email",
    "django_otp.plugins.otp_static",
    "two_factor",
    "two_factor.plugins.email",
    # Local apps
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Add whitenoise right after SecurityMiddleware
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # OTP Middleware - must be after AuthenticationMiddleware
    "django_otp.middleware.OTPMiddleware",
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
ASGI_APPLICATION = "config.asgi.application"

# Database
# Supports both DATABASE_URL and individual POSTGRES_* env vars
# Cloud SQL uses Unix socket: POSTGRES_HOST=/cloudsql/project:region:instance
POSTGRES_HOST = config("POSTGRES_HOST", default="")

if POSTGRES_HOST.startswith("/cloudsql/"):
    # Cloud SQL Unix socket connection
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("POSTGRES_DB", default="dr_lingo_db"),
            "USER": config("POSTGRES_USER", default="dr_lingo_user"),
            "PASSWORD": config("POSTGRES_PASSWORD", default=""),
            "HOST": POSTGRES_HOST,  # Unix socket path
            "PORT": "",  # Empty for Unix socket
            "CONN_MAX_AGE": 600,
            "CONN_HEALTH_CHECKS": True,
        }
    }
else:
    # Standard DATABASE_URL (docker-compose, Heroku, etc.)
    DATABASES = {
        "default": dj_database_url.config(
            default=config("DATABASE_URL", default="sqlite:///db.sqlite3"),
            conn_max_age=600,
            conn_health_checks=True,
        )
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

# Media files configuration
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Google Cloud Storage configuration for production
USE_GCS = config("USE_GCS", default=False, cast=bool)
GCS_BUCKET_NAME = config("GCS_BUCKET_NAME", default="")

if USE_GCS and GCS_BUCKET_NAME:
    # Use Google Cloud Storage for media files in production
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "OPTIONS": {
                "bucket_name": GCS_BUCKET_NAME,
                "location": "media",  # Prefix for media files
                "default_acl": "publicRead",  # Make files publicly readable
                "file_overwrite": False,  # Don't overwrite files with same name
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    # Update MEDIA_URL to use GCS
    MEDIA_URL = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/media/"
    logger.info(f"Using Google Cloud Storage bucket: {GCS_BUCKET_NAME}")
else:
    # Local filesystem storage (development)
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    logger.info("Using local filesystem storage for media files")

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
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.auth.OTPSessionAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}

# CORS settings
if DEBUG:
    # Development: allow any localhost
    CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:5173,http://127.0.0.1:5173").split(
        ","
    )
else:
    # Production: only allow specific domains
    CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="").split(",")
    # Filter out empty strings
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS if origin.strip()]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# Session settings (for cookie-based auth)
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 86400 * 7  # 7 days
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS only in production
# SameSite=None required for cross-origin authentication (frontend on different domain)
SESSION_COOKIE_SAMESITE = "None" if not DEBUG else "Lax"  # None required for cross-origin
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "None" if not DEBUG else "Lax"  # None required for cross-origin

# CSRF trusted origins
if DEBUG:
    CSRF_TRUSTED_ORIGINS = config(
        "CSRF_TRUSTED_ORIGINS", default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    ).split(",")
else:
    CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="").split(",")
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in CSRF_TRUSTED_ORIGINS if origin.strip()]

# Cloud Run Service Prefix (for WebSocket origin validation)
# Only Cloud Run services with this prefix will be allowed to connect via WebSocket
# Pattern: {prefix}-{service}-{hash}-{region}.a.run.app
CLOUD_RUN_SERVICE_PREFIX = config("CLOUD_RUN_SERVICE_PREFIX", default="dr-lingo")

# Two-Factor Authentication Settings
LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "two_factor:login"

# OTP Settings
OTP_EMAIL_SENDER = config("OTP_EMAIL_SENDER", default="noreply@dr-lingo.local")
OTP_EMAIL_SUBJECT = "Dr-Lingo Verification Code"
TWO_FACTOR_PATCH_ADMIN = False  # Disable 2FA for Django admin - use regular admin login

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


# Django Channels Configuration

# Used for: WebSocket connections, real-time chat updates

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config("REDIS_CHANNELS_URL", default="redis://localhost:6379/2")],  # Use DB 2 for channels
            "prefix": "dr_lingo_channels",
            "expiry": 60,  # Channel expiry in seconds
        },
    },
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
    "api.tasks.tts_tasks.*": {"queue": "audio"},  # TTS uses audio queue
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

# RabbitMQ Configuration (for docker-compose/local)
RABBITMQ_URL = config("RABBITMQ_URL", default="amqp://guest:guest@localhost:5672/")
RABBITMQ_EXCHANGE = config("RABBITMQ_EXCHANGE", default="medical_translation_events")

# Cloud Pub/Sub Configuration (for Cloud Run)
USE_PUBSUB = config("USE_PUBSUB", default=False, cast=bool)
PUBSUB_PROJECT_ID = config("PUBSUB_PROJECT_ID", default="")
PUBSUB_TOPIC = config("PUBSUB_TOPIC", default="dr-lingo-events")
PUBSUB_SUBSCRIPTION = config("PUBSUB_SUBSCRIPTION", default="dr-lingo-events-sub")

# Message Bus Configuration (used by BusRegistry)
# If USE_PUBSUB is True, events are published to Pub/Sub instead of RabbitMQ
if USE_PUBSUB:
    # Pub/Sub mode - events handled by consume_events management command
    MESSAGE_BUS_CONFIG = None
else:
    # RabbitMQ mode - events handled by BusRegistry
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

AI_PROVIDER = config("AI_PROVIDER", default="ollama")  # gemini, ollama
OLLAMA_BASE_URL = config("OLLAMA_BASE_URL", default="http://localhost:11434")
OLLAMA_TRANSLATION_MODEL = config("OLLAMA_TRANSLATION_MODEL", default="granite:latest")
OLLAMA_COMPLETION_MODEL = config("OLLAMA_COMPLETION_MODEL", default="granite3.3:8b")
OLLAMA_EMBEDDING_MODEL = config("OLLAMA_EMBEDDING_MODEL", default="nomic-embed-text:v1.5")


# Whisper Speech-to-Text Configuration

# Used for: Audio transcription via Whisper.cpp service
WHISPER_API_URL = config("WHISPER_API_URL", default="http://localhost:9000")


# Hugging Face Configuration

# Used for: Importing South African language datasets into RAG knowledge bases
# Get your token from: https://huggingface.co/settings/tokens
#
# IMPORTANT: The za-african-next-voices dataset is GATED!
# You must request access at: https://huggingface.co/datasets/dsfsi-anv/za-african-next-voices
# before the import will work.

HF_TOKEN = config("HF_TOKEN", default="")


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
            "format": "[{levelname}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
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
            "propagate": True,
        },
        "celery.task": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "celery.worker": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
