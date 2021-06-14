# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

# configures the logging for this whole application

import django
from django.conf import settings as dj_settings

from autoreduce_qp.autoreduce_django.settings import DATABASES, INSTALLED_APPS

if not dj_settings.configured:
    dj_settings.configure(DATABASES=DATABASES, INSTALLED_APPS=INSTALLED_APPS)
    django.setup()
