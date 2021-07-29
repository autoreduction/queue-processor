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
import logging
import time
import traceback
from contextlib import contextmanager
from typing import Tuple

from stomp import ConnectionListener
from autoreduce_utils.clients.queue_client import QueueClient
from autoreduce_utils.clients.connection_exception import ConnectionException
from autoreduce_utils.message.message import Message

from autoreduce_qp.queue_processor.handle_message import HandleMessage


class QueueListener(ConnectionListener):
    """ Listener class that is used to consume messages from ActiveMQ. """
    def __init__(self, client: QueueClient):
        """ Initialise listener. """
        self.client: QueueClient = client
        self.message_handler = HandleMessage()

        self.logger = logging.getLogger(__package__)

        # Keeps track of whether there is currently a message being processed.
        # Just a raw bool is OK because the subscription is configured to
        # prefetch 1 message at a time - i.e. this function should NOT run in parallel
        self._processing = False

    def is_processing_message(self):
        """
        Getter for the processing state
        """
        return self._processing

    @contextmanager
    def mark_processing(self):
        """
        Function usable by using `with ...` for context management
        and to ensure processing is always set to false at the end
        """
        self._processing = True
        try:
            yield
        finally:
            self._processing = False

    def on_disconnected(self):
        """
        Called when the listener loses connection to activemq
        """
        self.logger.warning("Connection to ActiveMQ lost unexpectedly, attempting to reconnect...")
        try:
            self.client.connect()
            self.client.subscribe(self)
        except ConnectionException:
            self.logger.warning("Failed to reconnect trying again in 30 seconds")
            time.sleep(30)
            self.on_disconnected()

    def on_message(self, frame):
        """ This method is where consumed messages are dealt with. It will
        consume a message. """
        with self.mark_processing():
            destination = frame.headers["destination"]
            priority = frame.headers["priority"]
            self.logger.info("Destination: %s Priority: %s", destination, priority)
            # Load the JSON message and header into dictionaries
            try:
                message = Message()
                message.populate(frame.body)
            except ValueError:
                self.logger.error("Could not decode message from %s\n\n%s", destination, traceback.format_exc())
                return

            # the connection is configured with client-individual, meaning that each client
            # has to submit an acknowledgement for receiving the message
            # (otherwise I think that it is not removed from the queue but I am not sure about that)
            self.client.ack(frame.headers["message-id"], frame.headers["subscription"])
            try:
                if destination == '/queue/DataReady':
                    self.message_handler.data_ready(message)
                else:
                    self.logger.error("Received a message on an unknown topic '%s'", destination)
            except Exception as exp:  # pylint:disable=broad-except
                self.logger.error("Unhandled exception encountered: %s %s\n\n%s",
                                  type(exp).__name__, exp, traceback.format_exc())


def setup_connection() -> Tuple[QueueClient, QueueListener]:
    """
    Starts the ActiveMQ connection and registers the event listener
    :return: A client connected and subscribed to the queue specified in credentials, and
             a listener instance which will handle incoming messages
    """
    # Connect to ActiveMQ
    activemq_client = QueueClient()
    activemq_client.connect()

    # Register the event listener
    listener = QueueListener(activemq_client)

    # Subscribe to queues
    activemq_client.subscribe(listener)
    return activemq_client, listener


def main():
    """
    Main method.
    :return: (Listener) returns a handle to a connected Active MQ listener
    """
    try:
        setup_connection()
    except ConnectionException as exp:
        logging.getLogger(__package__).error("Exception occurred while connecting: %s %s\n\n%s",
                                             type(exp).__name__, exp, traceback.format_exc())
        raise

    # print a success message to the terminal in case it's not being run through the daemon
    print("QueueClient connected and QueueListener active.")

    # if running this script as main (e.g. when debugging the queue listener)
    # the activemq connection runs async and without this sleep the process will
    # just connect to activemq then exit completely
    while True:
        time.sleep(0.5)


if __name__ == '__main__':
    main()
