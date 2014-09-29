import logging
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'rjjklyhpxrtrandbxx8s4m@aigiw&!i6d2=g&$b-)lueruz!aw'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'autoreduce_webapp',
    'reduction_viewer',
    'reduction_variables',
)

AUTH_PROFILE_MODULE = 'reduction_variables.UserProfile'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates')
TEMPLATE_DIRS = (
    TEMPLATE_PATH,
)

ROOT_URLCONF = 'autoreduce_webapp.urls'

WSGI_APPLICATION = 'autoreduce_webapp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'autoreduction',
        'USER' : 'autoreduce',
        'PASSWORD' : 'password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'
STATIC_PATH = os.path.join(BASE_DIR,'static')
STATICFILES_DIRS = (
    STATIC_PATH,
)

# Logging
# https://docs.python.org/2/howto/logging.html

LOG_FILE = os.path.join(BASE_DIR, 'autoreduction.log')
if DEBUG:
    LOG_LEVEL = logging.DEBUG
else:
    LOG_LEVEL = logging.INFO

# ActiveMQ 

ACTIVEMQ = {
    'topics' : [
        '/topic/DataReady',
        '/topic/ReductionPending',
        '/topic/ReductionStarted',
        '/topic/ReductionComplete',
        '/topic/ReductionError'
        ],
    'username' : 'admin',
    'password' : 'pa$$w0rd',
    'broker' : [("datareducedev.isis.cclrc.ac.uk", 61613)]
}

# File Locations

REDUCTION_SCRIPT_BASE = '/reduction_data/'
ARCHIVE_BASE = ''

# ICAT 

ICAT = {
    'AUTH' : 'uows',
    'URL' : 'https://icatdev.isis.cclrc.ac.uk/ICATService/ICAT?wsdl',
    'USER' : 'icat',
    'PASSWORD' : 'icat'
}

# UserOffice WebService

UOWS_URL = ''