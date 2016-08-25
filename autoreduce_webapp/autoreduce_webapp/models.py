from django.db import models
from reduction_viewer.models import Instrument, Experiment, ReductionRun


class Cache(model.Model):
    created = models.DateTimeField(auto_now_add=True, blank=False)

    def __unicode__(self):
        return u'%s' % self.name
    

class UserCache(Cache):
    name = models.IntegerField(blank=False)
    associated_experiments = models.ManyToManyField(Experiment)
    owned_instruments = models.ManyToManyField(Instrument)
    valid_instruments = models.ManyToManyField(Instrument)
    is_admin = models.BooleanField(default=False)
    is_instrument_scientist = models.BooleanField(default=False)


class InstrumentCache(Cache):
    name = models.CharField(max_length=80)
    upcoming_experiments = models.ManyToManyField(Experiment)


class ExperimentCache(Cache):
    reference_number = models.IntegerField(blank=False)
    start_date = models.TextField(default='')
    end_date = models.TextField(default='')
    title = models.TextField(default='')
    summary = models.TextField(default='')
    instrument = models.TextField(default='')
    pi = models.TextField(default='')