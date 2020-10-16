# ############################################################################
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################
"""
This module deals with the updating of the database backend.
It consumes messages from the queues and then updates the reduction run
status in the database.
"""
import logging.config
import sys
import traceback
from model.message.message import Message
from queue_processors.queue_processor.handle_message import HandleMessage
from queue_processors.queue_processor.handling_exceptions import \
    InvalidStateException
from queue_processors.queue_processor.settings import LOGGING
from utils.clients.queue_client import QueueClient


class QueueListener:
    """ Listener class that is used to consume messages from ActiveMQ. """
    def __init__(self, client):
        """ Initialise listener. """
        self._client = client
        self._message_handler = HandleMessage(queue_listener=self)
        self._priority = ''

        # Set up logging and attach the logging to the right part of the
        # config.
        logging.config.dictConfig(LOGGING)
        self._logger = logging.getLogger(__file__)

    def on_message(self, headers, message):
        """ This method is where consumed messages are dealt with. It will
        consume a message. """
        destination = headers["destination"]
        self._priority = headers["priority"]
        self._logger.info("Destination: %s Priority: %s", destination,
                          self._priority)
        # Load the JSON message and header into dictionaries
        try:
            if not isinstance(message, Message):
                json_string = message
                message = Message()
                message.populate(json_string)
        except ValueError:
            self._logger.error("Could not decode message from %s", destination)
            self._logger.error(sys.exc_info()[1])
            return
        try:
            if destination == '/queue/DataReady':
                self._message_handler.data_ready(message)
            elif destination == '/queue/ReductionStarted':
                self._message_handler.reduction_started(message)
            elif destination == '/queue/ReductionComplete':
                self._message_handler.reduction_complete(message)
            elif destination == '/queue/ReductionError':
                self._message_handler.reduction_error(message)
            elif destination == '/queue/ReductionSkipped':
                self._message_handler.reduction_skipped(message)
            else:
                self._logger.warning(
                    "Received a message on an unknown topic '%s'", destination)
        except InvalidStateException as exp:
            self._logger.error("Stomp Client message handling exception:"
                               "%s %s", type(exp).__name__, exp)
            self._logger.error(traceback.format_exc())

    def send_message(self, target: str, message: Message,
                     priority: int = None):
        """
        Sends the given message to the given queue. Priority is optionally
        provided by the caller if required, else it will use the client
        default priority.
        """
        priority = self._priority if priority is None else priority
        self._client.send(target, message, priority)


def setup_connection(consumer_name):
    """
    Starts the ActiveMQ connection and registers the event listener
    :return: (Listener) A listener instance which has subscribed to an
             ActiveMQ queue
    """
    # Connect to ActiveMQ
    activemq_client = QueueClient()
    activemq_client.connect()

    # Register the event listener
    listener = QueueListener(activemq_client)

    # Subscribe to queues
    activemq_client.subscribe_autoreduce(consumer_name, listener)
    return activemq_client


def main():
    """
    Main method.
    :return: (Listener) returns a handle to a connected Active MQ listener
    """
    return setup_connection('queue_processor')


if __name__ == '__main__':
    main()
