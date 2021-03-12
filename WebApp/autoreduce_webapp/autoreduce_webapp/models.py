# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Contains all the django models
"""
from django.db import models


class Cache(models.Model):
    """
    Ensures all models that implement cache have a date time field
    """
    created = models.DateTimeField(auto_now_add=True, blank=False)

    # pylint:disable=no-member
    def __str__(self):
        return f"{self.id_name}"


class UserCache(Cache):
    """
    Model representing the cached values for the users
    """
    id_name = models.IntegerField(blank=False)
    associated_experiments = models.TextField(blank=True)
    owned_instruments = models.TextField(blank=True)
    valid_instruments = models.TextField(blank=True)
    is_admin = models.BooleanField(default=False)
    is_instrument_scientist = models.BooleanField(default=False)


class InstrumentCache(Cache):
    """
    Model representing the cached values for the instruments
    """
    id_name = models.CharField(max_length=80)
    upcoming_experiments = models.TextField(blank=True)
    valid_experiments = models.TextField(blank=True)


class ExperimentCache(Cache):
    """
    Model representing the cached values for experiments
    """
    id_name = models.IntegerField(blank=False)
    start_date = models.TextField(default='')
    end_date = models.TextField(default='')
    title = models.TextField(default='')
    summary = models.TextField(default='')
    instrument = models.TextField(default='')
    pi = models.TextField(default='')
