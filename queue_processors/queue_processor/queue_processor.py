# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
This module deals with the updating of the database backend.
It consumes messages from the queues and then updates the reduction run status in the database.
"""
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
import datetime
import logging.config
import sys
import traceback

from model.message.job import Message

# pylint: disable=cyclic-import
from queue_processors.queue_processor.queueproc_utils.messaging_utils import MessagingUtils
from queue_processors.queue_processor.queueproc_utils.instrument_variable_utils \
    import InstrumentVariablesUtils
from queue_processors.queue_processor.queueproc_utils.status_utils import StatusUtils
from queue_processors.queue_processor.queueproc_utils.reduction_run_utils import ReductionRunUtils
# pylint: disable=import-error, no-name-in-module
from queue_processors.queue_processor.settings import LOGGING

from utils.clients.queue_client import QueueClient
from utils.settings import ACTIVEMQ_SETTINGS

from model.database import access as db_access

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")  # pylint: disable=invalid-name


def is_valid_rb(rb_number):
    """
    Detects if the RB number is valid e.g. (above 0 and not a string)
    :param rb_number:
    :return: An error message if one is generated or None if the RB is valid
    """
    try:
        rb_number = int(rb_number)
        if rb_number > 0:
            return None
        return "RB Number is less than or equal to 0"
    except ValueError:
        return "RB Number is a string"


class Listener:
    """ Listener class that is used to consume messages from ActiveMQ. """
    def __init__(self, client):
        """ Initialise listener. """
        self._client = client
        self.message = Message()
        self._priority = ''

    def on_message(self, headers, message):
        """ This method is where consumed messages are dealt with. It will consume a message. """
        destination = headers["destination"]
        self._priority = headers["priority"]
        logger.info("Destination: %s Priority: %s", destination, self._priority)
        # Load the JSON message and header into dictionaries
        try:
            if isinstance(message, Message):
                self.message = message
            else:
                self.message.populate(message)
        except ValueError:
            logger.error("Could not decode message from %s", destination)
            logger.error(sys.exc_info()[1])
            return
        try:
            if destination == '/queue/DataReady':
                self.data_ready()
            elif destination == '/queue/ReductionStarted':
                self.reduction_started()
            elif destination == '/queue/ReductionComplete':
                self.reduction_complete()
            elif destination == '/queue/ReductionError':
                self.reduction_error()
            elif destination == '/queue/ReductionSkipped':
                self.reduction_skipped()
            else:
                logger.warning("Recieved a message on an unknown topic '%s'", destination)
        except Exception as exp:  # pylint: disable=broad-except
            logger.error("UNCAUGHT ERROR: %s - %s", type(exp).__name__, str(exp))
            logger.error(traceback.format_exc())

    def data_ready(self):
        """
        Called when destination queue was data_ready.
        Updates the reduction run in the database.
        """
        run_no = str(self.message.run_number)
        instrument_name = str(self.message.instrument)
        rb_number = self.message.rb_number

        logger.info("Data ready for processing run %s on %s", run_no, instrument_name)

        # Check if the instrument is active or not in the MySQL database
        instrument = db_access.get_instrument(instrument_name, create=True)

        # Activate the instrument if it is currently set to inactive
        if not instrument.is_active:
            logger.info("Activating %s", instrument_name)
            instrument.is_active = 1
            db_access.save_record(instrument)

        if instrument.is_paused:
            status = StatusUtils().get_skipped()
        else:
            status = StatusUtils().get_queued()

        # If there has already been an autoreduction job for this run, we need to know it so we can
        # increase the version by 1 for this job. However, if not then we will set it to -1 which
        # will be incremented to 0
        model = db_access.start_database().data_model
        last_run = model.ReductionRun.objects \
            .filter(run_number=run_no) \
            .order_by('-run_version') \
            .first()
        if last_run is not None:
            highest_version = last_run.run_version
        else:
            highest_version = -1
        run_version = highest_version + 1

        # Search for the experiment, if it doesn't exist then add it
        experiment = db_access.get_experiment(rb_number, create=True)

        # Get the script text for the current instrument. If the script text is null then send to
        # error queue
        script_text = InstrumentVariablesUtils().get_current_script_text(instrument.name)[0]
        if script_text is None:
            self.reduction_error()
            return

        # Make the new reduction run with the information collected so far and add it into the
        # database
        reduction_run = model.ReductionRun(run_number=self.message.run_number,
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
                                           started_by=self.message.started_by)
        db_access.save_record(reduction_run)

        # Set our run_version to be the one we have just calculated
        self.message.run_version = reduction_run.run_version  # pylint: disable=no-member

        # Create a new data location entry which has a foreign key linking it to the current
        # reduction run. The file path itself will point to a datafile
        # (e.g. "\isis\inst$\NDXWISH\Instrument\data\cycle_17_1\WISH00038774.nxs")
        model = db_access.start_database().data_model
        data_location = model.DataLocation(file_path=self.message.data,
                                           reduction_run_id=reduction_run.id)
        db_access.save_record(data_location)

        # We now need to create all of the variables for the run such that the script can run
        # through in the desired way
        logger.info('Creating variables for run')
        variables = InstrumentVariablesUtils().create_variables_for_run(reduction_run)
        if not variables:
            logger.warning("No instrument variables found on %s for run %s",
                           instrument.name,
                           self.message.run_number)

        logger.info('Getting script and arguments')
        reduction_script, arguments = ReductionRunUtils().get_script_and_arguments(reduction_run)
        self.message.reduction_script = reduction_script
        self.message.reduction_arguments = arguments

        # Make sure the RB number is valid
        error_message = is_valid_rb(rb_number)
        if error_message:
            self._construct_and_send_skipped(rb_number, reason=error_message)
            return

        if instrument.is_paused:
            logger.info("Run %s has been skipped", self.message.run_number)
        else:
            self._client.send('/queue/ReductionPending', self.message,
                              priority=self._priority)
            logger.info("Run %s ready for reduction", self.message.run_number)

    # note: Why does this take arguments and not just take from the message attribs
    def _construct_and_send_skipped(self, rb_number, reason):
        """
        Construct a message and send to the skipped reduction queue
        :param rb_number: The RB Number associated with the reduction job
        :param reason: The error that caused the run to be skipped
        """
        logger.warning("Skipping non-integer RB number: %s", rb_number)
        msg = 'Reduction Skipped: {}. Assuming run number to be ' \
              'a calibration run.'.format(reason)
        self.message.message = msg
        skipped_queue = ACTIVEMQ_SETTINGS.reduction_skipped
        self._client.send(skipped_queue, self.message,
                          priority=self._priority)

    def reduction_started(self):
        """
        Called when destination queue was reduction_started.
        Updates the run as started in the database.
        """
        logger.info("Run %s has started reduction", self.message.run_number)

        reduction_run = self.find_run()

        if reduction_run:
            if str(reduction_run.status.value) == "Error" or str(
                    reduction_run.status.value) == "Queued":
                reduction_run.status = StatusUtils().get_processing()
                reduction_run.started = datetime.datetime.utcnow()
                db_access.save_record(reduction_run)
            else:
                logger.error("An invalid attempt to re-start a reduction run was captured. "
                             "Experiment: %s, "
                             "Run Number: %s, "
                             "Run Version %s",
                             self.message.rb_number,
                             self.message.run_number,
                             self.message.run_version)
        else:
            logger.error("A reduction run started that wasn't found in the database. "
                         "Experiment: %s, "
                         "Run Number: %s, "
                         "Run Version %s",
                         self.message.rb_number,
                         self.message.run_number,
                         self.message.run_version)

    def reduction_complete(self):
        """
        Called when the destination queue was reduction_complete
        Updates the run as complete in the database.
        """
        # pylint: disable=too-many-nested-blocks
        try:
            logger.info("Run %s has completed reduction", self.message.run_number)
            reduction_run = self.find_run()

            if reduction_run:
                if reduction_run.status.value == "Processing":
                    reduction_run.status = StatusUtils().get_completed()
                    reduction_run.finished = datetime.datetime.utcnow()
                    reduction_run.message = self.message.message
                    reduction_run.reduction_log = self.message.reduction_log
                    reduction_run.admin_log = self.message.admin_log

                    if self.message.reduction_data is not None:
                        for location in self.message.reduction_data:
                            model = db_access.start_database().data_model
                            reduction_location = model \
                                .ReductionLocation(file_path=location,
                                                   reduction_run=reduction_run)
                            db_access.save_record(reduction_location)
                    db_access.save_record(reduction_run)

                else:
                    logger.error("An invalid attempt to complete a reduction run that wasn't "
                                 "processing has been captured. "
                                 "Experiment: %s, "
                                 "Run Number: %s, "
                                 "Run Version %s",
                                 self.message.rb_number,
                                 self.message.run_number,
                                 self.message.run_version)
            else:
                logger.error("A reduction run completed that wasn't found in the database. "
                             "Experiment: %s, Run Number:%s,"
                             " Run Version %s",
                             self.message.rb_number,
                             self.message.run_number,
                             self.message.run_version)

        except BaseException as exp:
            logger.error("Error: %s", exp)

    def reduction_skipped(self):
        """
        Called when the destination was reduction skipped
        Updates the run to Skipped status in database
        Will NOT attempt re-run
        """
        if self.message.message is not None:
            logger.info("Run %s has been skipped - %s",
                        self.message.run_number,
                        self.message.message)
        else:
            logger.info("Run %s has been skipped - No error message was found",
                        self.message.run_number)

        reduction_run = self.find_run()
        if not reduction_run:
            logger.error("A reduction run that was skipped, could not be found in the database. "
                         "Experiment: %s, "
                         "Run Number: %s, "
                         "Run Version %s",
                         self.message.rb_number,
                         self.message.run_number,
                         self.message.run_version)
            return

        reduction_run.status = StatusUtils().get_skipped()
        reduction_run.finished = datetime.datetime.utcnow()
        reduction_run.message = self.message.message
        reduction_run.reduction_log = self.message.reduction_log
        reduction_run.admin_log = self.message.admin_log

        db_access.save_record(reduction_run)

    def reduction_error(self):
        """
        Called when the destination was reduction_error.
        Updates the run as complete in the database.
        """
        if self.message.message is not None:
            logger.info("Run %s has encountered an error - %s",
                        self.message.run_number,
                        self.message.message)
        else:
            logger.info("Run %s has encountered an error - No error message was found",
                        self.message.run_number)

        reduction_run = self.find_run()

        if not reduction_run:
            logger.error("A reduction run that caused an error wasn't found in the database. "
                         "Experiment: %s, "
                         "Run Number: %s, "
                         "Run Version %s",
                         self.message.rb_number,
                         self.message.run_number,
                         self.message.run_version)
            return

        reduction_run.status = StatusUtils().get_error()
        reduction_run.finished = datetime.datetime.utcnow()
        reduction_run.message = self.message.message
        reduction_run.reduction_log = self.message.reduction_log
        reduction_run.admin_log = self.message.admin_log
        db_access.save_record(reduction_run)

        if self.message.retry_in is not None:
            experiment = db_access.get_experiment(self.message.rb_number)
            model = db_access.start_database().data_model
            previous_runs = model.ReductionRun \
                .filter(run_number=self.message.run_number) \
                .filter(experiment=experiment)
            max_version = -1
            for previous_run in previous_runs:
                current_version = previous_run.run_version
                if current_version > max_version:
                    max_version = current_version

            # If we have already tried more than 5 times, we want to give up and we don't want
            # to retry the run
            if max_version <= 4:
                self.retry_run(
                    self.message.started_by,
                    reduction_run,
                    self.message.retry_in)
            else:
                # Need to delete the retry_in entry from the dictionary so that the front end
                # doesn't report a false retry instance.
                self.message.retry_in = None

    def find_run(self):
        """ Find a reduction run in the database. """
        experiment = db_access.get_experiment(self.message.rb_number)
        if not experiment:
            logger.error("Unable to find experiment %s", self.message.rb_number)
            return None

        logger.info('Finding a run with an experiment ID %s, run number %s and run version %s',
                    experiment.id,
                    int(self.message.run_number),
                    int(self.message.run_version))
        model = db_access.start_database().data_model
        reduction_run = model.ReductionRun.objects \
            .filter(experiment_id=experiment.id) \
            .filter(run_number=int(self.message.run_number)) \
            .filter(run_version=int(self.message.run_version)) \
            .first()
        return reduction_run

    @staticmethod
    def retry_run(user_id, reduction_run, retry_in):
        """ Retry a reduction run. """
        if reduction_run.cancel:
            logger.info("Cancelling run retry")
            return

        logger.info("Retrying run in %i seconds", retry_in)

        new_job = ReductionRunUtils().create_retry_run(
            user_id=user_id,
            reduction_run=reduction_run,
            delay=retry_in)
        try:
            #  Seconds to Milliseconds
            MessagingUtils().send_pending(new_job, delay=retry_in * 1000)
        except Exception as exp:
            logger.error(traceback.format_exc())
            raise exp


def setup_connection(consumer_name):
    """ Starts the ActiveMQ connection and registers the event listener """
    logger.info("Starting autoreduce queue connection")
    # Connect to ActiveMQ
    activemq_client = QueueClient()
    activemq_client.connect()

    # Register the event listener
    listener = Listener(activemq_client)

    # Subscribe to queues
    activemq_client.subscribe_autoreduce(consumer_name, listener)


def main():
    """ Main method. """
    setup_connection('queue_processor')


if __name__ == '__main__':
    main()
