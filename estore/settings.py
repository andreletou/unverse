from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$(0=*8=!$i(@qx#_gjk=16#(7f-)-44y#11_ep#e$x3apc5cr_'

DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    
    # Third-party apps
    'django_countries',
    'crispy_forms',
    'crispy_bootstrap5',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'import_export',
    'rangefilter',
    'admin_auto_filters',
    
    # Local apps
    'universepro',
    # 'users',
]
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Pour l'internationalisation
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware'
]

ROOT_URLCONF = 'estore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'universepro/templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # Custom context processors
                'universepro.context_processors.cart_context',
                'universepro.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'estore.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

import dj_database_url
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

if os.environ.get('RENDER'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }




# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'Africa/Lome'

USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('fr', _('French')),
    ('en', _('English')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
# AUTH_USER_MODEL = 'users.CustomUser'
# LOGIN_REDIRECT_URL = '/'
# LOGOUT_REDIRECT_URL = '/'
# LOGIN_URL = '/account/login/'

# Email configuration (pour développement)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Pour production:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.yourdomain.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'contact@yourdomain.com'
# EMAIL_HOST_PASSWORD = 'yourpassword'
DEFAULT_FROM_EMAIL = 'contact@universepro.com'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Django-allauth configuration
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
# Configuration de allauth
SITE_ID = 1  # Correspond à votre site dans la table django_site
LOGIN_REDIRECT_URL = '/'  # Redirection après connexion
ACCOUNT_LOGOUT_REDIRECT_URL = '/'  # Redirection après déconnexion
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'  # Permet de se connecter via email ou username
ACCOUNT_EMAIL_REQUIRED = True  # Email obligatoire
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # Vérification email obligatoire
ACCOUNT_SESSION_REMEMBER = True  # Se souvenir de la session
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True  # Confirmation du mot de passe
ACCOUNT_UNIQUE_EMAIL = True  # Email unique

# PayGateGlobal Configuration
PAYGATE_API_KEY = "cce29fe6-8aa7-419b-9020-4815d6b8fc85"
PAYGATE_PAY_URL = "https://paygateglobal.com/api/v1/pay"
PAYGATE_STATUS_URL = "https://paygateglobal.com/api/v1/status"
PAYGATE_CALLBACK_URL = "https://universepro.com/paygate/callback/"  # À configurer dans votre DNS

WHATSAPP_ENABLED = True
WHATSAPP_SUPPORT_NUMBER = '22893020525'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'first_name',
            'last_name',
            'email',
            'name',
            'verified',
        ],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
    }
}

# Configuration de crispy forms
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# E-commerce specific settings
FREE_SHIPPING_THRESHOLD = 100000  # 100,000 FCFA
DEFAULT_SHIPPING_COST = 5000  # 5,000 FCFA
CART_SESSION_ID = 'cart'
WHATSAPP_ENABLED = True
WHATSAPP_PHONE = '+22893020525'
WHATSAPP_MESSAGE = "Bonjour, j'ai une question sur votre boutique en ligne."

# Security settings (à ajuster pour la production)
SESSION_COOKIE_SECURE = False  # True en production avec HTTPS
CSRF_COOKIE_SECURE = False    # True en production avec HTTPS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
