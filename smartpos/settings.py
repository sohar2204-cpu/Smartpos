import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

# ── Security ───────────────────────────────────────────────────────────────────
# FIX SEC-01: No hardcoded fallback secret key. App will refuse to start without one.
_secret = os.environ.get('SECRET_KEY', '')
if not _secret:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(50))\""
    )
SECRET_KEY = _secret

# FIX SEC-02: DEBUG must be explicitly set to 'True' — defaults to False (safe).
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# FIX SEC-03: No wildcard ALLOWED_HOSTS. Must be explicitly configured.
_hosts = os.environ.get('ALLOWED_HOSTS', '')
if not _hosts and not DEBUG:
    raise RuntimeError(
        "ALLOWED_HOSTS environment variable must be set in production. "
        "Example: ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com"
    )
ALLOWED_HOSTS = [h.strip() for h in _hosts.split(',') if h.strip()] if _hosts else ['localhost', '127.0.0.1']

# ── Site URL ───────────────────────────────────────────────────────────────────
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')

# ── Installed apps ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pos',
    'dbbackup',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'pos.middleware.StoreScopeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smartpos.urls'

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

WSGI_APPLICATION = 'smartpos.wsgi.application'

# ── Database ───────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
elif os.environ.get('DB_ENGINE') == 'postgresql' or os.environ.get('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'smartpos'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'smartpos.db',
        }
    }

# ── Password validation ────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalisation ───────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = os.environ.get('TIME_ZONE', 'Asia/Karachi')
USE_I18N      = True
USE_TZ        = True

# ── Static & Media ─────────────────────────────────────────────────────────────
STATIC_URL    = '/static/'
STATIC_ROOT   = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Auth redirects ─────────────────────────────────────────────────────────────
LOGIN_URL          = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL= '/login/'

LOW_STOCK_THRESHOLD = 10

# ── Session Security ───────────────────────────────────────────────────────────
# FIX SEC-09: Session hardening
SESSION_COOKIE_HTTPONLY        = True          # JS cannot read session cookie
SESSION_COOKIE_SAMESITE        = 'Lax'         # CSRF protection for cookies
SESSION_EXPIRE_AT_BROWSER_CLOSE = True          # Session dies when browser closes
SESSION_COOKIE_AGE             = 8 * 60 * 60   # 8-hour absolute max

# CSRF cookie — HttpOnly MUST be False so JavaScript can read the csrftoken
# cookie and send it in the X-CSRFToken header for AJAX requests (fetch/XHR).
# Setting it True breaks all JSON POST endpoints (checkout, etc.) with 403.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

# FIX SEC-10: Login rate limiting (requires django-axes or handled in view)
# Max failed login attempts tracked via AXES (add to INSTALLED_APPS if using django-axes)
# LOGIN_ATTEMPTS_LIMIT = 5

# ── Email ──────────────────────────────────────────────────────────────────────
EMAIL_BACKEND       = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST          = os.environ.get('EMAIL_HOST',          'smtp.gmail.com')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT',      '587'))
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS',       'True') == 'True'
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER',     '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    f'SmartPOS <{EMAIL_HOST_USER}>'
)

# ── File Upload Security ───────────────────────────────────────────────────────
# FIX SEC-11: Limit upload sizes
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB max POST body
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB max file upload

# ── Production Security ────────────────────────────────────────────────────────
# FIX SEC-04/05/06/07/08: Comprehensive security headers
if not DEBUG:
    SECURE_PROXY_SSL_HEADER         = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE           = True
    CSRF_COOKIE_SECURE              = True
    SECURE_BROWSER_XSS_FILTER       = True
    X_FRAME_OPTIONS                 = 'DENY'
    SECURE_CONTENT_TYPE_NOSNIFF     = True           # FIX: Prevent MIME sniffing
    SECURE_HSTS_SECONDS             = 31536000        # FIX: 1 year HSTS
    SECURE_HSTS_INCLUDE_SUBDOMAINS  = True
    SECURE_HSTS_PRELOAD             = True
    SECURE_REFERRER_POLICY          = 'strict-origin-when-cross-origin'
else:
    # Dev-only: still set frame options and nosniff
    X_FRAME_OPTIONS             = 'SAMEORIGIN'
    SECURE_CONTENT_TYPE_NOSNIFF = True

# ── Logging ────────────────────────────────────────────────────────────────────
# FIX SEC-13: Structured security logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 10 * 1024 * 1024,   # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pos.security': {
            'handlers': ['console', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}

# Ensure log directory exists
import os as _os
_log_dir = BASE_DIR / 'logs'
_log_dir.mkdir(exist_ok=True)