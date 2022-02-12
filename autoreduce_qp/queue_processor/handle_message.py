# ############################################################################ #
# Autoreduction Repository :
# https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################ #
"""
Handle an incoming message from the queue processor and take appropriate
action(s) based on the message contents.

This may include shuffling the message to another queue, updating relevant DB
fields, or logging of the status.
"""
import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone

from autoreduce_db.reduction_viewer.models import (Experiment, Instrument, ReductionLocation, ReductionRun, Status,
                                                   Software)
from autoreduce_utils.message.message import Message
from autoreduce_qp.model.database import access as db_access
from autoreduce_qp.model.database import records
from autoreduce_qp.queue_processor.reduction.process_manager import ReductionProcessManager


class HandleMessage:
    """
    Handle messages from the queue client and forward through the various stages
    depending on the message contents.
    """

    def __init__(self):
        self._logger = logging.getLogger(__package__)

    def data_ready(self, message: Message):
        """
        Update the reduction run in the database. This is called when
        destination queue was data_ready.

        No processing occurs when:
        - RB number isn't a 7 digit integer.
        - Instrument is paused.
        - There is no reduce.py.
        """
        self._logger.info("Data ready for processing run %s on %s. Software: %s. Version %s ", message.run_number,
                          message.instrument, message.software["name"], message.software["version"])

        try:
            reduction_run, message, instrument, software = self.create_run_records(message)
        except Exception as err:
            # Failed to create the reduction run object - unrecoverable
            self._logger.error("Encountered error in transaction to create ReductionRun and related records, error: %s",
                               str(err))
            raise

        try:
            self.send_message_onwards(reduction_run, message, instrument, software)
        except Exception as err:
            self._handle_error(reduction_run, message, err)
            raise

        return reduction_run, message

    def _handle_error(self, reduction_run: ReductionRun, message: Message, err: Exception):
        """
        Couldn't save the state in the database properly - mark the run as
        errored.
        """
        err_msg = "Encountered error when saving run variables"
        message.message = err_msg
        self._logger.error("%s\n%s", err_msg, str(err))
        message.reduction_log = str(err)
        self.reduction_error(reduction_run, message)

    def create_run_records(self, message: Message):
        """
        Create or get the necessary records to construct a ReductionRun. This
        must be done before looking up the run version to make sure the
        experiment record exists!
        """
        rb_number = self.normalise_rb_number(message.rb_number)
        experiment = db_access.get_experiment(rb_number)
        run_version = db_access.find_highest_run_version(experiment, run_number=message.run_number)
        instrument = db_access.get_instrument(str(message.instrument))
        software = db_access.get_software(message.software.get("name"), message.software.get("version"))
        return self.do_create_reduction_record(message, experiment, instrument, run_version, software)

    @staticmethod
    @transaction.atomic
    def do_create_reduction_record(message: Message, experiment: Experiment, instrument: Instrument, run_version: int,
                                   software: Software):
        """Create the reduction record."""
        # Make the new reduction run with the information collected so far
        reduction_run, message = records.create_reduction_run_record(experiment=experiment,
                                                                     instrument=instrument,
                                                                     message=message,
                                                                     run_version=run_version,
                                                                     software=software,
                                                                     status=Status.get_queued())

        return reduction_run, message, instrument, software

    def send_message_onwards(self, reduction_run: ReductionRun, message: Message, instrument: Instrument,
                             software: Software):
        """
        Send the message onwards, either for processing, if validation is OK
        and instrument isn't paused, otherwiese skips if either of those is
        true.
        """
        # Activate instrument if script was found
        skip_reason = self.find_reason_to_skip_run(reduction_run, message, instrument)
        if skip_reason is not None:
            message.message = skip_reason
            message.reduction_log = skip_reason
            self.reduction_skipped(reduction_run, message)
        elif message.message:
            self.reduction_error(reduction_run, message)
        else:
            self.activate_db_inst(instrument)
            self.do_reduction(reduction_run, message, software)

    @staticmethod
    def find_reason_to_skip_run(reduction_run: ReductionRun, message: Message, instrument) -> Optional[str]:
        """
        Determine whether the processing should be skippped. The run will be
        skipped if the message validation fails or if the instrument is paused.
        """
        if reduction_run.script.text == "":
            return "Script text for current instrument is empty"
        try:
            message.validate("data_ready")
        except RuntimeError as validation_err:
            return f"Validation error from handler: {validation_err}"

        if not instrument.is_active:
            return f"Run {message.run_number} has been skipped because the instrument {instrument.name} is inactive"

        if instrument.is_paused:
            return f"Run {message.run_number} has been skipped because the instrument {instrument.name} is paused"

        return None

    def do_reduction(self, reduction_run: ReductionRun, message: Message, software: Software):
        """
        Handover to the ReductionProcessManager to actually run the reduction
        process and handle the outcome from the run.
        """
        if reduction_run.batch_run:
            run_name = f"batch-{reduction_run.run_numbers.first()}-{reduction_run.run_numbers.last()}"
        else:
            run_name = f"{reduction_run.run_number}"

        reduction_process_manager = ReductionProcessManager(message, run_name, software)
        self.reduction_started(reduction_run, message)

        output_message = reduction_process_manager.run()
        if output_message.message is not None:
            self.reduction_error(reduction_run, output_message)
        else:
            self.reduction_complete(reduction_run, output_message)

    def activate_db_inst(self, instrument: Instrument):
        """
        Get the DB instrument record from the database, if one is not found,
        create and save the record to the DB, then return it.
        """
        # Activate the instrument if it is currently set to inactive
        if not instrument.is_active:
            self._logger.info("Activating %s", instrument.name)
            instrument.is_active = 1
            instrument.save()

        return instrument

    def reduction_started(self, reduction_run: ReductionRun, message: Message):
        """
        Update the run as 'started' / 'processing' in the database. This is
        called when the run is ready to start.
        """
        self._logger.info("Run %s has started reduction", message.run_number)
        reduction_run.status = Status.get_processing()
        reduction_run.started = timezone.now()
        reduction_run.save()

    @transaction.atomic
    def reduction_complete(self, reduction_run: ReductionRun, message: Message):
        """
        Update the run as 'completed' in the database. This is called when the
        run has completed.
        """
        self._logger.info("Run %s has completed reduction", message.run_number)
        self._common_reduction_run_update(reduction_run, Status.get_completed(), message)
        reduction_run.save()

        if message.reduction_data is not None:
            reduction_location = ReductionLocation(file_path=message.reduction_data, reduction_run=reduction_run)
            reduction_location.save()

    def reduction_skipped(self, reduction_run: ReductionRun, message: Message):
        """
        Update the run status to 'skipped' in the database. This is called when
        there was a reason to skip the run. Will NOT attempt re-run.
        """
        if message.message is not None:
            self._logger.info("Run %s has been skipped - %s", message.run_number, message.message)
        else:
            self._logger.info("Run %s has been skipped - No error message was found", message.run_number)

        self._common_reduction_run_update(reduction_run, Status.get_skipped(), message)
        reduction_run.save()

    def reduction_error(self, reduction_run: ReductionRun, message: Message):
        """
        Update the run as 'errored' in the database. This is called when the run
        encounters an error.
        """
        if message.message:
            self._logger.info("Run %s has encountered an error - %s", message.run_number, message.message)
        else:
            self._logger.info("Run %s has encountered an error - No error message was found", message.run_number)

        self._common_reduction_run_update(reduction_run, Status.get_error(), message)
        reduction_run.save()

    @staticmethod
    def _common_reduction_run_update(reduction_run: ReductionRun, status: Status, message: Message):
        reduction_run.status = status
        reduction_run.finished = timezone.now()
        reduction_run.message = message.message
        reduction_run.reduction_log = message.reduction_log
        reduction_run.admin_log = message.admin_log

    @staticmethod
    def normalise_rb_number(rb_number) -> int:
        """
        Enforce the RB number to always be an int. If an invalid integer value
        is passed, return 0.
        """
        try:
            return int(rb_number)
        except ValueError:
            return 0
