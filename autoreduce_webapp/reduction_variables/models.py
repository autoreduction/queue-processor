from django.db import models
from reduction_viewer.models import Instrument, ReductionRun

class InstrumentVariable(models.Model):
    instrument = models.ForeignKey(Instrument)
    start_run = models.IntegerField(blank=False)
    name = models.CharField(max_length=50, blank=False)
    value = models.CharField(max_length=300, blank=False)
    type = models.CharField(max_length=50, blank=False)
    is_advanced = models.BooleanField(default=False)
    scripts = models.ManyToManyField(ScriptFile)

    def __unicode__(self):
        return u'%s - %s=%s' % (self.instrument.name, self.name, self.value)

class RunVariable(models.Model):
    reduction_run = models.ForeignKey(ReductionRun, related_name="run_variables")
    name = models.CharField(max_length=50, blank=False)
    value = models.CharField(max_length=300, blank=False)
    type = models.CharField(max_length=50, blank=False)
    scripts = models.ManyToManyField(ScriptFile)

    def __unicode__(self):
        return u'%s - %s=%s' % (self.reduction_run, self.name, self.value)

class ScriptFile(models.Model):
    script = models.BinaryField(blank=False)
    file_name = models.CharField(max_length=50, blank=False)
    created = models.DateTimeField(auto_now_add=True,blank=True)

    def __unicode__(self):
        return u'%s' % self.file_name
