# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Utility functions for the reduction viewer models

Note: This file has a large number of pylint disable as it was un unit tested
at the time of fixing the pylint issues. Once unit tested properly, these disables
should be able to be removed. Many are relating to imports
"""
import datetime
import logging
import time
import traceback

import django.core.exceptions
import django.http
from autoreduce_webapp.settings import FACILITY
from django.utils import timezone
from model.message.message import Message

from reduction_viewer.models import DataLocation, Instrument, ReductionRun
from utils.clients.queue_client import QueueClient
from instrument.models import RunVariable
from queue_processors.queue_processor.status_utils import StatusUtils

STATUS = StatusUtils()
LOGGER = logging.getLogger('app')


# pylint:disable=too-few-public-methods
class InstrumentUtils(object):
    """
    Utilities for the Instrument model
    """
    @staticmethod
    def get_instrument(instrument_name):
        """
        Helper method that will try to get an instrument matching the given name
        or create one if it doesn't yet exist
        """
        try:
            # pylint:disable=no-member
            instrument = Instrument.objects.get(name__iexact=instrument_name)
        except django.core.exceptions.ObjectDoesNotExist:
            raise django.http.Http404()
        return instrument


class ReductionRunUtils(object):
    """
    Utilities for the ReductionRun model
    """
    @staticmethod
    def make_kwargs_from_runvariables(reduction_run, use_value=False):
        standard_vars = {}
        advanced_vars = {}

        for run_variable in reduction_run.run_variables.all():
            variable = run_variable.variable
            if variable.is_advanced:
                advanced_vars[variable.name] = variable.value if use_value else variable
            else:
                standard_vars[variable.name] = variable.value if use_value else variable

        return {"standard_vars": standard_vars, "advanced_vars": advanced_vars}

    @staticmethod
    def send_retry_message(user_id: int, most_recent_run: ReductionRun, script_text: str, new_script_arguments: dict,
                           overwrite_previous_data: bool):
        message = Message(started_by=user_id,
                          run_number=most_recent_run.run_number,
                          instrument=most_recent_run.instrument.name,
                          rb_number=most_recent_run.experiment.reference_number,
                          data=most_recent_run.data_location.first().file_path,
                          reduction_script=script_text,
                          reduction_arguments=new_script_arguments,
                          run_version=most_recent_run.run_version,
                          facility=FACILITY,
                          overwrite=overwrite_previous_data)
        MessagingUtils.send(message)

    @staticmethod
    def send_retry_message_same_args(user_id: int, most_recent_run: ReductionRun):
        ReductionRunUtils.send_retry_message(user_id, most_recent_run, most_recent_run.script,
                                             ReductionRunUtils.make_kwargs_from_runvariables(most_recent_run, use_value=True),
                                             most_recent_run.overwrite)

    # pylint:disable=invalid-name,too-many-arguments,too-many-locals
    @staticmethod
    def createRetryRun(user_id, reduction_run, overwrite=None, script=None, variables=None, delay=0, description=''):
        """
        Create a run ready for re-running based on the run provided.
        If variables (RunVariable) are provided, copy them and associate
        them with the new one, otherwise use the previous run's.
        If a script (as a string) is supplied then use it, otherwise use the previous run's.
        """
        from instrument.utils import InstrumentVariablesUtils

        run_last_updated = reduction_run.last_updated

        # find the previous run version, so we don't create a duplicate
        last_version = -1
        # pylint:disable=no-member
        previous_run = ReductionRun.objects.filter(experiment=reduction_run.experiment,
                                                   run_number=reduction_run.run_number) \
            .order_by("-run_version").first()

        last_version = previous_run.run_version

        # get the script to use:
        script_text = script if script is not None else reduction_run.script

        # create the run object and save it
        new_job = ReductionRun(instrument=reduction_run.instrument,
                               run_number=reduction_run.run_number,
                               run_name=description,
                               run_version=last_version + 1,
                               experiment=reduction_run.experiment,
                               started_by=user_id,
                               status=StatusUtils().get_queued(),
                               script=script_text,
                               overwrite=overwrite)

        # Check record is safe to save
        try:
            new_job.full_clean()
        except Exception as exception:
            LOGGER.error(traceback.format_exc())
            LOGGER.error(exception)
            raise

        # Attempt to save
        try:
            new_job.save()
        except ValueError as exception:
            # This usually indicates a F.K. constraint mismatch. Maybe we didn't get a record in?
            LOGGER.error(traceback.format_exc())
            LOGGER.error(exception)
            raise

        reduction_run.retry_run = new_job
        reduction_run.retry_when = timezone.now().replace(microsecond=0) + datetime.timedelta(
            seconds=delay if delay else 0)
        reduction_run.save()

        # pylint:disable=no-member
        ReductionRun.objects.filter(id=reduction_run.id).update(last_updated=run_last_updated)

        # copy the previous data locations
        # pylint:disable=no-member
        for data_location in reduction_run.data_location.all():
            new_data_location = DataLocation(file_path=data_location.file_path, reduction_run=new_job)
            new_data_location.save()
            new_job.data_location.add(new_data_location)

        if variables is not None:
            # associate the variables with the new run
            for var in variables:
                var.reduction_run = new_job
                var.save()
        else:
            # provide variables if they aren't already
            InstrumentVariablesUtils().create_variables_for_run(new_job)

        return new_job  #

    @staticmethod
    def get_script_and_arguments(reduction_run):
        """
        Fetch the reduction script from the given run and return it as a string,
        along with a dictionary of arguments.
        """
        from instrument.utils import VariableUtils

        script = reduction_run.script

        # pylint:disable=no-member
        run_variables = RunVariable.objects.filter(reduction_run=reduction_run)
        standard_vars, advanced_vars = {}, {}
        for variables in run_variables:
            value = VariableUtils().convert_variable_to_type(variables.value, variables.type)
            if variables.is_advanced:
                advanced_vars[variables.name] = value
            else:
                standard_vars[variables.name] = value

        arguments = {'standard_vars': standard_vars, 'advanced_vars': advanced_vars}

        return script, arguments


class ScriptUtils(object):
    """
    Utilities for the scripts field
    """
    @staticmethod
    def get_reduce_scripts(scripts):
        """
        Returns a tuple of (reduction script, reduction vars script),
        each one a string of the contents of the script, given a list of script objects.
        """
        script_out = None
        script_vars_out = None
        for script in scripts:
            if script.file_name == "reduce.py":
                script_out = script
            elif script.file_name == "reduce_vars.py":
                script_vars_out = script
        return script_out, script_vars_out

    def get_cache_scripts_modified(self, scripts):
        """
        :returns: The last time the scripts in the database were
        modified (in seconds since epoch).
        """
        script_modified = None
        script_vars_modified = None

        for script in scripts:
            if script.file_name == "reduce.py":
                script_modified = self._convert_time_from_string(str(script.created))
            elif script.file_name == "reduce_vars.py":
                script_vars_modified = self._convert_time_from_string(str(script.created))
        return script_modified, script_vars_modified

    @staticmethod
    def _convert_time_from_string(string_time):
        """
        :return: time as integer for epoch
        """
        time_format = "%Y-%m-%d %H:%M:%S"
        string_time = string_time[:string_time.find('+')]
        return int(time.mktime(time.strptime(string_time, time_format)))


class MessagingUtils(object):
    """
    Utilities for sending messages to ActiveMQ
    """
    def send_pending(self, reduction_run, delay=None):
        raise RuntimeError("Stop using this")

    def send_cancel(self, reduction_run):
        raise RuntimeError("Stop using this")

    @staticmethod
    def _make_pending_msg(reduction_run):
        """ Creates a Message from the given run, ready to be sent to ReductionPending. """
        script, arguments = ReductionRunUtils().get_script_and_arguments(reduction_run)

        # Currently only support single location
        data_location = reduction_run.data_location.first()
        if data_location:
            data_path = data_location.file_path
        else:
            raise Exception("No data path found for reduction run")

        message = Message(run_number=reduction_run.run_number,
                          instrument=reduction_run.instrument.name,
                          rb_number=str(reduction_run.experiment.reference_number),
                          data=data_path,
                          reduction_script=script,
                          reduction_arguments=arguments,
                          run_version=reduction_run.run_version,
                          facility=FACILITY,
                          overwrite=reduction_run.overwrite)
        return message

    @staticmethod
    def send(message):
        """ Sends message to ReductionPending (with the specified delay) """
        message_client = QueueClient()
        message_client.connect()

        message_client.send('/queue/DataReady', message, priority='1')
        message_client.disconnect()
