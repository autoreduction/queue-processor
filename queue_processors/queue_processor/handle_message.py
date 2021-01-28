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

import model.database.records as db_records
from django.db import IntegrityError, transaction
from model.database import access as db_access
from model.message.message import Message
from model.message.validation.validators import validate_rb_number

from ._utils_classes import _UtilsClasses
from .handling_exceptions import InvalidStateException
from .reduction_runner.reduction_process_manager import ReductionProcessManager
from .reduction_runner.reduction_service import ReductionScript


class HandleMessage:
    """
    Handles messages from the queue client and forwards through various
    stages depending on the message contents.
    """

    # We cannot type hint queue listener without introducing a circular dep.
    def __init__(self, queue_listener):
        self._client = queue_listener
        self._utils = _UtilsClasses()

        self._logger = logging.getLogger("handle_queue_message")

        self._cached_db = None
        self._cached_data_model = None

    @property
    def _database(self):
        """
        Gets a handle to the database, starting it if required
        """
        if not self._cached_db:
            self._cached_db = db_access.start_database()
        return self._cached_db

    @property
    def data_model(self):
        """
        Gets a handle to the data model from the database
        """
        if not self._cached_data_model:
            self._cached_data_model = self._database.data_model
        return self._cached_data_model

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

        # This must be done before looking up the run version to make sure the record exists
        experiment = db_access.get_experiment(message.rb_number)
        run_version = db_access.find_highest_run_version(run_number=str(message.run_number), experiment=experiment)
        message.run_version = run_version

        instrument = db_access.get_instrument(str(message.instrument))
        script = ReductionScript(instrument.name)
        script_text = script.text()
        # Make the new reduction run with the information collected so far
        # and add it into the database
        reduction_run = db_records.create_reduction_run_record(experiment=experiment,
                                                               instrument=instrument,
                                                               message=message,
                                                               run_version=run_version,
                                                               script_text=script_text,
                                                               status=self._utils.status.get_queued())
        # if the script text is empty then send to error queue
        if script_text == "":
            message.message = "Script text for current instrument is null"
            self.reduction_error(reduction_run, message)
            raise InvalidStateException("Script text for current instrument is null")

        # activate instrument if script was found
        instrument = self.activate_db_inst(instrument)
        self.safe_save(reduction_run)

        # Create a new data location entry which has a foreign key linking it to the current
        # reduction run. The file path itself will point to a datafile
        # (e.g. "/isis/inst$/NDXWISH/Instrument/data/cycle_17_1/WISH00038774.nxs")
        # TODO figure out whether we only use this for showing the ReductionLocation line in the web app
        # TODO this should probably be part of the ReductionRun rather than the huge script text!
        data_location = self.data_model.DataLocation(file_path=message.data, reduction_run_id=reduction_run.id)
        self.safe_save(data_location)

        # Create all of the variables for the run that are described in it's reduce_vars.py
        self._logger.info('Creating variables for run')
        try:
            variables = self._utils.instrument_variable.create_run_variables(reduction_run)
            if not variables:
                # TODO is there a way to show some warning on the reduction run view page itself?
                # at the moment this is a developer only warning
                self._logger.warning("No instrument variables found on %s for run %s", instrument.name,
                                     message.run_number)
        except IntegrityError as err:
            # couldn't save the state in the database properly - this is a developer error
            self._logger.error("Encountered error in transaction to save RunVariables, error: %s", str(err))
            raise

        self._logger.info('Getting script and arguments')
        arguments = self._utils.reduction_run.get_script_arguments(variables)
        message.reduction_script = reduction_run.script
        message.reduction_arguments = arguments

        return self.send_message_onwards(reduction_run, message, instrument)

    def safe_save(self, obj):
        """
        Save objects with a transaction, if an integrity error is encountered the handling
        raises the exception and stops processing
        """
        try:
            with transaction.atomic():
                return obj.save()
        except IntegrityError as err:
            # couldn't save the state in the database
            self._logger.error("Encountered error in transaction, error: %s", str(err))
            raise

    def send_message_onwards(self, reduction_run, message: Message, instrument):
        """
        Sends the message onwards, either for processing, if validation is OK and instrument isn't paused
        or skips it if either of those is true.
        """
        try:
            message.validate("/queue/DataReady")
        except RuntimeError as validation_err:
            self._logger.error("Validation error from handler: %s", str(validation_err))
            self.reduction_skipped(reduction_run, message)
            return

        if instrument.is_paused:
            self._logger.info("Run %s has been skipped because the instrument %s is paused", message.run_number,
                              instrument.name)
            self.reduction_skipped(reduction_run, message)
        else:
            # success branch
            self._logger.info("Run %s ready for reduction", message.run_number)
            self.do_reduction(reduction_run, message)

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
        reduction_run.status = self._utils.status.get_processing()
        reduction_run.started = datetime.datetime.utcnow()
        self.safe_save(reduction_run)

    @transaction.atomic
    def reduction_complete(self, reduction_run, message: Message):
        """
        Called when the destination queue was reduction_complete
        Updates the run as complete in the database.
        """
        self._logger.info("Run %s has completed reduction", message.run_number)

        self._common_reduction_run_update(reduction_run, self._utils.status.get_completed(), message)

        if message.reduction_data is not None:
            for location in message.reduction_data:
                reduction_location = self.data_model.ReductionLocation(file_path=location, reduction_run=reduction_run)
                self.safe_save(reduction_location)
        self.safe_save(reduction_run)

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

        self._common_reduction_run_update(reduction_run, self._utils.status.get_skipped(), message)
        self.safe_save(reduction_run)

    def reduction_error(self, reduction_run, message: Message):
        """
        Called when the destination was reduction_error.
        Updates the run as complete in the database.
        """
        if message.message:
            self._logger.info("Run %s has encountered an error - %s", message.run_number, message.message)
        else:
            self._logger.info("Run %s has encountered an error - No error message was found", message.run_number)

        self._common_reduction_run_update(reduction_run, self._utils.status.get_error(), message)
        self.safe_save(reduction_run)

    @staticmethod
    def _common_reduction_run_update(reduction_run, status, message):
        reduction_run.status = status
        reduction_run.finished = datetime.datetime.utcnow()
        reduction_run.message = message.message
        reduction_run.reduction_log = message.reduction_log
        reduction_run.admin_log = message.admin_log
