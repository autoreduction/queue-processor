# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

# configures the logging for this whole application

import logging.config
import os
from utils.project.structure import get_project_root

from .settings import LOG_LEVEL

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
            'filename': os.path.join(get_project_root(), 'logs', 'everything_else.log'),
            'formatter': 'verbose',
            'maxBytes': 104857600,
            'backupCount': 20,
        },  'file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(get_project_root(), 'logs', 'queue_processor.log'),
            'formatter': 'verbose',
            'maxBytes': 104857600,
            'backupCount': 20,
        },
        'autoreduction_file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(get_project_root(), 'logs', 'autoreduction_processor.log'),
            'formatter': 'verbose',
            'maxBytes': 104857600,
            'backupCount': 20,
        },
        'handle_queue_message_file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(get_project_root(), 'logs', 'handle_queue_message.log'),
            'formatter': 'verbose',
            'maxBytes': 104857600,
            'backupCount': 20,
        },
    },
    'root': {
        'level': LOG_LEVEL,
        'handlers': ['file'],
        'propagate': True
    },
    'loggers': {
        'queue_processor': {
            'handlers': ['file'],
            'propagate': True,
            'level': LOG_LEVEL,
        },
        'app': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'autoreduction_processor': {
            'handlers': ['autoreduction_file'],
            'propagate': True,
            'level': LOG_LEVEL,
        },
        'handle_queue_message': {
            'handlers': ['handle_queue_message_file'],
            'propagate': True,
            'level': LOG_LEVEL,
        },
    }
}

logging.config.dictConfig(LOGGING)
