# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Register all the django models for reduction viewer
"""
from django.contrib import admin
from reduction_viewer.models import (Instrument, Experiment, Status, ReductionRun, DataLocation, ReductionLocation,
                                     Setting, Notification)

admin.site.register(Instrument)
admin.site.register(Experiment)
admin.site.register(Status)
admin.site.register(ReductionRun)
admin.site.register(DataLocation)
admin.site.register(ReductionLocation)
admin.site.register(Setting)
admin.site.register(Notification)
