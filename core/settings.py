from pathlib import Path
import os
from datetime import timedelta
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key')
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_crontab',

    'apps.accounts.apps.AccountsConfig',
    'apps.wallets',
    'apps.earnings',
    'apps.referrals',
    'apps.withdrawals',
    'apps.marketplace',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'core.middleware.DBRetryMiddleware',  # Handle Neon DB sleep mode
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Database: use Postgres via DATABASE_URL if provided, else fallback to local SQLite for dev
_DB_URL = os.environ.get('DATABASE_URL')
if _DB_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            _DB_URL,
            conn_max_age=600,
            ssl_require=True,  # Neon requires SSL
        )
    }
    # Enable atomic requests to prevent idle transaction timeouts
    DATABASES['default']['ATOMIC_REQUESTS'] = True
    # Add SSL mode for Neon free tier stability
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (uploads)
MEDIA_URL = '/media/'
# Allow overriding media root via environment for platforms like Render where a persistent disk is mounted
MEDIA_ROOT = Path(os.environ.get('DJANGO_MEDIA_ROOT', str(BASE_DIR / 'media')))

# Enable compressed, cache-busted static files via WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://adminui-oe7i.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.100.141:3000",  # Network IP for admin UI
    "http://192.168.100.141:8000",  # Network IP for backend
]

# Additional CORS headers for preflight requests
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

AUTH_USER_MODEL = 'accounts.User'

# Platform economics defaults
ECONOMICS = {
    # Mode: UNCHANGED (90-day plan) or CYCLIC_130 (1%..3.5% then 4% for 100 days, repeat)
    'PASSIVE_MODE': os.environ.get('PASSIVE_MODE', 'UNCHANGED'),
    # Passive income (unchanged plan)
    'PASSIVE_SCHEDULE': [
        # (start_day, end_day, daily_percent)
        (1, 10, 0.004),   # 0.4%
        (11, 20, 0.006),  # 0.6%
        (21, 30, 0.008),  # 0.8%
        (31, 60, 0.010),  # 1.0%
        (61, 90, 0.013),  # 1.3%
    ],
    # Cyclic 130-day plan definition
    'PASSIVE_SCHEDULE_CYCLIC_130': [
        (1, 5, 0.010),   # 1%
        (6, 10, 0.015),  # 1.5%
        (11, 15, 0.020), # 2%
        (16, 20, 0.025), # 2.5%
        (21, 25, 0.030), # 3%
        (26, 30, 0.035), # 3.5%
        (31, 130, 0.040) # 4% for next 100 days
    ],
    'USER_WALLET_SHARE': float(os.environ.get('USER_WALLET_SHARE', '0.80')),
    'WITHDRAW_TAX': float(os.environ.get('WITHDRAW_TAX', '0.20')),  # 20% withdraw tax
    'GLOBAL_POOL_CUT': float(os.environ.get('GLOBAL_POOL_CUT', '0.10')), # optional applied before referral
    # Referral tiers default (after gates): L1=6%, L2=3%, L3=1%. Can be overridden via env: 0.06,0.03,0.01
    'REFERRAL_TIERS': [float(x) for x in os.environ.get('REFERRAL_TIERS', '0.06,0.03,0.01').split(',')],
    # Milestone payout percents per target, e.g. "10:0.05,30:0.10" (optional)
    'MILESTONE_PCTS': os.environ.get('MILESTONE_PCTS', ''),
    # USD->PKR
    'FX_SOURCE': 'ADMIN_RATE',
}

# Admin settable rate fallback
ADMIN_USD_TO_PKR = float(os.environ.get('ADMIN_USD_TO_PKR', '280.0'))
# Signup payment base in PKR
SIGNUP_FEE_PKR = float(os.environ.get('SIGNUP_FEE_PKR', '1410'))

# Cron jobs for automated tasks
CRONJOBS = [
    # Daily earnings generation (every day at 00:01 UTC)
    ('1 0 * * *', 'django.core.management.call_command', ['run_daily_earnings']),
    # Weekly global pool distribution (every Monday at 00:00 UTC)
    ('0 0 * * 1', 'django.core.management.call_command', ['distribute_global_pool']),
]

# Admin bank details for manual payments (shown at checkout)
ADMIN_BANK_NAME = os.environ.get('ADMIN_BANK_NAME', '')
ADMIN_ACCOUNT_NAME = os.environ.get('ADMIN_ACCOUNT_NAME', '')
ADMIN_ACCOUNT_ID = os.environ.get('ADMIN_ACCOUNT_ID', '')

# Logging configuration for debugging database issues
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING' if not DEBUG else 'DEBUG',
            'propagate': False,
        },
        'core.middleware': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}