# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Register models variables here
"""
from django.contrib import admin
from reduction_variables.models import InstrumentVariable, RunVariable

# Register your models here.
admin.site.register(InstrumentVariable)
admin.site.register(RunVariable)
