# """
# Django settings for mysite project.
# """

# from pathlib import Path
# from datetime import timedelta
# from decouple import config


# BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY = 'django-insecure-rj(yt$_wdhsv&kg7l#-*6f!8f1!4g3l4qubem&&%8-l-evz%az'

# DEBUG = True

# ALLOWED_HOSTS = ['*']


# # ── Installed Apps ────────────────────────────────────────────────────────────

# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',

#     'corsheaders',
#     'rest_framework',
#     'rest_framework_simplejwt',
#     # ← token_blacklist removed: we don't use blacklisting (causes OutstandingToken clash)
#     'app',
#     'rest_framework.authtoken',
# ]

# MIDDLEWARE = [
#     'corsheaders.middleware.CorsMiddleware',          # must be first
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# EMAIL_BACKEND: str = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST: str = "smtp.gmail.com"
# EMAIL_PORT: int = 587
# EMAIL_USE_TLS: bool = True

# EMAIL_HOST_USER: str = "veereshbashetti121@gmail.com"
# EMAIL_HOST_PASSWORD: str = "jhda mhyj svxb egqz"  # NOT normal password

# DEFAULT_FROM_EMAIL: str = EMAIL_HOST_USER

# # Optional
# SITE_URL: str = "http://127.0.0.1:5173"
# ADMIN_NOTIFY_EMAIL: str = EMAIL_HOST_USER


# ROOT_URLCONF = 'mysite.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'mysite.wsgi.application'


# # ── Database ──────────────────────────────────────────────────────────────────

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'sapthapadi_db',
#         'USER': 'root',
#         'PASSWORD': 'Root@123',
#         'HOST': '127.0.0.1',
#         'PORT': '3306',
#     }
# }

# # Member is the site's AUTH_USER_MODEL (for public login)
# # AdminUser is a SEPARATE model with its own JWT — not AUTH_USER_MODEL
# AUTH_USER_MODEL = 'app.Member'


# # ── Password Validation ───────────────────────────────────────────────────────

# AUTH_PASSWORD_VALIDATORS = [
#     {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
# ]


# # ── Internationalisation ──────────────────────────────────────────────────────

# LANGUAGE_CODE = 'en-us'
# TIME_ZONE     = 'UTC'
# USE_I18N      = True
# USE_TZ        = True


# # ── Static & Media ────────────────────────────────────────────────────────────

# STATIC_URL  = 'static/'
# STATIC_ROOT = BASE_DIR / 'staticfiles'

# MEDIA_URL  = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'


# # ── CORS ──────────────────────────────────────────────────────────────────────
# CORS_ALLOWED_ORIGINS = [
#     'http://localhost:5173',
#     'http://127.0.0.1:5173',
#     'http://10.18.33.75:5173',
#     'http://10.133.190.75:5173',
#     'http://10.48.140.75:5173'
# ]

# ALLOWED_HOSTS = ['localhost', '127.0.0.1', '10.18.33.75', '10.133.190.75', '10.48.140.75']

# CORS_ALLOW_CREDENTIALS = True

# CORS_ALLOW_HEADERS = [
#     'accept',
#     'authorization',
#     'content-type',
#     'origin',
#     'x-csrftoken',
#     'x-requested-with',
# ]

# CORS_ALLOW_METHODS = [
#     'DELETE',
#     'GET',
#     'OPTIONS',
#     'PATCH',
#     'POST',
#     'PUT',
# ]


# # ── Django REST Framework ─────────────────────────────────────────────────────

# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#         'rest_framework.authentication.TokenAuthentication',  # 🔥 ONLY THIS
#     ],
#     'DEFAULT_PERMISSION_CLASSES': [
#         'rest_framework.permissions.IsAuthenticated',
#     ],
# }

# FRONTEND_URL = 'http://localhost:5173'


# # ── Simple JWT ────────────────────────────────────────────────────────────────

# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME':    timedelta(minutes=3650),
#     'REFRESH_TOKEN_LIFETIME':   timedelta(days=3650),
#     'ROTATE_REFRESH_TOKENS':    False,
#     'BLACKLIST_AFTER_ROTATION': False,
#     'UPDATE_LAST_LOGIN':        False,   # must be False — AdminUser ≠ AUTH_USER_MODEL
#     'ALGORITHM':                'HS256',
#     'SIGNING_KEY':              SECRET_KEY,
#     'AUTH_HEADER_TYPES':        ('Bearer',),
# }


# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'






from pathlib import Path
from datetime import timedelta
import os
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ── SECURITY ─────────────────────────────────────────────

SECRET_KEY = config("SECRET_KEY")
DEBUG = False

ALLOWED_HOSTS = [
    config("RENDER_EXTERNAL_HOSTNAME", default="localhost")
]

# ── INSTALLED APPS ──────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework.authtoken',

    'cloudinary',
    'cloudinary_storage',

    'app',
]

# ── MIDDLEWARE ──────────────────────────────────────────

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ── EMAIL ───────────────────────────────────────────────

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = config("EMAIL_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_PASS")

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ── URLS ────────────────────────────────────────────────

ROOT_URLCONF = 'mysite.urls'
WSGI_APPLICATION = 'mysite.wsgi.application'

# ── DATABASE (REPLACED MYSQL → POSTGRES) ───────────────

DATABASES = {
    "default": dj_database_url.parse(config("DATABASE_URL"))
}

# ── AUTH USER MODEL ────────────────────────────────────

AUTH_USER_MODEL = 'app.Member'

# ── PASSWORD VALIDATION ────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── INTERNATIONALIZATION ───────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── STATIC FILES ───────────────────────────────────────

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── MEDIA (CLOUDINARY INSTEAD OF LOCAL) ────────────────

import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config(
    cloud_name=config("CLOUD_NAME"),
    api_key=config("API_KEY"),
    api_secret=config("API_SECRET"),
)

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ── CORS ───────────────────────────────────────────────

CORS_ALLOW_ALL_ORIGINS = True  # tighten after frontend deploy
CORS_ALLOW_CREDENTIALS = True

# ── REST FRAMEWORK ─────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# ── JWT ────────────────────────────────────────────────

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=3650),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=3650),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ── SECURITY HARDENING ─────────────────────────────────

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ── DEFAULT FIELD ──────────────────────────────────────

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'