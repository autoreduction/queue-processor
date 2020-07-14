# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Initialise admin pages
"""
import django.contrib.admin

# pylint: disable=relative-import
from .models import UserCache, InstrumentCache, ExperimentCache

django.contrib.admin.site.register(UserCache)
django.contrib.admin.site.register(InstrumentCache)
django.contrib.admin.site.register(ExperimentCache)
