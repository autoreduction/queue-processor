import stomp
import logging.config
import smtplib
import datetime
import time
import sys
import json
import glob
import base64
from base import session
from orm_mapping import *
import traceback
sys.path.append('/home/isisautoreduce/NewQueueProcessing/QueueProcessor/utils')
from messaging_utils import MessagingUtils
from instrument_variable_utils import InstrumentVariablesUtils
from status_utils import StatusUtils
from reduction_run_utils import ReductionRunUtils
from settings import ACTIVEMQ, LOGGING, EMAIL_HOST, EMAIL_PORT, EMAIL_ERROR_RECIPIENTS, EMAIL_ERROR_SENDER, BASE_URL

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")


class Listener(object):
    def __init__(self, client):
        self._client = client
        self._data_dict = {}
        self._priority = ''

    def on_message(self, headers, message):
        destination = headers["destination"]
        self._priority = headers["priority"]
        logger.info("Destination: %s Priority: %s" % (destination, self._priority))
        # Load the JSON message and header into dictionaries
        try:
            self._data_dict = json.loads(message)
        except ValueError:
            logger.error("Could not decode message from %s" % destination)
            logger.error(sys.exc_value)
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
            else:
                logger.warning("Recieved a message on an unknown topic '%s'" % destination)
        except Exception as e:
            logger.error("UNCAUGHT ERROR: %s - %s" % (type(e).__name__, str(e)))
            logger.error(traceback.format_exc())

    def data_ready(self):
        # Rollback the session to avoid getting caught in a loop where we have uncommitted changes causing problems
        session.rollback()

        # Strip information from the JSON file (_data_dict)
        run_no = str(self._data_dict['run_number'])
        instrument_name = str(self._data_dict['instrument'])
        rb_number = self._data_dict['rb_number']

        logger.info("Data ready for processing run %s on %s" % (run_no, instrument_name))

        # Check if the instrument is active or not in the MySQL database
        instrument = session.query(Instrument).filter_by(name=instrument_name).first()

        # Add the instrument if it doesn't exist
        if not instrument:
            instrument = Instrument(name=instrument_name,
                                    is_active=1,
                                    is_paused=0
                                    )
            session.add(instrument)
            session.commit()
            instrument = session.query(Instrument).filter_by(name=instrument_name).first()
        
        # Activate the instrument if it is currently set to inactive
        if not instrument.is_active:
            logger.info("Activating " + instrument_name)
            instrument.is_active = 1
            session.commit()
        
        # If the instrument is paused, we need to find the 'Skipped' status
        if instrument.is_paused:
            status = session.query(Status).filter_by(value='Skipped').first()

        # Else we need to find the 'Queued' status number
        else:
            status = session.query(Status).filter_by(value='Queued').first()

        # If there has already been an autoreduction job for this run, we need to know it so we can increase the version
        # by 1 for this job. However, if not then we will set it to -1 which will be incremented to 0
        last_run = session.query(ReductionRun).filter_by(run_number=run_no).order_by('-run_version').first()
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

        # Get the script text for the current instrument. If the script text is null then send to error queue
        script_text = InstrumentVariablesUtils().get_current_script_text(instrument.name)[0]
        if script_text is None:
            self.reduction_error()
            return
        
        # Make the new reduction run with the information collected so far and add it into the database
        reduction_run = ReductionRun(run_number=self._data_dict['run_number'],
                                     run_version=run_version,
                                     run_name='',
                                     message='',
                                     cancel=0,
                                     hidden_in_failviewer=0,
                                     admin_log='',
                                     reduction_log='',
                                     created=datetime.datetime.now(),
                                     last_updated=datetime.datetime.now(),
                                     experiment_id=experiment.id,
                                     instrument_id=instrument.id,
                                     status_id=status.id,
                                     script=script_text
                                     )
        session.add(reduction_run)
        session.commit()

        # Set our run_version to be the one we have just calculated
        self._data_dict['run_version'] = reduction_run.run_version

        # Create a new data location entry which has a foreign key linking it to the current reduction run. The file
        # path itself will point to a datafile (e.g. "\isis\inst$\NDXWISH\Instrument\data\cycle_17_1\WISH00038774.nxs")
        data_location = DataLocation(file_path=self._data_dict['data'], reduction_run_id=reduction_run.id)
        session.add(data_location)
        session.commit()

        # We now need to create all of the variables for the run such that the script can run through in the desired way
        logger.info('Creating variables for run')
        variables = InstrumentVariablesUtils().create_variables_for_run(reduction_run)
        if not variables:
            logger.warning("No instrument variables found on %s for run %s" %
                           (instrument.name, self._data_dict['run_number']))
        
        logger.info('Getting script and arguments')
        reduction_script, arguments = ReductionRunUtils().get_script_and_arguments(reduction_run)
        self._data_dict['reduction_script'] = reduction_script
        self._data_dict['reduction_arguments'] = arguments
        
        if instrument.is_paused:
            logger.info("Run %s has been skipped" % self._data_dict['run_number'])
        else:
            self._client.send('/queue/ReductionPending', json.dumps(self._data_dict), priority=self._priority)
            logger.info("Run %s ready for reduction" % self._data_dict['run_number'])

    def reduction_started(self):
        logger.info("Run %s has started reduction" % self._data_dict['run_number'])
        
        reduction_run = self.find_run()
        
        if reduction_run:
            if str(reduction_run.status.value) == "Error" or str(reduction_run.status.value) == "Queued":
                reduction_run.status = StatusUtils().get_processing()
                reduction_run.started = datetime.datetime.now()
                session.add(reduction_run)
                session.commit()
            else:
                logger.error("An invalid attempt to re-start a reduction run was captured. Experiment: %s, "
                             "Run Number: %s, Run Version %s" % (self._data_dict['rb_number'],
                                                                 self._data_dict['run_number'],
                                                                 self._data_dict['run_version'])
                             )
        else:
            logger.error("A reduction run started that wasn't found in the database. Experiment: %s, Run Number: %s, "
                         "Run Version %s" %
                         (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))

    def reduction_complete(self):
        try:
            logger.info("Run %s has completed reduction" % self._data_dict['run_number'])
            reduction_run = self.find_run()
            
            if reduction_run:
                if reduction_run.status.value == "Processing":
                    reduction_run.status = StatusUtils().get_completed()
                    reduction_run.finished = datetime.datetime.now()
                    for name in ['message', 'reduction_log', 'admin_log']:
                        setattr(reduction_run, name, self._data_dict.get(name, ""))
                    if 'reduction_data' in self._data_dict:
                        for location in self._data_dict['reduction_data']:
                            reduction_location = ReductionLocation(file_path=location,
                                                                   reduction_run=reduction_run
                                                                   )
                            session.add(reduction_location)
                            session.commit()
                            
                            # Get any .png files and store them as base64 strings
                            # Currently doesn't check sub-directories
                            graphs = glob.glob(location + '*.[pP][nN][gG]')
                            for graph in graphs:
                                with open(graph, "rb") as image_file:
                                    encoded_string = 'data:image/png;base64,' + base64.b64encode(image_file.read())
                                    if reduction_run.graph is None:
                                        reduction_run.graph = [encoded_string]
                                    else:
                                        reduction_run.graph.append(encoded_string)
                    session.add(reduction_run)
                    session.commit()

                else:
                    logger.error("An invalid attempt to complete a reduction run that wasn't processing has been "
                                 "captured. Experiment: %s, Run Number: %s, Run Version %s" %
                                 (self._data_dict['rb_number'],
                                  self._data_dict['run_number'],
                                  self._data_dict['run_version']))
            else:
                logger.error("A reduction run completed that wasn't found in the database. Experiment: %s, Run Number: "
                             "%s, Run Version %s" %
                             (self._data_dict['rb_number'],
                              self._data_dict['run_number'],
                              self._data_dict['run_version']))

        except BaseException as e:
            logger.error("Error: %s" % e)

    def reduction_error(self):
        if 'message' in self._data_dict:
            logger.info("Run %s has encountered an error - %s" % (self._data_dict['run_number'],
                                                                  self._data_dict['message']))
        else:
            logger.info("Run %s has encountered an error - No error message was found" %
                        (self._data_dict['run_number']))
        
        reduction_run = self.find_run()
                    
        if not reduction_run:
            logger.error("A reduction run that caused an error wasn't found in the database. Experiment: %s, "
                         "Run Number: %s, Run Version %s" %
                         (self._data_dict['rb_number'],
                          self._data_dict['run_number'],
                          self._data_dict['run_version']))
            return
        
        reduction_run.status = StatusUtils().get_error()
        #  TODO : Here, and in other places where datetime is used, need to make sure we are using GMT.
        reduction_run.finished = datetime.datetime.now()
        for name in ['message', 'reduction_log', 'admin_log']:
            setattr(reduction_run, name, self._data_dict.get(name, ""))
        session.add(reduction_run)
        session.commit()

        if 'retry_in' in self._data_dict:
            experiment = session.query(Experiment).filter_by(reference_number=self._data_dict['rb_number']).first()
            previous_runs = session.query(ReductionRun).filter_by(run_number=self._data_dict['run_number'],
                                                                  experiment=experiment).all()
            max_version = -1
            for previous_run in previous_runs:
                current_version = previous_run.run_version
                if current_version > max_version:
                    max_version = current_version

            # If we have already tried more than 5 times, we want to give up and we don't want to retry the run
            if max_version <= 4:
                self.retry_run(reduction_run, self._data_dict["retry_in"])
            else:
                # Need to delete the retry_in entry from the dictionary so that the front end doesn't report a false
                # retry instance.
                del self._data_dict['retry_in']
            
        self.notify_run_failure(reduction_run)

    def find_run(self):
        # Commit before we attempt to find the run. Committing will sync any values that have been added to the database
        # from the front end (normally retrying runs).
        session.commit()
        experiment = session.query(Experiment).filter_by(reference_number=self._data_dict['rb_number']).first()
        if not experiment:
            logger.error("Unable to find experiment %s" % self._data_dict['rb_number'])
            return None

        logger.info('Finding a run with an experiment ID %s, run number %s and run version %s' %
                    (experiment.id,
                     int(self._data_dict['run_number']),
                     int(self._data_dict['run_version'])))
        reduction_run = session.query(ReductionRun).filter_by(experiment=experiment,
                                                              run_number=int(self._data_dict['run_number']),
                                                              run_version=int(self._data_dict['run_version'])).first()
        return reduction_run

    @staticmethod
    def notify_run_failure(reduction_run):
        recipients = EMAIL_ERROR_RECIPIENTS
        #  This does not parse esoteric (but RFC-compliant) email addresses correctly
        local_recipients = filter(lambda address: address.split('@')[-1] == BASE_URL, recipients)
        #  Don't send local emails
        if local_recipients:
            raise Exception("Local email address specified in ERROR_EMAILS - %s match %s" %
                            (local_recipients, BASE_URL))
    
        sender_address = EMAIL_ERROR_SENDER
        
        error_message = "A reduction run - experiment %s, run %s, version %s - has failed:\n%s\n\n" % \
                        (reduction_run.experiment.reference_number,
                         reduction_run.run_number,
                         reduction_run.run_version,
                         reduction_run.message)

        if not reduction_run.retry_when:
            error_message += "The run will not retry automatically.\n"
        else:
            error_message += "The run will automatically retry on %s.\n" % reduction_run.retry_when

        error_message += "Retry manually at %s%i/%i/ or on %sruns/failed/." % \
                         (BASE_URL,
                          reduction_run.run_number,
                          reduction_run.run_version,
                          BASE_URL)
        
        email_content = "From: %s\nTo: %s\nSubject:Autoreduction error\n\n%s" % \
                        (sender_address,
                         ", ".join(recipients),
                         error_message)

        logger.info("Sending email: %s" % email_content)
                       
        try:
            s = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            s.sendmail(sender_address, recipients, email_content)
            s.close()
        except Exception as e:
            logger.error("Failed to send emails %s" % email_content)
            logger.error("Exception %s - %s" % (type(e).__name__, str(e)))
        
    @staticmethod
    def retry_run(reduction_run, retry_in):
        if reduction_run.cancel:
            logger.info("Cancelling run retry")
            return
            
        logger.info("Retrying run in %i seconds" % retry_in)
        
        new_job = ReductionRunUtils().create_retry_run(reduction_run, delay=retry_in)
        try:
            #  Seconds to Milliseconds
            MessagingUtils().send_pending(new_job, delay=retry_in*1000)
        except Exception as e:
            logger.error(traceback.format_exc())
            new_job.delete()
            raise e
        

class Client(object):
    def __init__(self, brokers, user, password, topics=None, consumer_name='QueueProcessor',
                 client_only=True, use_ssl=ACTIVEMQ['SSL']):
        self._brokers = brokers
        self._user = user
        self._password = password
        self._connection = None
        self._topics = topics
        self._consumer_name = consumer_name
        self._listener = None
        self._client_only = client_only
        self._use_ssl = use_ssl

    def set_listener(self, listener):
        self._listener = listener

    def get_connection(self, listener=None):
        if listener is None and not self._client_only:
            if self._listener is None:
                listener = Listener(self)
                self._listener = listener
            else:
                listener = self._listener

        logger.info("[%s] Connecting to %s" % (self._consumer_name, str(self._brokers)))

        connection = stomp.Connection(host_and_ports=self._brokers, use_ssl=self._use_ssl)
        if not self._client_only:
            connection.set_listener(self._consumer_name, listener)
        connection.start()
        connection.connect(self._user, self._password, wait=False)

        time.sleep(0.5)
        return connection

    def connect(self):
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()
        
        for queue in self._topics:
            logger.info("[%s] Subscribing to %s" % (self._consumer_name, queue))
            self._connection.subscribe(destination=queue, id=1, ack='auto')

    def _disconnect(self):
        if self._connection is not None and self._connection.is_connected():
            self._connection.disconnect()
        self._connection = None
        logger.info("[%s] Disconnected" % self._consumer_name)

    def stop(self):
        self._disconnect()
        if self._connection is not None:
            self._connection.stop()
        self._connection = None

    def send(self, destination, message, persistent='true', priority='4', delay=None):
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()
            
        headers = {}
        if delay:
            headers['AMQ_SCHEDULED_DELAY'] = str(delay)
        self._connection.send(destination, message, persistent=persistent, priority=priority, headers=headers)
        logger.debug("[%s] send message to %s" % (self._consumer_name, destination))


def main():
    client = Client(ACTIVEMQ['broker'],
                    ACTIVEMQ['username'],
                    ACTIVEMQ['password'],
                    ACTIVEMQ['topics'],
                    'Autoreduction_QueueProcessor',
                    False,
                    ACTIVEMQ['SSL'])
    client.connect()
    return client

if __name__ == '__main__':
    main()
