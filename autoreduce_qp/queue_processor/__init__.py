# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

# configures the logging for this whole application

import logging.config
import os
import django
from django.conf import settings
from autoreduce_qp.autoreduce_django.settings import DATABASES, INSTALLED_APPS

from .settings import LOG_LEVEL, AUTOREDUCE_HOME_ROOT

os.makedirs(os.path.join(AUTOREDUCE_HOME_ROOT, "logs"), exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'root_file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(AUTOREDUCE_HOME_ROOT, 'logs', 'root.log'),
            'formatter': 'verbose',
            'maxBytes': 104857600,
            'backupCount': 20,
        },
        'queue_processor_file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(AUTOREDUCE_HOME_ROOT, 'logs', 'queue_processor.log'),
            'formatter': 'verbose',
            'maxBytes': 104857600,
            'backupCount': 20,
        },
        'autoreduction_file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(AUTOREDUCE_HOME_ROOT, 'logs', 'autoreduction_processor.log'),
            'formatter': 'verbose',
            'maxBytes': 104857600,
            'backupCount': 20,
        },
        'handle_queue_message_file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(AUTOREDUCE_HOME_ROOT, 'logs', 'handle_queue_message.log'),
            'formatter': 'verbose',
            'maxBytes': 104857600,
            'backupCount': 20,
        },
        'webapp_file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(AUTOREDUCE_HOME_ROOT, 'logs', 'webapp.log'),
            'formatter': 'verbose',
            'maxBytes': 104857600,
            'backupCount': 20,
        },
        'stdout': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'level': LOG_LEVEL,
        'handlers': ['root_file'],
        'propagate': True
    },
    'loggers': {
        'queue_processor': {
            'handlers': ['stdout', 'queue_processor_file'],
            'propagate': True,
            'level': LOG_LEVEL,
        },
        'queue_listener': {
            'handlers': ['stdout', 'queue_processor_file'],
            'propagate': True,
            'level': LOG_LEVEL,
        },
        'django.server': {
            'handlers': ['stdout', 'webapp_file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'app': {
            'handlers': ['stdout', 'webapp_file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'reduction_runner': {
            'handlers': ['stdout', 'autoreduction_file'],
            'propagate': True,
            'level': LOG_LEVEL,
        },
        'reduction_service': {
            'handlers': ['stdout', 'autoreduction_file'],
            'propagate': True,
            'level': LOG_LEVEL,
        },
        'handle_queue_message': {
            'handlers': ['stdout', 'handle_queue_message_file'],
            'propagate': True,
            'level': LOG_LEVEL,
        },
        'stomp.py': {
            'propagate': False,
            'level': 'ERROR'
        }
    }
}

logging.config.dictConfig(LOGGING)

if not settings.configured:
    settings.configure(DATABASES=DATABASES, INSTALLED_APPS=INSTALLED_APPS)
    django.setup()
