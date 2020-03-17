import os
import datetime


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '9g+*-ze7p(l6m1#hq$0ya#xxc-f180rk0!g-8bfq9+gykg($7&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'aries_api',
    'aries_community',
]

ARIES_CONFIG = {
    'storage_config': {'url': 'localhost:5432'},
    'storage_credentials': {'account': 'postgres', 'password': 'mysecretpassword', 'admin_account': 'postgres', 'admin_password': 'mysecretpassword'},
    'register_dids': True,
    'ledger_url': 'http://localhost:9000',
    'genesis_url': 'http://localhost:9000/genesis',
    'default_enterprise_seed': 'aries_community_enterprise_00000',
    'default_institution_seed': 'aries_community_institution_0000',
    'managed_agent_host': 'localhost',
    'webhook_host': 'localhost',
    'webhook_port': '8000',
    'webhook_root': '',
    'aca_py_bin_path': '../venv/bin/',
}

ARIES_PROFILE_VIEW = 'aries_community.views.profile_view'
ARIES_DATA_VIEW = 'aries_community.views.data_view'
ARIES_WALLET_VIEW = 'aries_community.views.wallet_view'

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aries_community_demo.urls'

#SESSION_COOKIE_AGE = 1800

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

WSGI_APPLICATION = 'aries_community_demo.wsgi.application'

AUTH_USER_MODEL = 'aries_community.AriesUser'

# override to create app-specific models during data loading
ARIES_ORGANIZATION_MODEL = 'aries_community.AriesOrganization'
ARIES_ORG_RELATION_MODEL = 'aries_community.AriesOrgRelationship'

DEFAULT_USER_ROLE = 'User'
DEFAULT_ORG_ROLE = 'Admin'

LOGOUT_REDIRECT_URL = '/'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

gettext = lambda s: s
LANGUAGES = (
    ('en', gettext('English')),
    ('es', gettext('Spanish')),
    ('zh-hans', gettext('Chinese')),
    ('fr', gettext('French')),
)
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
MODELTRANSLATION_TRANSLATION_REGISTRY = "aries_community.translation"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
