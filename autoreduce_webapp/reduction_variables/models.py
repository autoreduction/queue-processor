from django.db import models
from reduction_viewer.models import Instrument, ReductionRun

class ScriptFile(models.Model):
    script = models.BinaryField(blank=False)
    file_name = models.CharField(max_length=50, blank=False)
    created = models.DateTimeField(auto_now_add=True,blank=True)

    def __unicode__(self):
        return u'%s' % self.file_name

class InstrumentVariable(models.Model):
    instrument = models.ForeignKey(Instrument)
    start_run = models.IntegerField(blank=True, null=True)
    experiment_reference = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=50, blank=False)
    value = models.CharField(max_length=300, blank=False)
    type = models.CharField(max_length=50, blank=False)
    is_advanced = models.BooleanField(default=False)
    scripts = models.ManyToManyField(ScriptFile)
    help_text = models.CharField(max_length=300, blank=True, null=True, default='')

    def __unicode__(self):
        return u'%s - %s=%s' % (self.instrument.name, self.name, self.value)

    def sanitized_name(self):
        """
        Returns a HTMl-friendly name that can be used as element IDs or form input names
        """
        return self.name.replace(' ', '-')

class RunVariable(models.Model):
    reduction_run = models.ForeignKey(ReductionRun, related_name="run_variables")
    name = models.CharField(max_length=50, blank=False)
    value = models.CharField(max_length=300, blank=False)
    type = models.CharField(max_length=50, blank=False)
    scripts = models.ManyToManyField(ScriptFile)
    is_advanced = models.BooleanField(default=False)
    help_text = models.CharField(max_length=300, blank=True, null=True, default='')

    def __unicode__(self):
        return u'%s - %s=%s' % (self.reduction_run, self.name, self.value)

    def sanitized_name(self):
        """
        Returns a HTMl-friendly name that can be used as element IDs or form input names
        """
        return self.name.replace(' ', '-')