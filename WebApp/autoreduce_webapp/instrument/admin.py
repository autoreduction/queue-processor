# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Register models variables here
"""
from django.contrib import admin
from autoreduce_db.instrument.models import InstrumentVariable, RunVariable

# Register your models here.
admin.site.register(InstrumentVariable)
admin.site.register(RunVariable)
