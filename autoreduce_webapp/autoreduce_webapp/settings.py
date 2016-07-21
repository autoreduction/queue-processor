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

ADMINS = ()

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'autoreduce_webapp',
    'reduction_viewer',
    'reduction_variables',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'autoreduce_webapp.backends.UOWSAuthenticationBackend',
)
LOGIN_URL = '/autoreduce_webapp/'

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

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
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
    #LOG_LEVEL = 'DEBUG' 
    LOG_LEVEL = 'INFO'
else:
    LOG_LEVEL = 'INFO'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': LOG_LEVEL,
            'class': 'logging.FileHandler',
            'filename': LOG_FILE,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers':['file'],
            'propagate': True,
            'level':LOG_LEVEL,
        },
        'app' : {
            'handlers':['file'],
            'propagate': True,
            'level':'DEBUG',
        },
    }
}

# ActiveMQ 

ACTIVEMQ = {
    'topics' : [
        '/queue/DataReady',
        #'/queue/ReductionPending', - Only used by autoreduction server
        '/queue/ReductionStarted',
        '/queue/ReductionComplete',
        '/queue/ReductionError'
        ],
    'username' : 'autoreduce',
    'password' : 'pa$$w0rd',
    'broker' : [("autoreduce.isis.cclrc.ac.uk", 61613)]
}

# File Locations

#REDUCTION_SCRIPT_BASE = '/reduction_data/'
#ARCHIVE_BASE = ''
if os.name == 'nt':
    REDUCTION_DIRECTORY = '\\\\isis\\inst$\\NDX%s\\user\\scripts\\autoreduction' # %(instrument)
    TEMP_OUTPUT_DIRECTORY = '\\\\autoreduce\\data\\reduction_script_temp'
    ARCHIVE_DIRECTORY = '\\\\isis\\inst$\\NDX%s\\Instrument\\data\\cycle_%s\\autoreduced\\%s\\%s' # %(instrument, cycle, experiment_number, run_number)
else:
    REDUCTION_DIRECTORY = '/isis/NDX%s/user/scripts/autoreduction' # %(instrument)
    TEMP_OUTPUT_DIRECTORY = '/tmp/autoreduce'
    ARCHIVE_DIRECTORY = '/isis/NDX%s/Instrument/data/cycle_%s/autoreduced/%s/%s' # %(instrument, cycle, experiment_number, run_number)

# ICAT 

ICAT = {
    'AUTH' : 'simple',
    'URL' : 'https://icatdev.isis.cclrc.ac.uk/ICATService/ICAT?wsdl',
    'USER' : 'autoreduce',
    'PASSWORD' : 'icat'
}

# UserOffice WebService

UOWS_URL = 'https://fitbawebdev.isis.cclrc.ac.uk:8181/UserOfficeWebService/UserOfficeWebService?wsdl'
UOWS_LOGIN_URL = 'https://devusers.facilities.rl.ac.uk/auth/?service=http://datareducedev.isis.cclrc.ac.uk&redirecturl='

# Constant vars

FACILITY = "ISIS"
