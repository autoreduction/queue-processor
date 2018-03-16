import logging.config
import datetime
from settings import LOGGING
from orm_mapping import *
from base import session
from messaging_utils import MessagingUtils
from instrument_variable_utils import InstrumentVariablesUtils
from variable_utils import VariableUtils
from status_utils import StatusUtils

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")


class ReductionRunUtils(object):
    @staticmethod
    def cancel_run(reduction_run):
        """
        Try to cancel the run given, or the run that was scheduled as the next retry of the run.
        When we cancel, we send a message to the backend queue processor, telling it to ignore this run if it arrives.
        This is most likely through a delayed message through ActiveMQ's scheduler.
        We also set statuses and error messages. If we can't do any of the above, we set the variable (retry_run.cancel)
        that tells the frontend to not schedule another retry if the next run fails.
        """

        def set_cancelled(run):
            run.message = "Run cancelled by user"
            run.status = StatusUtils().get_error()
            run.finished = datetime.datetime.now()
            run.retry_when = None
            run.save()

        # This is the queued run, send the message to queueProcessor to cancel it
        if reduction_run.status == StatusUtils().get_queued():
            MessagingUtils().send_cancel(reduction_run)
            set_cancelled(reduction_run)

        # Otherwise this run has already failed, and we're looking at a scheduled rerun of it
        # We don't actually have a rerun, so just ensure the retry time is set to "Never" (None)
        elif not reduction_run.retry_run:
            reduction_run.retry_when = None

        # This run is being queued to retry, so send the message to queueProcessor to cancel it, and set it as cancelled
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
        reduction_run.save()
        if reduction_run.retry_run:
            reduction_run.retry_run.save()

    @staticmethod
    def create_retry_run(reduction_run, script=None, variables=None, delay=0, username=None):
        """
        Create a run ready for re-running based on the run provided. If variables (RunVariable) are provided, copy them
        and associate them with the new one, otherwise use the previous run's.
        If a script (as a string) is supplied then use it, otherwise use the previous run's.
        """
        # find the previous run version, so we don't create a duplicate
        last_version = -1
        for run in session.query(ReductionRun).filter_by(experiment=reduction_run.experiment,
                                                         run_number=reduction_run.run_number).all():
            last_version = max(last_version, run.run_version)

        # get the script to use:
        script_text = script if script is not None else reduction_run.script

        # create the run object and save it
        new_job = ReductionRun(run_number=reduction_run.run_number,
                               run_version=last_version + 1,
                               run_name="",
                               experiment=reduction_run.experiment,
                               instrument=reduction_run.instrument,
                               script=script_text,
                               status=StatusUtils().get_queued(),
                               created=datetime.datetime.now(),
                               last_updated=datetime.datetime.now(),
                               message="",
                               started_by=username,
                               cancel=0,
                               hidden_in_failviewer=0,
                               admin_log="",
                               reduction_log=""
                               )

        try:
            session.add(new_job)
            session.commit()

            reduction_run.retry_run = new_job
            reduction_run.retry_when = datetime.datetime.now() + datetime.timedelta(seconds=delay if delay else 0)
            session.add(new_job)
            session.commit()

            data_locations = session.query(DataLocation).filter_by(reduction_run_id=reduction_run.id).all()

            # copy the previous data locations
            for data_location in data_locations:
                new_data_location = DataLocation(file_path=data_location.file_path, reduction_run=new_job)
                session.add(new_data_location)
                session.commit()

            if variables is not None:
                # associate the variables with the new run
                for var in variables:
                    var.reduction_run = new_job
                    session.add(var)
                    session.commit()
            else:
                # provide variables if they aren't already
                InstrumentVariablesUtils().create_variables_for_run(new_job)

            return new_job

        except:
            session.delete(new_job)
            session.commit()
            raise

    @staticmethod
    def get_script_and_arguments(reduction_run):
        """
        Fetch the reduction script from the given run and return it as a string, along with a dictionary of arguments.
        """
        script = reduction_run.script
        run_variables = (session.query(RunJoin).filter_by(reduction_run=reduction_run)).all()

        standard_vars, advanced_vars = {}, {}
        for variables in run_variables:
            value = VariableUtils().convert_variable_to_type(variables.value, variables.type)
            if variables.is_advanced:
                advanced_vars[variables.name] = value
            else:
                standard_vars[variables.name] = value

        arguments = {'standard_vars': standard_vars, 'advanced_vars': advanced_vars}

        return script, arguments
