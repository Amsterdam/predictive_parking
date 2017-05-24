"""
Django settings for predictive_parking project.

NOTE: database is predictiveparking.

"""

import re
import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
insecure_key = 'insecure'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', insecure_key)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = SECRET_KEY == insecure_key

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

ALLOWED_HOSTS = ['*']


INTERNAL_IPS = ('127.0.0.1', '0.0.0.0')

OVERRIDE_HOST_ENV_VAR = 'DATABASE_HOST_OVERRIDE'
OVERRIDE_PORT_ENV_VAR = 'DATABASE_PORT_OVERRIDE'

OVERRIDE_EL_HOST_VAR = 'ELASTICSEARCH_HOST_OVERRIDE'
OVERRIDE_EL_PORT_VAR = 'ELASTICSEARCH_PORT_OVERRIDE'


SITE_ID = 1
# Application definition

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    'django_extensions',
    'django_filters',

    'rest_framework_gis',
    'rest_framework',

    'datapunt',
    'health',

    'metingen',
    'wegdelen',
    'parkeerkans',

    'predictive_parking',
]

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


if DEBUG:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')


ROOT_URLCONF = 'predictive_parking.urls'

INTERNAL_IPS = ['127.0.0.1']

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                # 'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'predictive_parking.wsgi.application'


def get_docker_host():
    """Find the local docker-deamon
    """
    d_host = os.getenv('DOCKER_HOST', None)
    if d_host:
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', d_host):
            return d_host
        return re.match(r'tcp://(.*?):\d+', d_host).group(1)
    return 'localhost'


# noinspection PyBroadException
def in_docker():
    """
    Checks pid 1 cgroup settings to check with reasonable certainty we're in a
    docker env.
    :return: true when running in a docker container, false otherwise
    """
    try:
        return ':/docker/' in open('/proc/1/cgroup', 'r').read()
    except:
        return False


class LocationKey(object):
    local = 'local'
    docker = 'docker'
    override = 'override'


def get_database_key():
    if os.getenv(OVERRIDE_HOST_ENV_VAR):
        return LocationKey.override
    elif in_docker():
        return LocationKey.docker

    return LocationKey.local


DATABASE_OPTIONS = {
    LocationKey.docker: {
        'HOST': 'database',
        'PORT': '5432'
    },
    LocationKey.local: {
        'HOST': get_docker_host(),
        'PORT': '5432'    # defined in compose file
    },
    LocationKey.override: {
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': os.getenv(OVERRIDE_HOST_ENV_VAR),
        'PORT': os.getenv(OVERRIDE_PORT_ENV_VAR, '5432')
    }
}


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'predictiveparking'),
        'USER': os.getenv('DATABASE_USER', 'predictiveparking'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
    }
}

DATABASES['default'].update(DATABASE_OPTIONS[get_database_key()])

ELASTIC_INDICES = {
    'scans': 'scans-*',
}


ELASTIC_SEARCH_HOSTS = ["{}:{}".format(
    os.getenv('ELASTICSEARCH_HOST_OVERRIDE', 'elasticsearch'),
    os.getenv('ELASTICSEARCH_PORT_OVERRIDE', 9200))]


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

REST_FRAMEWORK = dict(
    PAGE_SIZE=20,

    MAX_PAGINATE_BY=100,

    UNAUTHENTICATED_USER=None,
    UNAUTHENTICATED_TOKE=None,

    DEFAULT_RENDERER_CLASSES=(
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer'
    ),
    DEFAULT_FILTER_BACKENDS=(
        'rest_framework.filters.DjangoFilterBackend',
        # 'rest_framework.filters.OrderingFilter',

        ),
    COERCE_DECIMAL_TO_STRING=True,
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'console': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },

    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    },


    'loggers': {
        'django.db': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
        },

        # Debug all batch jobs
        'doc': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'index': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },

        'search': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },

        'elasticsearch': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },

        'urllib3': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },

        'factory.containers': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },

        'factory.generate': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },

        'requests.packages.urllib3.connectionpool': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },

        # Log all unhandled exceptions
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },

    },
}
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
