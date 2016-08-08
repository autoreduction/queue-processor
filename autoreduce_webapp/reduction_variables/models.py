from django.db import models
from reduction_viewer.models import Instrument, ReductionRun
        
class Variable(models.Model):
    name = models.CharField(max_length=50, blank=False)
    value = models.CharField(max_length=300, blank=False)
    type = models.CharField(max_length=50, blank=False)
    is_advanced = models.BooleanField(default=False)
    help_text = models.CharField(max_length=300, blank=True, null=True, default='')

    def __unicode__(self):
        return u'%s - %s=%s' % (self.instrument.name, self.name, self.value)

    def sanitized_name(self):
        """
        Returns a HTMl-friendly name that can be used as element IDs or form input names
        """
        return self.name.replace(' ', '-')

        
class InstrumentVariable(Variable):
    instrument = models.ForeignKey(Instrument)
    experiment = models.ForeignKey(blank=True, null=True)
    start_run = models.IntegerField(blank=True, null=True)
        
class RunVariable(Variable):
    reduction_run = models.ForeignKey(ReductionRun, related_name="run_variables")
