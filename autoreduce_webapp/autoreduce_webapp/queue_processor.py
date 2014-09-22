import stomp
from settings import LOG_FILE, LOG_LEVEL, ACTIVEMQ, BASE_DIR, ARCHIVE_BASE, REDUCTION_SCRIPT_BASE
import logging
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)
import time
import sys
import os
from datetime import datetime
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)
from reduction_viewer.models import ReductionRun, Instrument, ReductionLocation, Status
from reduction_variables.models import InstrumentVariable, RunVariable, ScriptFile
from reduction_viewer.utils import StatusUtils, InstrumentUtils
import icat

class Listener(object):
    def __init__(self, client):
        self._client = client
        self._data_dict = {}

    def on_error(self, headers, message):
        logging.error("Error recieved - %s" % str(message))

    def on_message(self, headers, message):
        destination = headers["destination"]
        # Load the JSON message into a dictionary
        try:
            self._data_dict = json.loads(message)
        except:
            logging.error("Could not decode message from %s" % destination)
            logging.error(sys.exc_value)
            return

        if destination is '/Topic/DataReady':
            data_ready()
        elif destination is '/Topic/ReductionPending':
            reduction_pending()
        elif destination is '/Topic/ReductionStarted':
            reduction_started()
        elif destination is '/Topic/ReductionComplete':
            reduction_complete()
        elif destination is '/Topic/ReductionError':
            reduction_error()
        else:
            logging.warning("Recieved a message on an unknown topic %s" % destination)

    def data_ready():
        logging.info("Data ready for processing run %s on %s" % (str(self._data_dict['run_number']), self._data_dict['instrument']))
        
        instrument = InstrumentUtils.get_instrument(self._data_dict['instrument'])
        # Activate the instrument if it is currently set to inactive
        if not instrument.is_active:
            instrument.is_active = True
            instrument.save()

        instrument_variables_start_run = InstrumentVariable.objects.filter(instrument=instrument, start_run__lte=self._data_dict['run_number']).order_by('start_run')[:1].start_run
        instrument_variables = InstrumentVariable.objects.filter(instrument=instrument, start_run=instrument_variables_start_run)

        reduction_run, created = ReductionRun.object.get_or_create(run_number=self._data_dict['run_number'],
                                    run_version=0, 
                                    experiment=self._data_dict['rb_number'], 
                                    data_location=self._data_dict['data']
                                    )
        if created:
            if not instrument_variables:
                logging.error("No instrument variables found on %s for run %s" % (instrument.name, self._data_dict['run_number']))
                
                reduction_run.message = "No instrument variables found on %s for run %s" % (instrument.name, self._data_dict['run_number'])
                reduction_run.status = StatusUtils.get_error()
            else:
                for variables in instrument_variables:
                    reduction_run_variables = RunVariable(name=variables.name, value=variables.value, type=variables.type)
                    reduction_run.run_variables.add(reduction_run_variables)
                # TODO: Create script - need some logic for finding script file
                #reduction_run.scripts.add()

            reduction_run.save()

            if instrument_variables:
                # TODO: add script and variables to data_dict
                self._client.send('Topic.ReductionPending', json.dumps(self._data_dict))        
        else:
            logging.error("An invalid attempt to queue an existing reduction run was captured. Experiment: %s, Run Number: %s, Run Version %s" % (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))

    def reduction_pending():
        logging.info("Run %s ready for reduction" % self._data_dict['run_number'])

    def reduction_started():
        logging.info("Run %s has started reduction" % self._data_dict['run_number'])
        
        reduction_run = ReductionRun.objects.get(experiment=self._data_dict['rb_number'], run_number=self._data_dict['run_number'], run_version=self._data_dict['run_version'])
        if reduction_run:
            if reduction_run.status.value == "Error" or reduction_run.status.value == "Queued":
                reduction_run.status = StatusUtils.get_processing()
                reduction_run.started = datetime.now()
                reduction_run.save()
            else:
                logging.error("An invalid attempt to re-start a reduction run was captured. Experiment: %s, Run Number: %s, Run Version %s" % (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))
        else:
            logging.error("A reduction run started that wasn't found in the database. Experiment: %s, Run Number: %s, Run Version %s" % (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))

    def reduction_complete():
        logging.info("Run %s has completed reduction" % self._data_dict['run_number'])
        
        reduction_run = ReductionRun.objects.get(experiment=self._data_dict['rb_number'], run_number=self._data_dict['run_number'], run_version=self._data_dict['run_version'])
             
         if reduction_run:
            if reduction_run.status.value == "Processing":
                reduction_run.status = StatusUtils.get_completed()
                reduction_run.finished = datetime.now()
                if self._data_dict['message']:
                    reduction_run.message = self._data_dict['message']
                for location in self._data_dict['reduction_data']:
                    reduction_location = ReductionLocation(file_path=location)
                    reduction_run.reduction_location.add(reduction_location)
                    # TODO: get graphs
                reduction_run.save()

                # TODO: reduction_complete - trigger any post-processes (e.g. ICAT)
            else:
                logging.error("An invalid attempt to complete a reduction run that wasn't processing has been captured. Experiment: %s, Run Number: %s, Run Version %s" % (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))
        else:
            logging.error("A reduction run completed that wasn't found in the database. Experiment: %s, Run Number: %s, Run Version %s" % (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))

    def reduction_error():
        logging.info("Run %s has encountered an error - %s" % (self._data_dict['run_number'], self._data_dict['message']))
        
        reduction_run = ReductionRun.objects.get(experiment=self._data_dict['rb_number'], run_number=self._data_dict['run_number'], run_version=self._data_dict['run_version'])
                
        if reduction_run:
            reduction_run.status = StatusUtils.get_error()
            reduction_run.finished = datetime.now()
            reduction_run.message = self._data_dict['message']
            reduction_run.save()
        else:
            logging.error("A reduction run that caused an error wasn't found in the database. Experiment: %s, Run Number: %s, Run Version %s" % (self._data_dict['rb_number'], self._data_dict['run_number'], self._data_dict['run_version']))
        

class Client(object):
    def __init__(self, brokers, user, password, topics=None, consumer_name='QueueProcessor'):
        self._brokers = brokers
        self._user = user
        self._password = password
        self._connection = None
        self._topics = topics
        self._consumer_name = consumer_name
        self._listener = None

    def set_listner(self, listener):
        self._listener = listener

    def get_connection(self, listener=None):
        if listener is None:
            if self._listener is None:
                listener = Listener(self)
            else:
                listener = self._listener

        logging.info("[%s] Connecting to %s" % (self._consumer_name, str(self._brokers)))

        connection = stomp.Connection(host_and_ports=self._brokers)
        connection.set_listener(self._consumer_name, listener)
        connection.start()
        connection.connect(self._user, self._password, wait=True)

        time.sleep(0.5)
        return connection

    def connect(self):
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()
        
        for queue in self._queues:
            logging.info("[%s] Subscribing to %s" % (self._consumer_name, queue))
            self._connection.subscribe(destination=queue, id=1, ack='auto')

    def _disconnect(self):
        if self._connection is not None and self._connection.is_connected():
            self._connection.disconnect()
        self._connection = None
        logging.info("[%s] Disconnected" % (self._consumer_name))

    def stop(self):
        self._disconnect()
        if self._connection is not None:
            self._connection.stop()
        self._connection = None

    def send(self, destination, message, persistent='true'):
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()
        self._connection.send(destination, message, persistent=persistent)
        logging.debug("[%s] send message to %s" % (self._consumer_name, destination))


def main():
    client = Client(ACTIVEMQ['broker'], ACTIVEMQ['username'], ACTIVEMQ['password'], ACTIVEMQ['topics'], 'Autoreduction_QueueProcessor')
    client.connect()

if __name__ == '__main__':
    main()