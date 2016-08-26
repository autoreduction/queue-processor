from django.db import models


class Cache(models.Model):
    created = models.DateTimeField(auto_now_add=True, blank=False)

    def __unicode__(self):
        return u'%s' % self.id_name
    

class UserCache(Cache):
    id_name = models.IntegerField(blank=False)
    associated_experiments = models.TextField(blank=True)
    owned_instruments = models.TextField(blank=True)
    valid_instruments = models.TextField(blank=True)
    is_admin = models.BooleanField(default=False)
    is_instrument_scientist = models.BooleanField(default=False)


class InstrumentCache(Cache):
    id_name = models.CharField(max_length=80)
    upcoming_experiments = models.TextField(blank=True)
    valid_experiments = models.TextField(blank=True)


class ExperimentCache(Cache):
    id_name = models.IntegerField(blank=False)
    start_date = models.TextField(default='')
    end_date = models.TextField(default='')
    title = models.TextField(default='')
    summary = models.TextField(default='')
    instrument = models.TextField(default='')
    pi = models.TextField(default='')