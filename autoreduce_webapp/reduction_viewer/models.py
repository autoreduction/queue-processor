from django.db import models
from django.contrib.auth.models import User
from autoreduce_webapp.utils import SeparatedValuesField

class Instrument(models.Model):
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    scientists = models.ManyToManyField(User)

    def __unicode__(self):
        return u'%s' % self.name

    def get_experiments():
        #ToDo: get filtered experiments
        pass

    def should_show_instrument():
        #ToDo: return whether or not to display this instrument based on its status and if the user has any valid runs 
        pass

class Experiment(models.Model):
    reference_number = models.IntegerField()

    def __unicode__(self):
        return u'%s' % self.reference_number

    def get_runs():
        #ToDo: get filtered experiment runs
        pass

    def get_ICAT_details():
        #ToDo: get details from ICAT
        pass

    def is_team_member(possibleMember):
        #ToDo: check is the given user is a member of the experiment team
        pass

class Status(models.Model):
    value = models.CharField(max_length=25)

    def __unicode__(self):
        return u'%s' % self.value

class ReductionRun(models.Model):
    run_number = models.IntegerField(blank=False)
    run_name = models.CharField(max_length=50)
    run_version = models.IntegerField(blank=False)
    experiment = models.ForeignKey(Experiment,blank=False)
    created = models.DateTimeField(auto_now_add=True,blank=False)
    started_by = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True,blank=False)
    status = models.ForeignKey(Status, blank=False, related_name='+', default=1)
    started = models.DateTimeField()
    finished = models.DateTimeField()
    message = models.CharField(max_length=255)
    graph = SeparatedValuesField()

    def __unicode__(self):
        if seld.run_name:
            return u'%s-%s' % (self.run_number, self.run_name)
        else:
            return u'%s' % self.run_number

class DataLocation(models.Model):
    file_path = models.CharField(max_length=255)
    reduction_run = models.ForeignKey(ReductionRun, blank=False, related_name='data_location')
    
    def __unicode__(self):
        return u'%s' % self.file_path

class ReductionLocation(models.Model):
    file_path = models.CharField(max_length=255)
    reduction_run = models.ForeignKey(ReductionRun, blank=False, related_name='reduction_location')
    
    def __unicode__(self):
        return u'%s' % self.file_path

class Setting(models.Model):
    name = models.CharField(max_length=50, blank=False)
    value = models.CharField(max_length=50)

    def __unicode__(self):
        return u'%s=%s' % (self.name, self.value)

class Notification(models.Model):
    SEVERITY_CHOICES = (
        (1, 'info'),
        (2, 'warning'),
        (3, 'error')
    );

    message = models.CharField(max_length=50, blank=False)
    is_active = models.BooleanField(default=True)
    severity = models.CharField(max_length=1,choices=SEVERITY_CHOICES,default=1)
    is_staff_only = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s' % self.message