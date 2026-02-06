from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta
import firebase_admin
from firebase_admin import credentials
from django.contrib.messages import constants as messages
from celery.schedules import crontab

if not firebase_admin._apps:
    cred = credentials.Certificate(r"firebase_config.json")
    firebase_admin.initialize_app(cred)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = True

# ALLOWED_HOSTS = ['18.117.142.132', 'localhost', '127.0.0.1']
ALLOWED_HOSTS = ["*"]

DJANGO_APPS = [
    "daphne",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_user_agents',
    "django.contrib.sites",

]

THIRD_PARTY_PACKAGES = [
    "rest_framework",
    "import_export",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    "drf_yasg",
    "ckeditor",
    "ckeditor_uploader",
    "django_celery_results",
    "django_celery_beat",
    'django_cleanup.apps.CleanupConfig',
]

CUSTOM_APPS = [
    'common',
    'users',
    'players',
    'fans',
    'coach',
    "evaluator",
    "dashboard",
    "notification",
    "chatapp",
    "event"
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_PACKAGES + CUSTOM_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
    "middleware.SelectiveUserAgentMiddleware",
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR, "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            "libraries": {
                "event_filters": "event.core.templatetags.event_filter",
                "player_filters": "players.core.templatetags.badge_filter",
                "user_filters": "users.templatetags.verification_tags",
            }
        },
    },
]

# WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # },
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DBNAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'
# TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True
USE_TZ = False

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# MEDIA_ROOT = '/home/ubuntu/AthleteRated/media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

# SMTP

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')

# cache

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        # "LOCATION": "redis://192.168.10.186:6379",
        "LOCATION": "redis://127.0.0.1:6379",
        # "LOCATION": "redis://default:q7ZnRqTtJeV6KojsaIvZGH05AHj6paEl@redis-12397.c8.us-east-1-2.ec2.redns.redis-cloud.com:12397",
    }
}

# Rest Framework

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DATETIME_FORMAT': "%d-%b,%Y, %I:%M %p",
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 30,

    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'MAX_CONTENT_LENGTH': 250 * 1024 * 1024,

}

# JWT

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60 * 9),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=3),
    'SLIDING_TOKEN_LIFETIME': timedelta(days=30),
    'SLIDING_TOKEN_REFRESH_LIFETIME_LATE_USER': timedelta(days=1),
    'SLIDING_TOKEN_LIFETIME_LATE_USER': timedelta(days=30),
}

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "https://youthbasketball.csdevhub.com"
]

USER_AGENTS_CACHE = 'default'

# Celery Configuration
# CELERY_TIMEZONE = 'Asia/Kolkata'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_URL = "redis://localhost:6379/1"
# CELERY_BROKER_URL = "redis://192.168.10.186:6379"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# CK Editor
CKEDITOR_UPLOAD_PATH = "uploads/"
SILENCED_SYSTEM_CHECKS = ["ckeditor.W001"]

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline', 'strikethrough', 'code', 'subscript', 'superscript', 'highlight',
             'codeBlock', 'sourceEditing', 'insertImage', 'numberedList', 'bulletedList', 'todoList'],
            ['NumberedList', 'BulletedList', '-',
             'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['RemoveFormat', 'Source', 'insertTable', 'fontColor', 'fontFamily', 'fontSize', 'fontBackgroundColor',
             'mediaEmbed', 'removeFormat', 'insertTable']
        ],
    },

}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "JWT Authorization header using the Bearer scheme. Example: 'Bearer <token>'",
        },
    },
    'USE_SESSION_AUTH': False,
}

# Cors Headers
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "https://youthbasketball.csdevhub.com"
]

# Admin
LOGIN_URL = "/login/"

MESSAGE_TAGS = {
    messages.ERROR: "danger"
}

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DATA_UPLOAD_MAX_MEMORY_SIZE = 250 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 250 * 1024 * 1024

DJANGO_CLEANUP = {
    "FETCH_DELETE_ENABLED": True,
    "DELETE_UNUSED_FILES": True,
}

if os.getenv("GITHUB_ACTIONS"):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

SITE_ID = 1

PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
PAYPAL_ENVIRONMENT = os.getenv("PAYPAL_ENVIRONMENT")
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com" if PAYPAL_ENVIRONMENT == "sandbox" else "https://api-m.paypal.com"
PAYPAL_WEBHOOK_ID = os.getenv("PAYPAL_WEBHOOK_ID")

APPEND_SLASH = True


# SECURE_SSL_REDIRECT = True
# USE_X_FORWARDED_HOST = True

