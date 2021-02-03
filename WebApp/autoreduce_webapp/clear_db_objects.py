# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

# Use this to clear all objects in Experiment, Instrument and ReductionRun

from reduction_viewer.models import Experiment, Instrument, ReductionRun
from autoreduce_webapp.settings import DATABASES

if DATABASES["default"]["HOST"] != "127.0.0.1":
    raise RuntimeError(
        "Trying to clear a DB that is not on 127.0.0.1/LOCALHOST. This is dangerous so this script stops the exectuion.\n"
        f"If you really mean to delete the DB at:\n\t{DATABASES['default']['HOST']}\nthen you will have to manually go into this script and delete this check."
    )

for o in Experiment.objects.all():
    o.delete()
for o in Instrument.objects.all():
    o.delete()
for o in ReductionRun.objects.all():
    o.delete()
