from django.db import models
from django.contrib.auth.models import User
from autoreduce_webapp.utils import SeparatedValuesField
import autoreduce_webapp.icat_communication

class UserProfile(models.Model):
    user_number = models.IntegerField()
    user = models.ForeignKey(User, unique=True)

class Instrument(models.Model):
    name = models.CharField(max_length=80)
    is_active = models.BooleanField(default=False)
    scientists = models.ManyToManyField(User)
    experimenters = models.ManyToManyField(User, related_name='experiment_instruments')

    def __unicode__(self):
        return u'%s' % self.name

    def get_experiments(current_user):
        reference_numbers = icat_communication.get_associated_experiments(current_user)
        return Experiment.objects.filter(reference_number__in=reference_numbers)

    def should_show_instrument(current_user):
        if current_user.is_superuser:
            ''' Superusers can see everything '''
            return True
        elif not is_active:
            ''' Don't show if it is inactive '''
            return False
        elif current_user.is_staff:
            ''' Staff can see instruments they are the scientist on '''
            if current_user.instrument_set.filter(name=name):
                return True
            else:
                ''' Get an updated list of associated instruments from ICAT '''
                current_user.instrument_set = icat_communication.get_owned_instruments(current_user.get_profile().user_number)
                current_user.save()
                if current_user.instrument_set.filter(name=name):
                    return True
        else:
            if current_user.experiment_instruments.filter(name=name):
                return True
            else:
                ''' Get an updated list of associated instruments from ICAT '''
                current_user.experiment_instruments = icat_communication.get_valid_instruments(current_user.get_profile().user_number)
                current_user.save()
                if current_user.experiment_instruments.filter(name=name):
                    return True
        return False

class Experiment(models.Model):
    reference_number = models.IntegerField()

    def __unicode__(self):
        return u'%s' % self.reference_number

    def get_ICAT_details():
        return icat_communication.get_experiment_details(reference_number)

    def is_team_member(possibleMember):
        return icat_communication.is_on_experiment_team(reference_number, possibleMember.get_profile().user_number)

class Status(models.Model):
    value = models.CharField(max_length=25)

    def __unicode__(self):
        return u'%s' % self.value

class ReductionRun(models.Model):
    instrument = models.ForeignKey(Instrument, related_name='reduction_runs', null=True)
    run_number = models.IntegerField(blank=False)
    run_name = models.CharField(max_length=50)
    run_version = models.IntegerField(blank=False)
    experiment = models.ForeignKey(Experiment,blank=False, related_name='reduction_runs')
    created = models.DateTimeField(auto_now_add=True,blank=False)
    started_by = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True,blank=False)
    status = models.ForeignKey(Status, blank=False, related_name='+', default=1)
    started = models.DateTimeField(null=True, blank=True)
    finished = models.DateTimeField(null=True, blank=True)
    message = models.CharField(max_length=255)
    graph = SeparatedValuesField(null=True, blank=True)

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