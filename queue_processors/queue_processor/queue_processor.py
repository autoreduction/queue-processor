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

import base64
import datetime
import glob
import json
import logging.config
import sys
import traceback

from sqlalchemy import sql

from queue_processors.queue_processor.base import session
from queue_processors.queue_processor.orm_mapping import (ReductionRun, Instrument,
                                                          Status, Experiment,
                                                          DataLocation, ReductionLocation)
# pylint: disable=cyclic-import
from queue_processors.queue_processor.queueproc_utils.messaging_utils import MessagingUtils
from queue_processors.queue_processor.queueproc_utils.instrument_variable_utils \
    import InstrumentVariablesUtils
from queue_processors.queue_processor.queueproc_utils.status_utils import StatusUtils
from queue_processors.queue_processor.queueproc_utils.reduction_run_utils import ReductionRunUtils
# pylint: disable=import-error, no-name-in-module
from queue_processors.queue_processor.settings import LOGGING

from utils.clients.queue_client import QueueClient

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")  # pylint: disable=invalid-name


def is_integer_rb(rb_number):
    """
    Detects string RB numbers. These tend to
    be used by calibration experiments.
    """
    try:
        int(rb_number)
        return True
    except ValueError:
        return False


class Listener:
    """ Listener class that is used to consume messages from ActiveMQ. """
    def __init__(self, client):
        """ Initialise listener. """
        self._client = client
        self._data_dict = {}
        self._priority = ''

    def on_message(self, headers, message):
        """ This method is where consumed messages are dealt with. It will consume a message. """
        destination = headers["destination"]
        self._priority = headers["priority"]
        logger.info("Destination: %s Priority: %s", destination, self._priority)
        # Load the JSON message and header into dictionaries
        try:
            self._data_dict = json.loads(message)
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
        # pylint: disable=too-many-statements
        # Rollback the session to avoid getting caught in a loop where we have uncommitted
        # changes causing problems
        session.rollback()

        # Strip information from the JSON file (_data_dict)
        run_no = str(self._data_dict['run_number'])
        instrument_name = str(self._data_dict['instrument'])
        rb_number = self._data_dict['rb_number']

        # Make sure the RB number is an integer
        if not is_integer_rb(rb_number):
            logger.warning("Skipping non-integer RB number: %s", rb_number)
            return

        logger.info("Data ready for processing run %s on %s", run_no, instrument_name)

        # Check if the instrument is active or not in the MySQL database
        instrument = session.query(Instrument).filter_by(name=instrument_name).first()

        # Add the instrument if it doesn't exist
        if not instrument:
            instrument = Instrument(name=instrument_name, is_active=1, is_paused=0)
            session.add(instrument)
            session.commit()
            instrument = session.query(Instrument).filter_by(name=instrument_name).first()

        # Activate the instrument if it is currently set to inactive
        if not instrument.is_active:
            logger.info("Activating %s", instrument_name)
            instrument.is_active = 1
            session.commit()

        # If the instrument is paused, we need to find the 'Skipped' status
        if instrument.is_paused:
            status = session.query(Status).filter_by(value='Skipped').first()

        # Else we need to find the 'Queued' status number
        else:
            status = session.query(Status).filter_by(value='Queued').first()

        # If there has already been an autoreduction job for this run, we need to know it so we can
        # increase the version by 1 for this job. However, if not then we will set it to -1 which
        # will be incremented to 0
        last_run = session.query(ReductionRun).filter_by(run_number=run_no).order_by(
            sql.text('-run_version')).first()
        if last_run is not None:
            highest_version = last_run.run_version
        else:
            highest_version = -1
        run_version = highest_version + 1

        # Search for the experiment, if it doesn't exist then add it
        experiment = session.query(Experiment).filter_by(reference_number=rb_number).first()
        if experiment is None:
            new_exp = Experiment(reference_number=rb_number)
            session.add(new_exp)
            session.commit()
            experiment = session.query(Experiment).filter_by(reference_number=rb_number).first()

        # Get the script text for the current instrument. If the script text is null then send to
        # error queue
        script_text = InstrumentVariablesUtils().get_current_script_text(instrument.name)[0]
        if script_text is None:
            self.reduction_error()
            return

        # Make the new reduction run with the information collected so far and add it into the
        # database
        reduction_run = ReductionRun(run_number=self._data_dict['run_number'],
                                     run_version=run_version,
                                     run_name='',
                                     message='',
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
                                     started_by=self._data_dict['started_by'])
        session.add(reduction_run)
        session.commit()

        # Set our run_version to be the one we have just calculated
        self._data_dict['run_version'] = reduction_run.run_version  # pylint: disable=no-member

        # Create a new data location entry which has a foreign key linking it to the current
        # reduction run. The file path itself will point to a datafile
        # (e.g. "\isis\inst$\NDXWISH\Instrument\data\cycle_17_1\WISH00038774.nxs")
        data_location = DataLocation(file_path=self._data_dict['data'],
                                     reduction_run_id=reduction_run.id) # pylint: disable=no-member
        session.add(data_location)
        session.commit()

        # We now need to create all of the variables for the run such that the script can run
        # through in the desired way
        logger.info('Creating variables for run')
        variables = InstrumentVariablesUtils().create_variables_for_run(reduction_run)
        if not variables:
            logger.warning("No instrument variables found on %s for run %s",
                           instrument.name,
                           self._data_dict['run_number'])

        logger.info('Getting script and arguments')
        reduction_script, arguments = ReductionRunUtils().get_script_and_arguments(reduction_run)
        self._data_dict['reduction_script'] = reduction_script
        self._data_dict['reduction_arguments'] = arguments

        if instrument.is_paused:
            logger.info("Run %s has been skipped", self._data_dict['run_number'])
        else:
            self._client.send('/queue/ReductionPending', json.dumps(self._data_dict),
                              priority=self._priority)
            logger.info("Run %s ready for reduction", self._data_dict['run_number'])

    def reduction_started(self):
        """
        Called when destination queue was reduction_started.
        Updates the run as started in the database.
        """
        logger.info("Run %s has started reduction", self._data_dict['run_number'])

        reduction_run = self.find_run()

        if reduction_run:
            if str(reduction_run.status.value) == "Error" or str(
                    reduction_run.status.value) == "Queued":
                reduction_run.status = StatusUtils().get_processing()
                reduction_run.started = datetime.datetime.utcnow()
                session.add(reduction_run)
                session.commit()
            else:
                logger.error("An invalid attempt to re-start a reduction run was captured. "
                             "Experiment: %s, "
                             "Run Number: %s, "
                             "Run Version %s",
                             self._data_dict['rb_number'],
                             self._data_dict['run_number'],
                             self._data_dict['run_version'])
        else:
            logger.error("A reduction run started that wasn't found in the database. "
                         "Experiment: %s, "
                         "Run Number: %s, "
                         "Run Version %s",
                         self._data_dict['rb_number'],
                         self._data_dict['run_number'],
                         self._data_dict['run_version'])

    def reduction_complete(self):
        """
        Called when the destination queue was reduction_complete
        Updates the run as complete in the database.
        """
        # pylint: disable=too-many-nested-blocks
        try:
            logger.info("Run %s has completed reduction", self._data_dict['run_number'])
            reduction_run = self.find_run()

            if reduction_run:
                if reduction_run.status.value == "Processing":
                    reduction_run.status = StatusUtils().get_completed()
                    reduction_run.finished = datetime.datetime.utcnow()
                    for name in ['message', 'reduction_log', 'admin_log']:
                        setattr(reduction_run, name, self._data_dict.get(name, ""))
                    if 'reduction_data' in self._data_dict:
                        for location in self._data_dict['reduction_data']:
                            reduction_location = ReductionLocation(file_path=location,
                                                                   reduction_run=reduction_run)
                            session.add(reduction_location)
                            session.commit()

                            # Get any .png files and store them as base64 strings
                            # Currently doesn't check sub-directories
                            graphs = glob.glob(location + '*.[pP][nN][gG]')
                            for graph in graphs:
                                with open(graph, "rb") as image_file:
                                    encoded_string = 'data:image/png;base64,' + base64.b64encode(
                                        image_file.read())
                                    if reduction_run.graph is None:
                                        reduction_run.graph = [encoded_string]
                                    else:
                                        reduction_run.graph.append(encoded_string)
                    session.add(reduction_run)
                    session.commit()

                else:
                    logger.error("An invalid attempt to complete a reduction run that wasn't "
                                 "processing has been captured. "
                                 "Experiment: %s, "
                                 "Run Number: %s, "
                                 "Run Version %s",
                                 self._data_dict['rb_number'],
                                 self._data_dict['run_number'],
                                 self._data_dict['run_version'])
            else:
                logger.error("A reduction run completed that wasn't found in the database. "
                             "Experiment: %s, Run Number:%s,"
                             " Run Version %s",
                             self._data_dict['rb_number'],
                             self._data_dict['run_number'],
                             self._data_dict['run_version'])

        except BaseException as exp:
            logger.error("Error: %s", exp)

    def reduction_skipped(self):
        """
        Called when the destination was reduction skipped
        Updates the run to Skipped status in database
        Will NOT attempt re-run
        """
        if 'message' in self._data_dict:
            logger.info("Run %s has been skipped - %s",
                        self._data_dict['run_number'],
                        self._data_dict['message'])
        else:
            logger.info("Run %s has been skipped - No error message was found",
                        self._data_dict['run_number'])

        reduction_run = self.find_run()
        if not reduction_run:
            logger.error("A reduction run that was skipped, could not be found in the database. "
                         "Experiment: %s, "
                         "Run Number: %s, "
                         "Run Version %s",
                         self._data_dict['rb_number'],
                         self._data_dict['run_number'],
                         self._data_dict['run_version'])
            return

        reduction_run.status = StatusUtils().get_skipped()
        reduction_run.finished = datetime.datetime.utcnow()
        for name in ['message', 'reduction_log', 'admin_log']:
            setattr(reduction_run, name, self._data_dict.get(name, ""))
        session.add(reduction_run)
        session.commit()

    def reduction_error(self):
        """
        Called when the destination was reduction_error.
        Updates the run as complete in the database.
        """
        if 'message' in self._data_dict:
            logger.info("Run %s has encountered an error - %s",
                        self._data_dict['run_number'],
                        self._data_dict['message'])
        else:
            logger.info("Run %s has encountered an error - No error message was found",
                        self._data_dict['run_number'])

        reduction_run = self.find_run()

        if not reduction_run:
            logger.error("A reduction run that caused an error wasn't found in the database. "
                         "Experiment: %s, "
                         "Run Number: %s, "
                         "Run Version %s",
                         self._data_dict['rb_number'],
                         self._data_dict['run_number'],
                         self._data_dict['run_version'])
            return

        reduction_run.status = StatusUtils().get_error()
        reduction_run.finished = datetime.datetime.utcnow()
        for name in ['message', 'reduction_log', 'admin_log']:
            setattr(reduction_run, name, self._data_dict.get(name, ""))
        session.add(reduction_run)
        session.commit()

        if 'retry_in' in self._data_dict:
            experiment = session.query(Experiment).filter_by(
                reference_number=self._data_dict['rb_number']).first()
            previous_runs = session.query(ReductionRun).filter_by(
                run_number=self._data_dict['run_number'],
                experiment=experiment).all()
            max_version = -1
            for previous_run in previous_runs:
                current_version = previous_run.run_version
                if current_version > max_version:
                    max_version = current_version

            # If we have already tried more than 5 times, we want to give up and we don't want
            # to retry the run
            if max_version <= 4:
                self.retry_run(
                    self._data_dict["started_by"],
                    reduction_run,
                    self._data_dict["retry_in"])
            else:
                # Need to delete the retry_in entry from the dictionary so that the front end
                # doesn't report a false retry instance.
                del self._data_dict['retry_in']

    def find_run(self):
        """ Find a reduction run in the database. """
        # Commit before we attempt to find the run. Committing will sync any values that have
        #  been added to the database from the front end (normally retrying runs).
        session.commit()
        experiment = session.query(Experiment).filter_by(
            reference_number=self._data_dict['rb_number']).first()
        if not experiment:
            logger.error("Unable to find experiment %s", self._data_dict['rb_number'])
            return None

        logger.info('Finding a run with an experiment ID %s, run number %s and run version %s',
                    experiment.id,
                    int(self._data_dict['run_number']),
                    int(self._data_dict['run_version']))
        reduction_run = session.query(ReductionRun).filter_by(experiment=experiment,
                                                              run_number=int(
                                                                  self._data_dict['run_number']),
                                                              run_version=int(
                                                                  self._data_dict['run_version']))\
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
    setup_connection('Autoreduction_QueueProcessor')


if __name__ == '__main__':
    main()
