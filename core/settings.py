from pathlib import Path
import os
from datetime import timedelta

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

    'apps.accounts.apps.AccountsConfig',
    'apps.wallets',
    'apps.earnings',
    'apps.referrals',
    'apps.withdrawals',
    'apps.marketplace',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
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

CORS_ALLOW_ALL_ORIGINS = True

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
    'WITHDRAW_TAX': float(os.environ.get('WITHDRAW_TAX', '0.10')),
    'GLOBAL_POOL_CUT': float(os.environ.get('GLOBAL_POOL_CUT', '0.10')), # optional applied before referral
    # Referral tiers default (after gates): L1=5%, L2=3%, L3=2%. Can be overridden via env: 0.05,0.03,0.02
    'REFERRAL_TIERS': [float(x) for x in os.environ.get('REFERRAL_TIERS', '0.05,0.03,0.02').split(',')],
    # USD->PKR
    'FX_SOURCE': 'ADMIN_RATE',
}

# Admin settable rate fallback
ADMIN_USD_TO_PKR = float(os.environ.get('ADMIN_USD_TO_PKR', '280.0'))

# Admin bank details for manual payments (shown at checkout)
ADMIN_BANK_NAME = os.environ.get('ADMIN_BANK_NAME', '')
ADMIN_ACCOUNT_NAME = os.environ.get('ADMIN_ACCOUNT_NAME', '')
ADMIN_ACCOUNT_ID = os.environ.get('ADMIN_ACCOUNT_ID', '')