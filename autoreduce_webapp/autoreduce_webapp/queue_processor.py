import stomp
from settings import ACTIVEMQ, BASE_DIR, LOGGING, EMAIL_HOST, EMAIL_PORT, EMAIL_ERROR_RECIPIENTS, EMAIL_ERROR_SENDER, BASE_URL
import logging
import logging.config
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("django")
import time, sys, os, json, glob, base64
from django.utils import timezone
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)
from reduction_viewer.models import ReductionRun, ReductionLocation, DataLocation, Experiment
from reduction_viewer.utils import StatusUtils, InstrumentUtils, ReductionRunUtils
from reduction_variables.models import RunVariable
from reduction_variables.utils import MessagingUtils
from icat_communication import ICATCommunication
from django.db import connection
import smtplib
import django
django.setup()

class Listener(object):
    def __init__(self, client):
        self._client = client
        self._data_dict = {}
        self._priority = ''

    def on_error(self, headers, message):
        logger.error("Error recieved - %s" % str(message))

    def on_message(self, headers, message):
        # Slight hack to avoid the MySQL wait timeout limit (default 8 hours) that causes "MySQL has gone away"
        connection.close()

        destination = headers["destination"]
        self._priority = headers["priority"]
        logger.info("Dest: %s Prior: %s" % (destination, self._priority))
        # Load the JSON message and header into dictionaries
        try:
            self._data_dict = json.loads(message)
        except:
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
        except BaseException as e:
            logger.error("UNCAUGHT ERROR: %s" % e)

            
    def data_ready(self):
        # Import within method to prevent cylindrical imports
        from reduction_variables.utils import InstrumentVariablesUtils, ReductionVariablesUtils

        logger.info("Data ready for processing run %s on %s" % (str(self._data_dict['run_number']), self._data_dict['instrument']))
        
        instrument = InstrumentUtils().get_instrument(self._data_dict['instrument'])
        # Activate the instrument if it is currently set to inactive
        if not instrument.is_active:
            instrument.is_active = True
            instrument.save()

        last_run = ReductionRun.objects.filter(run_number=self._data_dict['run_number']).order_by('-run_version').first()
        if last_run is not None:
            highest_version = last_run.run_version
        else:
            highest_version = -1

        experiment, experiment_created = Experiment.objects.get_or_create(reference_number=self._data_dict['rb_number'])
        if experiment_created:
            experiment.save()

        if instrument.is_paused:
            status=StatusUtils().get_skipped()
        else:
            status=StatusUtils().get_queued()

        run_version = highest_version+1
        reduction_run = ReductionRun(run_number=self._data_dict['run_number'],
                                     run_version=run_version,
                                     experiment=experiment,
                                     instrument=instrument,
                                     status=status
                                     )
        reduction_run.save()
        self._data_dict['run_version'] = reduction_run.run_version

        variables = InstrumentVariablesUtils().get_variables_for_run(reduction_run)
        data_location = DataLocation(file_path=self._data_dict['data'], reduction_run=reduction_run)

        if not variables:
            logger.warning("No instrument variables found on %s for run %s" % (instrument.name, self._data_dict['run_number']))
        else:
            for variable in variables:
                reduction_run_variables = RunVariable(name=variable.name, value=variable.value, type=variable.type, is_advanced=variable.is_advanced, help_text=variable.help_text)
                reduction_run_variables.reduction_run = reduction_run
                reduction_run.run_variables.add(reduction_run_variables)
                reduction_run_variables.save()
                for script in variable.scripts.all():
                    reduction_run_variables.scripts.add(script)

        reduction_run.save()
        data_location.save()

        if variables:
            reduction_script, arguments = ReductionVariablesUtils().get_script_and_arguments(reduction_run.run_variables.all())
            self._data_dict['reduction_script'] = reduction_script
            self._data_dict['reduction_arguments'] = arguments
        else:
            self._data_dict['reduction_script'] = InstrumentVariablesUtils().get_script(instrument.name)
            self._data_dict['reduction_arguments'] = {}

        if instrument.is_paused:
            logger.info("Run %s has been skipped" % self._data_dict['run_number'])
        else:
            self._client.send('/queue/ReductionPending', json.dumps(self._data_dict), priority=self._priority)
            logger.info("Run %s ready for reduction" % self._data_dict['run_number'])
            logger.info("Reduction script: %s" % self._data_dict['reduction_script'][:50])

            
    def reduction_started(self):
        logger.info("Run %s has started reduction" % self._data_dict['run_number'])
        
        reduction_run = self.find_run()
        
        if reduction_run:
            if str(reduction_run.status) == "Error" or str(reduction_run.status) == "Queued":
                reduction_run.status = StatusUtils().get_processing()
                reduction_run.started = timezone.now().replace(microsecond=0)
                reduction_run.save()
            else:
                logger.error("An invalid attempt to re-start a reduction run was captured. Experiment: %s, Run Number: %s, Run Version %s" % (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))
        else:
            logger.error("A reduction run started that wasn't found in the database. Experiment: %s, Run Number: %s, Run Version %s" % (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))

            
    def reduction_complete(self):
        try:
            logger.info("Run %s has completed reduction" % self._data_dict['run_number'])
            
            reduction_run = self.find_run()
            
            if reduction_run:
                if reduction_run.status.value == "Processing":
                    reduction_run.status = StatusUtils().get_completed()
                    reduction_run.finished = timezone.now().replace(microsecond=0)
                    if 'message' in self._data_dict:
                        reduction_run.message = self._data_dict['message']
                    if 'reduction_data' in self._data_dict:
                        for location in self._data_dict['reduction_data']:
                            reduction_location = ReductionLocation(file_path=location, reduction_run=reduction_run)
                            reduction_run.reduction_location.add(reduction_location)
                            reduction_location.save()
                            
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

                    reduction_run.save()
                    
                    # Trigger any post-processing, such as saving data to ICAT
                    with ICATCommunication() as icat:
                        icat.post_process(reduction_run)                    
                else:
                    logger.error("An invalid attempt to complete a reduction run that wasn't processing has been captured. Experiment: %s, Run Number: %s, Run Version %s" % (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))
            else:
                logger.error("A reduction run completed that wasn't found in the database. Experiment: %s, Run Number: %s, Run Version %s" % (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))

        except BaseException as e:
            logger.error("Error: %s" % e)
                    

    def reduction_error(self):
        if 'message' in self._data_dict:
            logger.info("Run %s has encountered an error - %s" % (self._data_dict['run_number'], self._data_dict['message']))
        else:
            logger.info("Run %s has encountered an error - No error message was found" % (self._data_dict['run_number']))
        
        reduction_run = self.find_run()
                    
        if not reduction_run:
            logger.error("A reduction run that caused an error wasn't found in the database. Experiment: %s, Run Number: %s, Run Version %s" % (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))
            return
        
        reduction_run.status = StatusUtils().get_error()
        reduction_run.finished = timezone.now().replace(microsecond=0)
        if 'message' in self._data_dict:
            reduction_run.message = self._data_dict['message']
        reduction_run.save()
        
        if 'retry_in' in self._data_dict:
            self.retryRun(reduction_run, self._data_dict["retry_in"])
            
        self.notifyRunFailure(reduction_run)
        
        
    def find_run(self):
        experiment = Experiment.objects.filter(reference_number=self._data_dict['rb_number']).first()
        if not experiment:
            logger.error("Unable to find experiment %s" % self._data_dict['rb_number'])
            return None

        reduction_run = ReductionRun.objects.get(experiment=experiment, run_number=int(self._data_dict['run_number']), run_version=int(self._data_dict['run_version']))
        return reduction_run
        
        
    def notifyRunFailure(self, reductionRun):
    
        recipients = EMAIL_ERROR_RECIPIENTS
        localRecipients = filter(lambda addr: addr.split('@')[-1] == BASE_URL, recipients) # this does not parse esoteric (but RFC-compliant) email addresses correctly
        if localRecipients: # don't send local emails
            raise Exception("Local email address specified in ERROR_EMAILS - %s match %s" % (localRecipients, BASE_URL))
    
        senderAddress = EMAIL_ERROR_SENDER
        
        errorMsg = "A reduction run - experiment %s, run %s, version %s - has failed:\n%s\n\n" % (reductionRun.experiment.reference_number, reductionRun.run_number, reductionRun.run_version, reductionRun.message)
        errorMsg += "The run will not retry automatically.\n" if not reductionRun.retry_when else "The run will automatically retry on %s.\n" % reductionRun.retry_when
        errorMsg += "Retry manually at %s%i/%i/ or on %sruns/failed/." % (BASE_URL, reductionRun.run_number, reductionRun.run_version, BASE_URL)
        
        emailContent = "From: %s\nTo: %s\nSubject:Autoreduction error\n\n%s" % (senderAddress, ", ".join(recipients), errorMsg)

        logger.info("Sending email: %s" % emailContent)
                       
        try:
            s = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            s.sendmail(senderAddress, recipients, emailContent)
            s.close()
        except Exception as e:
            logger.error("Failed to send emails %s" % emailContent)
            logger.error("Exception %s - %s" % (type(e).__name__, str(e)))
        
        
    def retryRun(self, reductionRun, retryIn):
    
        if (reductionRun.cancel):
            logger.info("Cancelling run retry")
            return
            
        logger.info("Retrying run in %i seconds" % retryIn)
        
        new_job = ReductionRunUtils().createRetryRun(reductionRun, delay=retryIn)          
        try:
            MessagingUtils().send_pending(new_job, delay=retryIn*1000) # seconds to ms
        except Exception as e:
            new_job.delete()
            raise e
        

class Client(object):
    def __init__(self, brokers, user, password, topics=None, consumer_name='QueueProcessor', client_only=True, use_ssl=ACTIVEMQ['SSL']):
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

        connection = stomp.Connection(host_and_ports=self._brokers, use_ssl=self._use_ssl, ssl_version=3)
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
        logger.info("[%s] Disconnected" % (self._consumer_name))

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
    client = Client(ACTIVEMQ['broker'], ACTIVEMQ['username'], ACTIVEMQ['password'], ACTIVEMQ['topics'], 'Autoreduction_QueueProcessor', False, ACTIVEMQ['SSL'])
    client.connect()
    return client

if __name__ == '__main__':
    main()
