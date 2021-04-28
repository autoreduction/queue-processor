# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Definition of Variable classes used for the WebApp model
"""
from django.db import models
from reduction_viewer.models import Instrument, ReductionRun


class Variable(models.Model):
    """
    Generic model class that should be treated as abstract
    """
    name = models.CharField(max_length=50, blank=False)
    value = models.CharField(max_length=300, blank=True, null=True)
    type = models.CharField(max_length=50, blank=False)
    is_advanced = models.BooleanField(default=False)
    help_text = models.TextField(blank=True, null=True, default='')

    def sanitized_name(self):
        """
        Returns a HTMl-friendly name that can be used as element IDs or form input names
        """
        # pylint:disable=no-member
        return self.name.replace(' ', '-')


class InstrumentVariable(Variable):
    """
    Instrument specific variable class

    - Holds the IDs of the variables used for the instrument

    - Holds `start_run` for functionality to "Configure new runs" - e.g. variables starting from `start_run` will
      use the defaults that are queried with

    """
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    experiment_reference = models.IntegerField(blank=True, null=True)
    start_run = models.IntegerField(blank=True, null=True)
    tracks_script = models.BooleanField(default=False)

    # pylint:disable=no-member
    def __str__(self):
        return f"{self.instrument.name} - {self.name}=self.value"


class RunVariable(models.Model):
    """
    Run specific Variable class
    """
    variable = models.ForeignKey(Variable, related_name="runs", on_delete=models.CASCADE)
    reduction_run = models.ForeignKey(ReductionRun, related_name="run_variables", on_delete=models.CASCADE)
