# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module to deal with creating and caneling of reduction runs in the database.
"""
import datetime
import logging.config

from queue_processors.queue_processor.settings import LOGGING

from queue_processors.queue_processor.queueproc_utils.instrument_variable_utils \
    import InstrumentVariablesUtils
from queue_processors.queue_processor.queueproc_utils.messaging_utils import MessagingUtils
from queue_processors.queue_processor.queueproc_utils.status_utils import StatusUtils
from queue_processors.queue_processor.queueproc_utils.variable_utils import VariableUtils

from model.database import access

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")  # pylint: disable=invalid-name


class ReductionRunUtils:
    """ Reduction run utils, deals with creating and canceling of runs. """

    @staticmethod
    def cancel_run(reduction_run):
        """
        Try to cancel the run given, or the run that was scheduled as the next retry of the run.
        When we cancel, we send a message to the backend queue processor, telling it to ignore this
        run if it arrives. This is most likely through a delayed message through ActiveMQ's. We
        also set statuses and error messages. If we can't do any of the above, we set the variable
        (retry_run.cancel) that tells the frontend to not schedule another retry if the next run
        fails.
        """

        def set_cancelled(run):
            """ Set a run as canceled """
            run.message = "Run cancelled by user"
            run.status = StatusUtils().get_error()
            run.finished = datetime.datetime.utcnow()
            run.retry_when = None
            access.save_record(run)

        # This is the queued run, send the message to queueProcessor to cancel it
        if reduction_run.status == StatusUtils().get_queued():
            MessagingUtils().send_cancel(reduction_run)
            set_cancelled(reduction_run)

        # Otherwise this run has already failed, and we're looking at a scheduled rerun of it
        # We don't actually have a rerun, so just ensure the retry time is set to "Never" (None)
        elif not reduction_run.retry_run:
            reduction_run.retry_when = None

        # This run is being queued to retry, so send the message to queueProcessor to cancel it,
        # and set it as cancelled
        elif reduction_run.retry_run.status == StatusUtils().get_queued():
            MessagingUtils().send_cancel(reduction_run.retry_run)
            set_cancelled(reduction_run.retry_run)

        # We have a run that's retrying, so just make sure it doesn't retry next time
        elif reduction_run.retry_run.status == StatusUtils().get_processing():
            reduction_run.cancel = True
            reduction_run.retry_run.cancel = True

        # The retry run already completed, so do nothing
        else:
            pass

        # save the run states we modified
        access.save_record(reduction_run)
        if reduction_run.retry_run:
            access.save_record(reduction_run.retry_run)

    @staticmethod
    def create_retry_run(user_id, reduction_run, script=None, variables=None, delay=0):
        """
        Create a run ready for re-running based on the run provided. If variables (RunVariable) are
        provided, copy them and associate them with the new one, otherwise use the previous run's.
        If a script (as a string) is supplied then use it, otherwise use the previous run's.
        """
        # find the previous run version, so we don't create a duplicate
        last_version = -1
        model = access.start_database().data_model
        reduction_records = model.ReductionRun.objects \
            .filter(experiment=reduction_run.experiment) \
            .filter(run_number=reduction_run.run_number)
        for run in reduction_records:
            last_version = max(last_version, run.run_version)

        # get the script to use:
        script_text = script if script is not None else reduction_run.script

        # create the run object and save it
        new_job = model.ReductionRun(run_number=reduction_run.run_number,
                                     run_version=last_version + 1,
                                     run_name="",
                                     experiment=reduction_run.experiment,
                                     instrument=reduction_run.instrument,
                                     script=script_text,
                                     status=StatusUtils().get_queued(),
                                     created=datetime.datetime.utcnow(),
                                     last_updated=datetime.datetime.utcnow(),
                                     message="",
                                     started_by=user_id,
                                     cancel=0,
                                     hidden_in_failviewer=0,
                                     admin_log="",
                                     reduction_log="")

        try:
            access.save_record(new_job)

            reduction_run.retry_run = new_job
            reduction_run.retry_when = \
                datetime.datetime.utcnow() + datetime.timedelta(seconds=delay if delay else 0)
            access.save_record(reduction_run)

            data_locations = model.DataLocation.objects \
                .filter(reduction_run_id=reduction_run.id)

            # copy the previous data locations
            for data_location in data_locations:
                new_data_location = model.DataLocation(file_path=data_location.file_path,
                                                       reduction_run=new_job)
                access.save_record(new_data_location)

            if variables is not None:
                # associate the variables with the new run
                for var in variables:
                    var.reduction_run = new_job
                    access.save_record(var)
            else:
                # provide variables if they aren't already
                InstrumentVariablesUtils().create_variables_for_run(new_job)

            return new_job

        except:
            new_job.delete()
            raise

    @staticmethod
    def get_script_and_arguments(reduction_run):
        """
        Fetch the reduction script from the given run and return it as a string, along with a
        dictionary of arguments.
        """
        script = reduction_run.script
        model = access.start_database().variable_model
        run_variable_records = model.RunVariable.objects \
            .filter(reduction_run_id=reduction_run.id)

        standard_vars, advanced_vars = {}, {}
        for run_variable in run_variable_records:
            variable = model.Variable.objects.filter(id=run_variable.variable_ptr_id).first()
            value = VariableUtils().convert_variable_to_type(variable.value, variable.type)
            if variable.is_advanced:
                advanced_vars[variable.name] = value
            else:
                standard_vars[variable.name] = value

        arguments = {'standard_vars': standard_vars, 'advanced_vars': advanced_vars}

        return script, arguments
