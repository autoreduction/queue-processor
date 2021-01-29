# ############################################################################
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################
"""
This modules handles an incoming message from the queue processor
and takes appropriate action(s) based on the message contents.

For example, this may include shuffling the message to another queue,
update relevant DB fields or logging out the status.
"""
import datetime
import logging
from queue_processors.queue_processor.queueproc_utils.variable_utils import VariableUtils
from typing import Optional
from django.db import transaction

import model.database.records as db_records
from model.database import access as db_access
from model.message.message import Message

from queue_processors.queue_processor.reduction_runner.reduction_process_manager import ReductionProcessManager
from queue_processors.queue_processor.reduction_runner.reduction_service import ReductionScript
from queue_processors.queue_processor.queueproc_utils.instrument_variable_utils import InstrumentVariablesUtils
from queue_processors.queue_processor.queueproc_utils.status_utils import StatusUtils


class HandleMessage:
    """
    Handles messages from the queue client and forwards through various
    stages depending on the message contents.
    """

    # We cannot type hint queue listener without introducing a circular dep.
    def __init__(self, queue_listener):
        self._client = queue_listener
        self.status = StatusUtils()
        self.instrument_variable = InstrumentVariablesUtils()

        self._logger = logging.getLogger("handle_queue_message")

        self.database = db_access.start_database()
        self.data_model = self.database.data_model

    def data_ready(self, message: Message):
        """
        Called when destination queue was data_ready.
        Updates the reduction run in the database.

        When we DO NO PROCESSING:
        - If rb number isn't an integer, or isn't a 7 digit integer
        - If instrument is paused
        - If there is no reduce.py
        """
        self._logger.info("Data ready for processing run %s on %s", message.run_number, message.instrument)

        try:
            reduction_run, message, instrument = self.create_run_records(message)
        except Exception as err:
            # failed to even create the reduction run object - can't reacover from this
            self._logger.error("Encountered error in transaction to create ReductionRun and related records, error: %s",
                               str(err))
            raise

        try:
            message = self.create_run_variables(reduction_run, message, instrument)
            self.send_message_onwards(reduction_run, message, instrument)
        except Exception as err:
            self._handle_error(reduction_run, message, err)
            raise

    def _handle_error(self, reduction_run, message, err):
        # couldn't save the state in the database properly - mark the run as errored
        err_msg = f"Encountered error in transaction to save RunVariables, error: {str(err)}"
        self._logger.error(err_msg)
        message.message = err_msg
        self.reduction_error(reduction_run, message)

    @transaction.atomic
    def create_run_records(self, message: Message):
        """
        Creates or gets the necessary records to construct a ReductionRun
        """
        # This must be done before looking up the run version to make sure the record exists
        experiment = db_access.get_experiment(message.rb_number)
        run_version = db_access.find_highest_run_version(run_number=str(message.run_number), experiment=experiment)
        message.run_version = run_version

        instrument = db_access.get_instrument(str(message.instrument))
        script = ReductionScript(instrument.name)
        script_text = script.text()
        # Make the new reduction run with the information collected so far
        reduction_run = db_records.create_reduction_run_record(experiment=experiment,
                                                               instrument=instrument,
                                                               message=message,
                                                               run_version=run_version,
                                                               script_text=script_text,
                                                               status=self.status.get_queued())
        reduction_run.save()

        # Create a new data location entry which has a foreign key linking it to the current
        # reduction run. The file path itself will point to a datafile
        # (e.g. "/isis/inst$/NDXWISH/Instrument/data/cycle_17_1/WISH00038774.nxs")
        # TODO figure out whether we only use this for showing the ReductionLocation line in the web app
        # TODO this should probably be part of the ReductionRun rather than the huge script text!
        data_location = self.data_model.DataLocation(file_path=message.data, reduction_run_id=reduction_run.id)
        data_location.save()

        return reduction_run, message, instrument

    def create_run_variables(self, reduction_run, message: Message, instrument):
        """
        Creates the RunVariables for this ReductionRun
        """
        # Create all of the variables for the run that are described in it's reduce_vars.py
        self._logger.info('Creating variables for run')
        variables = self.instrument_variable.create_run_variables(reduction_run)
        if not variables:
            self._logger.warning("No instrument variables found on %s for run %s", instrument.name, message.run_number)

        self._logger.info('Getting script and arguments')
        message.reduction_arguments = self.get_script_arguments(variables)
        return message

    def send_message_onwards(self, reduction_run, message: Message, instrument):
        """
        Sends the message onwards, either for processing, if validation is OK and instrument isn't paused
        or skips it if either of those is true.
        """
        # activate instrument if script was found
        skip_reason = self.should_skip(reduction_run, message, instrument)
        if skip_reason is not None:
            message.message = skip_reason
            self.reduction_skipped(reduction_run, message)
        else:
            instrument = self.activate_db_inst(instrument)
            self.do_reduction(reduction_run, message)

    @staticmethod
    def should_skip(reduction_run, message: Message, instrument) -> Optional[str]:
        """
        Determines whether the processing should be skippped.

        The run will be skipped if the message validation fails or if the instrument is paused
        """
        if reduction_run.script == "":
            return "Script text for current instrument is empty"
        try:
            message.validate("/queue/DataReady")
        except RuntimeError as validation_err:
            return f"Validation error from handler: {str(validation_err)}"

        if instrument.is_paused:
            return f"Run {message.run_number} has been skipped because the instrument {instrument.name} is paused"

        return None

    def do_reduction(self, reduction_run, message: Message):
        """
        Handovers to the ReductionProcessManager to actually run the reduction process.
        Handles the outcome from the run.
        """
        reduction_process_manager = ReductionProcessManager(message)
        self.reduction_started(reduction_run, message)
        message = reduction_process_manager.run()
        if message.message is not None:
            self.reduction_error(reduction_run, message)
        else:
            self.reduction_complete(reduction_run, message)

    def activate_db_inst(self, instrument):
        """
        Gets the DB instrument record from the database, if one is not
        found it instead creates and saves the record to the DB, then
        returns it.
        """
        # Activate the instrument if it is currently set to inactive
        if not instrument.is_active:
            self._logger.info("Activating %s", instrument.name)
            instrument.is_active = 1
            instrument.save()
        return instrument

    def reduction_started(self, reduction_run, message: Message):
        """
        Called when destination queue was reduction_started.
        Updates the run as started in the database.
        """
        self._logger.info("Run %s has started reduction", message.run_number)
        reduction_run.status = self.status.get_processing()
        reduction_run.started = datetime.datetime.utcnow()
        reduction_run.save()

    @transaction.atomic
    def reduction_complete(self, reduction_run, message: Message):
        """
        Called when the destination queue was reduction_complete
        Updates the run as complete in the database.
        """
        self._logger.info("Run %s has completed reduction", message.run_number)

        self._common_reduction_run_update(reduction_run, self.status.get_completed(), message)

        if message.reduction_data is not None:
            reduction_location = self.data_model.ReductionLocation(file_path=message.reduction_data,
                                                                   reduction_run=reduction_run)
            reduction_location.save()
        reduction_run.save()

    def reduction_skipped(self, reduction_run, message: Message):
        """
        Called when the destination was reduction skipped
        Updates the run to Skipped status in database
        Will NOT attempt re-run
        """
        if message.message is not None:
            self._logger.info("Run %s has been skipped - %s", message.run_number, message.message)
        else:
            self._logger.info("Run %s has been skipped - No error message was found", message.run_number)

        self._common_reduction_run_update(reduction_run, self.status.get_skipped(), message)
        reduction_run.save()

    def reduction_error(self, reduction_run, message: Message):
        """
        Called when the destination was reduction_error.
        Updates the run as complete in the database.
        """
        if message.message:
            self._logger.info("Run %s has encountered an error - %s", message.run_number, message.message)
        else:
            self._logger.info("Run %s has encountered an error - No error message was found", message.run_number)

        self._common_reduction_run_update(reduction_run, self.status.get_error(), message)
        reduction_run.save()

    @staticmethod
    def _common_reduction_run_update(reduction_run, status, message):
        reduction_run.status = status
        reduction_run.finished = datetime.datetime.utcnow()
        reduction_run.message = message.message
        reduction_run.reduction_log = message.reduction_log
        reduction_run.admin_log = message.admin_log

    @staticmethod
    def get_script_arguments(run_variables):
        """
        Converts the RunVariables that have been created into Python kwargs which can
        be passed as the script parameters at runtime.
        """
        standard_vars, advanced_vars = {}, {}
        for run_variable in run_variables:
            variable = run_variable.variable
            value = VariableUtils.convert_variable_to_type(variable.value, variable.type)
            if variable.is_advanced:
                advanced_vars[variable.name] = value
            else:
                standard_vars[variable.name] = value

        arguments = {'standard_vars': standard_vars, 'advanced_vars': advanced_vars}

        return arguments
