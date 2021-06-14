# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

# configures the logging for this whole application

import logging
import logging.handlers
import os
import sys
import django
from django.conf import settings as dj_settings
from autoreduce_utils.runtime_settings import LOG_FILE, LOG_LEVEL

from autoreduce_qp.autoreduce_django.settings import DATABASES, INSTALLED_APPS

rotating_file_handler = logging.handlers.RotatingFileHandler(filename=LOG_FILE, maxBytes=209715200, backupCount=5)
stream_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(format="[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
                    datefmt="%d/%b/%Y %H:%M:%S",
                    level=LOG_LEVEL,
                    handlers=[rotating_file_handler, stream_handler])

logging.getLogger('stomp.py').setLevel("ERROR")

if not dj_settings.configured:
    dj_settings.configure(DATABASES=DATABASES, INSTALLED_APPS=INSTALLED_APPS)
    django.setup()
