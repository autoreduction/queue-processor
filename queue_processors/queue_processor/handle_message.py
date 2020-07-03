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
import logging.config
import traceback

from model.database import access as db_access
from model.message.job import Message
from queue_processors.queue_processor._utils_classes import _UtilsClasses
from queue_processors.queue_processor.handling_exceptions import \
    MissingReductionRunRecord, InvalidStateException, MissingExperimentRecord
from queue_processors.queue_processor.settings import LOGGING
from utils.settings import ACTIVEMQ_SETTINGS


def validate_rb_num(rb_number):
    """
    Detects if the RB number is valid e.g. (above 0 and not a string)
    :param rb_number:
    :raises: InvalidStateException If the RB is not valid
    """
    try:
        rb_number = int(rb_number)
    except (ValueError, TypeError):
        raise InvalidStateException(
            f"RB Number: {rb_number} is not a valid int")

    if rb_number <= 0:
        raise InvalidStateException(
            f"RB Number: {rb_number} is less than or equal to 0")


class HandleMessage:
    """
    Handles messages from the queue client and forwards through various
    stages depending on the message contents.
    """
    # We cannot type hint queue listener without introducing a circular dep.
    def __init__(self, queue_listener):
        self._client = queue_listener
        self._utils = _UtilsClasses()

        logging.config.dictConfig(LOGGING)
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
    def _data_model(self):
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
        """
        self._logger.info("Data ready for processing run %s on %s",
                          message.run_number, message.instrument)
        run_no = str(message.run_number)
        instrument = self._get_and_activate_db_inst(message.instrument)

        status = self._utils.status.get_skipped() if instrument.is_paused \
            else self._utils.status.get_queued()

        # This must be done before looking up the run version to make sure
        # the record exists
        experiment = db_access.get_experiment(message.rb_number, create=True)
        run_version = self._get_last_run_version(run_no, experiment=experiment)
        run_version += 1
        message.run_version = run_version

        # Get the script text for the current instrument. If the script text
        # is null then send to
        # error queue
        script_text = self._utils. \
            instrument_variable.get_current_script_text(instrument.name)[0]
        if script_text is None:
            self.reduction_error(message)
            raise InvalidStateException(
                "Script text for current instrument is null")

        # Make the new reduction run with the information collected so far
        # and add it into the database
        reduction_run = self._create_reduction_run_record(
            experiment=experiment, instrument=instrument, message=message,
            run_version=run_version, script_text=script_text, status=status)
        db_access.save_record(reduction_run)

        # Create a new data location entry which has a foreign key linking
        # it to the current
        # reduction run. The file path itself will point to a datafile
        # (e.g. "\isis\inst$\NDXWISH\Instrument\data\cycle_17_1\WISH00038774
        # .nxs")
        data_location = self._data_model.DataLocation(file_path=message.data,
                                                      reduction_run_id=reduction_run.id)
        db_access.save_record(data_location)

        # We now need to create all of the variables for the run such that
        # the script can run
        # through in the desired way
        self._logger.info('Creating variables for run')
        variables = self._utils.instrument_variable.create_variables_for_run(
            reduction_run)
        if not variables:
            self._logger.warning(
                "No instrument variables found on %s for run %s",
                instrument.name, message.run_number)

        self._logger.info('Getting script and arguments')
        reduction_script, arguments = self._utils.reduction_run. \
            get_script_and_arguments(reduction_run)
        message.reduction_script = reduction_script
        message.reduction_arguments = arguments

        # Make sure the RB number is valid
        try:
            validate_rb_num(message.rb_number)
        except InvalidStateException as ex:
            self._construct_and_send_skipped(
                message=message, rb_number=message.rb_number, reason=str(ex))
            raise ex

        if instrument.is_paused:
            self._logger.info("Run %s has been skipped",
                              message.run_number)
        else:
            self._client.send_message('/queue/ReductionPending', message)
            self._logger.info("Run %s ready for reduction",
                              message.run_number)

    # pylint: disable=too-many-arguments
    def _create_reduction_run_record(self, experiment, instrument, message,
                                     run_version, script_text, status):
        """
        Creates an ORM record for the given reduction run and returns
        this record without saving it to the DB
        """
        reduction_run = self._data_model.ReductionRun(
            run_number=message.run_number,
            run_version=run_version,
            run_name='',
            cancel=0,
            hidden_in_failviewer=0,
            admin_log='',
            reduction_log='',
            created=datetime.datetime.utcnow(),
            last_updated=datetime.datetime.utcnow(),
            experiment_id=experiment.id,
            instrument_id=instrument.id,
            status_id=status.id,
            script=script_text,
            started_by=message.started_by)
        return reduction_run

    def _get_last_run_version(self, run_no, experiment):
        """
        Returns the latest run version for the given run number
        and experiment combo. If none is found (i.e. a new reduction)
        -1 is returned to indicate this is a new version
        """
        last_run = self._data_model.ReductionRun.objects \
            .filter(run_number=run_no) \
            .filter(experiment=experiment) \
            .order_by('-run_version') \
            .first()

        # By returning -1 callers can blindly increment the version
        return last_run.run_version if last_run else -1

    def _get_and_activate_db_inst(self, instrument_name):
        """
        Gets the DB instrument record from the database, if one is not
        found it instead creates and saves the record to the DB, then
        returns it.
        """
        # Check if the instrument is active or not in the MySQL database
        instrument = db_access.get_instrument(str(instrument_name),
                                              create=True)
        # Activate the instrument if it is currently set to inactive
        if not instrument.is_active:
            self._logger.info("Activating %s", instrument_name)
            instrument.is_active = 1
            db_access.save_record(instrument)
        return instrument

    # note: Why does this take arguments and not just take from the message
    # attribs
    def _construct_and_send_skipped(self, rb_number, reason, message: Message):
        """
        Construct a message and send to the skipped reduction queue
        :param rb_number: The RB Number associated with the reduction job
        :param reason: The error that caused the run to be skipped
        """
        self._logger.warning("Skipping non-integer RB number: %s", rb_number)
        msg = 'Reduction Skipped: {}. Assuming run number to be ' \
              'a calibration run.'.format(reason)
        message.message = msg
        skipped_queue = ACTIVEMQ_SETTINGS.reduction_skipped
        self._client.send_message(skipped_queue, message)

    def reduction_started(self, message: Message):
        """
        Called when destination queue was reduction_started.
        Updates the run as started in the database.
        """
        self._logger.info("Run %s has started reduction",
                          message.run_number)

        reduction_run = self.find_run(message=message)

        if not reduction_run:
            raise MissingReductionRunRecord(
                rb_number=message.rb_number, run_number=message.run_number,
                run_version=message.run_version)

        if reduction_run.status.value not in ("Error", "Queued"):
            raise InvalidStateException(
                "An invalid attempt to re-start a reduction run was captured."
                f" Experiment: {message.rb_number},"
                f" Run Number: {message.run_number},"
                f" Run Version {message.run_version}")

        reduction_run.status = self._utils.status.get_processing()
        reduction_run.started = datetime.datetime.utcnow()
        db_access.save_record(reduction_run)

    def reduction_complete(self, message: Message):
        """
        Called when the destination queue was reduction_complete
        Updates the run as complete in the database.
        """
        self._logger.info("Run %s has completed reduction", message.run_number)
        reduction_run = self.find_run(message)

        if not reduction_run:
            raise MissingReductionRunRecord(
                rb_number=message.rb_number, run_number=message.run_number,
                run_version=message.run_version)

        if not reduction_run.status.value == "Processing":
            raise InvalidStateException(
                "An invalid attempt to complete a reduction run that wasn't"
                " processing has been captured. "
                f" Experiment: {message.rb_number},"
                f" Run Number: {message.run_number},"
                f" Run Version {message.run_version}")

        reduction_run.status = self._utils.status.get_completed()
        reduction_run.finished = datetime.datetime.utcnow()
        reduction_run.message = message.message
        reduction_run.reduction_log = message.reduction_log
        reduction_run.admin_log = message.admin_log

        if message.reduction_data is not None:
            for location in message.reduction_data:
                model = db_access.start_database().data_model
                reduction_location = model \
                    .ReductionLocation(file_path=location,
                                       reduction_run=reduction_run)
                db_access.save_record(reduction_location)
        db_access.save_record(reduction_run)

    def reduction_skipped(self, message: Message):
        """
        Called when the destination was reduction skipped
        Updates the run to Skipped status in database
        Will NOT attempt re-run
        """
        if message.message is not None:
            self._logger.info("Run %s has been skipped - %s",
                              message.run_number,
                              message.message)
        else:
            self._logger.info(
                "Run %s has been skipped - No error message was found",
                message.run_number)

        reduction_run = self.find_run(message)
        if not reduction_run:
            raise MissingReductionRunRecord(rb_number=message.rb_number,
                                            run_number=message.run_number,
                                            run_version=message.run_version)

        reduction_run.status = self._utils.status.get_skipped()
        reduction_run.finished = datetime.datetime.utcnow()
        reduction_run.message = message.message
        reduction_run.reduction_log = message.reduction_log
        reduction_run.admin_log = message.admin_log

        db_access.save_record(reduction_run)

    def reduction_error(self, message: Message):
        """
        Called when the destination was reduction_error.
        Updates the run as complete in the database.
        """
        if message.message:
            self._logger.info("Run %s has encountered an error - %s",
                              message.run_number, message.message)
        else:
            self._logger.info(
                "Run %s has encountered an error - No error message was found",
                message.run_number)

        reduction_run = self.find_run(message)

        if not reduction_run:
            raise MissingReductionRunRecord(rb_number=message.rb_number,
                                            run_number=message.run_number,
                                            run_version=message.run_version)

        reduction_run.status = self._utils.status.get_error()
        reduction_run.finished = datetime.datetime.utcnow()
        reduction_run.message = message.message
        reduction_run.reduction_log = message.reduction_log
        reduction_run.admin_log = message.admin_log
        db_access.save_record(reduction_run)

        if message.retry_in is not None:
            experiment = db_access.get_experiment(message.rb_number)
            max_version = self._get_last_run_version(run_no=message.run_number,
                                                     experiment=experiment)

            # If we have already tried more than 5 times, we want to give up
            # and we don't want
            # to retry the run
            if max_version <= 4:
                self.retry_run(
                    message.started_by,
                    reduction_run,
                    message.retry_in)
            else:
                # Need to delete the retry_in entry from the dictionary so
                # that the front end
                # doesn't report a false retry instance.
                message.retry_in = None

    def find_run(self, message: Message):
        """ Find a reduction run in the database. """
        experiment = db_access.get_experiment(message.rb_number)
        if not experiment:
            raise MissingExperimentRecord(rb_number=message.rb_number,
                                          run_number=message.run_number,
                                          run_version=message.run_version)
        self._logger.info(
            'Finding a run with an experiment ID %s, run number %s and run '
            'version %s',
            experiment.id,
            int(message.run_number),
            int(message.run_version))
        model = db_access.start_database().data_model
        reduction_run = model.ReductionRun.objects \
            .filter(experiment_id=experiment.id) \
            .filter(run_number=int(message.run_number)) \
            .filter(run_version=int(message.run_version)) \
            .first()
        return reduction_run

    def retry_run(self, user_id, reduction_run, retry_in):
        """ Retry a reduction run. """
        if reduction_run.cancel:
            self._logger.info("Cancelling run retry")
            return

        self._logger.info("Retrying run in %i seconds", retry_in)

        new_job = self._utils.reduction_run.create_retry_run(
            user_id=user_id,
            reduction_run=reduction_run,
            delay=retry_in)
        try:
            #  Seconds to Milliseconds
            self._utils.messaging.send_pending(new_job, delay=retry_in * 1000)
        except Exception as exp:
            self._logger.error(traceback.format_exc())
            raise exp
