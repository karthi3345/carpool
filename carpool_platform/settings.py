import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, True),
    DB_FALLBACK_SQLITE=(bool, True),
    REDIS_URL=(str, 'redis://127.0.0.1:6379/0'),
    CELERY_BROKER_URL=(str, 'redis://127.0.0.1:6379/0'),
    CELERY_RESULT_BACKEND=(str, 'redis://127.0.0.1:6379/0'),
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-carpool-india-platform-yellow-white-secret')
DEBUG = env('DEBUG', default=False)
ALLOWED_HOSTS = ['*']

# Application definition
DJANGO_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'channels',
    'cloudinary_storage',
    'cloudinary',
    'rest_framework',
    'django_celery_results',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.profiles',
    'apps.vehicles',
    'apps.locations',
    'apps.rides',
    'apps.bookings',
    'apps.payments',
    'apps.messaging',
    'apps.notifications',
    'apps.reviews',
    'apps.favourites',
    'apps.support',
    'apps.analytics',
    'apps.community',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'carpool_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'carpool_platform.wsgi.application'

# Database Configuration with PostgreSQL (via DATABASE_URL or POSTGRES_URL) and fallback
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Vercel / Production Postgres: Check if DATABASE_URL or POSTGRES_URL is set
database_url = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL') or os.getenv('POSTGRES_PRISMA_URL')
# If DATABASE_URL is not localhost dummy, configure PostgreSQL
if database_url and not ('localhost' in database_url and 'postgres:postgres' in database_url):
    try:
        import dj_database_url
        DATABASES['default'] = dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True if any(host in database_url for host in ['vercel', 'supabase', 'neon', 'aws', 'pooler']) else False
        )
    except Exception:
        pass


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-in'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False

# Media files & Cloudinary Storage
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

CLOUDINARY_CLOUD_NAME = env('CLOUDINARY_CLOUD_NAME', default='wtxe3ffw')
CLOUDINARY_API_KEY = env('CLOUDINARY_API_KEY', default='754469489494381')
CLOUDINARY_API_SECRET = env('CLOUDINARY_API_SECRET', default='fx978eIsL4nL0tKG4e4WXGLHxEY')

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
        'API_KEY': CLOUDINARY_API_KEY,
        'API_SECRET': CLOUDINARY_API_SECRET,
    }
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ASGI Application for Django Channels
ASGI_APPLICATION = 'carpool_platform.asgi.application'

# Channel Layer Configuration (Redis if available, with in-memory fallback for local/serverless)
REDIS_URL = env('REDIS_URL', default=env('CELERY_BROKER_URL', default=''))
if REDIS_URL and ('redis://' in REDIS_URL or 'rediss://' in REDIS_URL):
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [REDIS_URL],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 15,
}

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Redis Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-carpool-cache',
    }
}

# Theme Configuration - Yellow and White Color Combination
CARPOOL_THEME = {
    'PRIMARY_YELLOW': '#FFD000',
    'ACCENT_YELLOW': '#FDB813',
    'LIGHT_YELLOW': '#FFFBEA',
    'DARK_ACCENT': '#181C20',
    'PURE_WHITE': '#FFFFFF',
    'TEXT_MAIN': '#1E293B',
    'TEXT_MUTED': '#64748B',
    'BORDER_COLOR': '#E2E8F0',
}
