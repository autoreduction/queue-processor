# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Models that represent the tables in the database
"""
from django.core.validators import MinValueValidator, MaxLengthValidator
from django.db import models


class Instrument(models.Model):
    """
    Hold data about an Instrument
    """
    name = models.CharField(max_length=80)
    is_active = models.BooleanField(default=False)
    is_paused = models.BooleanField(default=False)

    def __str__(self):
        """
        :return: str representation of instrument
        """
        return f"{self.name}"


class Experiment(models.Model):
    """
    Holds data about an Experiment
    """
    reference_number = models.IntegerField()

    def __str__(self):
        """
        :return: str representation of experiment
        """
        return f"RB{self.reference_number}"


class Status(models.Model):
    """
    Enum table for status types of messages
    """
    STATUS_CHOICES = (('q', 'Queued'), ('p', 'Processing'), ('s', 'Skipped'), ('c', 'Completed'), ('e', 'Error'))

    value = models.CharField(max_length=1, choices=STATUS_CHOICES)

    def value_verbose(self):
        """
        :return: (str) the status as its textual value
        """
        return dict(Status.STATUS_CHOICES)[self.value]

    def __str__(self) -> str:
        """
        :return: str representation of status
        """
        return self.value_verbose()


class Software(models.Model):
    """
    Represents the software used to perform the reduction
    """
    name = models.CharField(max_length=100, blank=False, null=False)
    version = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
        return f"{self.name}-{self.version}"


class ReductionRun(models.Model):
    """
    Table designed to link all table together. This represents a single reduction run that
    takes place at ISIS. Thus, this will store all the relevant data regarding that run.
    """
    # Integer fields
    run_number = models.IntegerField(blank=False, validators=[MinValueValidator(0)])
    run_version = models.IntegerField(blank=False, validators=[MinValueValidator(0)])
    started_by = models.IntegerField(null=True, blank=True)

    # Char fields
    run_description = models.CharField(max_length=200, blank=True)

    # Text fields
    admin_log = models.TextField(blank=True)
    graph = models.TextField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    reduction_log = models.TextField(blank=True)
    # Scripts should be 100,000 chars or less. The DB supports up to 4GB strings here
    script = models.TextField(blank=False, validators=[MaxLengthValidator(100000)])

    # Date time fields
    created = models.DateTimeField(auto_now_add=True, blank=False)
    finished = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, blank=False)
    retry_when = models.DateTimeField(null=True, blank=True)
    started = models.DateTimeField(null=True, blank=True)

    # Bool field
    hidden_in_failviewer = models.BooleanField(default=False)
    overwrite = models.NullBooleanField(default=True)

    # Foreign Keys
    experiment = models.ForeignKey(Experiment, blank=False, related_name='reduction_runs', on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, related_name='reduction_runs', null=True, on_delete=models.CASCADE)
    retry_run = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.ForeignKey(Status, blank=False, related_name='+', on_delete=models.CASCADE)
    # Allowed software field to be black in code line below. Issued opened (#852) to later
    # populate this field
    software = models.ForeignKey(Software,
                                 blank=True,
                                 related_name='reduction_runs',
                                 null=True,
                                 on_delete=models.CASCADE)

    def __str__(self):
        """
        Return str representation of reduction run based on run name if available else run number
        :return: str representation of ReductionRun
        """
        return f"{self.run_number}: {self.run_description}" if self.run_description else f"{self.run_number}"

    def title(self):
        """
        :return: An interface-friendly name that identifies this run using either
        run name or run version
        """
        if self.run_version > 0:
            if self.run_description:
                title = '%s - %s' % (self.run_number, self.run_description)
            else:
                title = '%s - %s' % (self.run_number, self.run_version)
        else:
            title = '%s' % self.run_number
        return title


class DataLocation(models.Model):
    """
    Represents the location at which the unreduced data is stored on disk
    """
    file_path = models.CharField(max_length=255)
    reduction_run = models.ForeignKey(ReductionRun, blank=False, related_name='data_location', on_delete=models.CASCADE)

    def __str__(self):
        """
        :return: str representation of file path
        """
        return f"{self.file_path}"


class ReductionLocation(models.Model):
    """
    Represents the location at which the reduced data is stored on disk
    """
    file_path = models.CharField(max_length=255)
    reduction_run = models.ForeignKey(ReductionRun,
                                      blank=False,
                                      related_name='reduction_location',
                                      on_delete=models.CASCADE)

    def __str__(self):
        """
        :return: str representation of ReductionLocation
        """
        return f"{self.file_path}"


class Setting(models.Model):
    """
    Represents additional settings options for the reduction run
    """
    name = models.CharField(max_length=50, blank=False)
    value = models.CharField(max_length=50)

    def __str__(self):
        """
        :return: str representation of Setting
        """
        return f"{self.name} = {self.value}"


class Notification(models.Model):
    """
    Represents possible notification messages regarding reduction runs
    """
    SEVERITY_CHOICES = (('i', 'info'), ('w', 'warning'), ('e', 'error'))

    message = models.CharField(max_length=255, blank=False)
    is_active = models.BooleanField(default=True)
    severity = models.CharField(max_length=1, choices=SEVERITY_CHOICES, default='i')
    is_staff_only = models.BooleanField(default=False)

    def __str__(self):
        """
        :return: str representation of Notification based on message
        """
        return f"Notification: {self.message}"

    def severity_verbose(self):
        """
        :return: the severity as its textual value
        """
        return dict(Notification.SEVERITY_CHOICES)[self.severity]


class OutputType(models.Model):
    """
    Represents the output types of file that can be output from a job
    This is an enum table
    """
    type = models.CharField(max_length=50, blank=False)


class Output(models.Model):
    """
    Represents the output of a reduction job (file path and type)
    """
    job = models.ForeignKey(ReductionRun, blank=False, related_name='output', on_delete=models.CASCADE)
    file_path = models.CharField(max_length=255, blank=False)
    type = models.ForeignKey(OutputType, blank=False, related_name='output', on_delete=models.CASCADE)
