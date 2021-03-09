# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Initialise admin pages
"""
from django.contrib import admin

from .models import UserCache, InstrumentCache, ExperimentCache

admin.site.register(UserCache)
admin.site.register(InstrumentCache)
admin.site.register(ExperimentCache)
