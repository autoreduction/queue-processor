import stomp
from settings import LOG_FILE, LOG_LEVEL, ACTIVEMQ, BASE_DIR
import logging
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)
import time
import sys
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)
from reduction_viewer.models import ReductionRun

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

        if destination is 'Topic.DataReady':
            data_ready()
        elif destination is 'Topic.ReductionPending':
            reduction_pending()
        elif destination is 'Topic.ReductionStarted':
            reduction_started()
        elif destination is 'Topic.ReductionComplete':
            reduction_complete()
        elif destination is 'Topic.ReductionError':
            reduction_error()
        else:
            logging.warning("Recieved a message on an unknown topic %s" % destination)

    def data_ready():
        # TODO: data_ready - Build script/variables and send to autorecution server
        pass

    def reduction_pending():
        # TODO: reduction_pending - update status
        pass

    def reduction_started():
        # TODO: reduction_started - update status
        pass

    def reduction_complete():
        # TODO: reduction_complete - update status and trigger any post-processes (e.g. ICAT)
        pass

    def reduction_error():
        # TODO: reduction_error
        pass


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
        connection.connect(self._user, self._passcode, wait=True)

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
    # TODO: Remove these values and replace with real ones
    client = Client(ACTIVEMQ['broker'], ACTIVEMQ['username'], ACTIVEMQ['password'], ACTIVEMQ['topics'], 'Autoreduction_QueueProcessor')
    client.connect()

if __name__ == '__main__':
    main()