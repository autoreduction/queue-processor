# ############################################################################
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################
import logging
import time
import traceback
from contextlib import contextmanager

import stomp

from model.message.message import Message
from queue_processors.queue_processor.handle_message import HandleMessage
from utils.clients.connection_exception import ConnectionException
from utils.clients.queue_client import QueueClient


class QueueListener(stomp.ConnectionListener):
    """
    QueueListener consumes messages from activemq and delegates them to be processed.
    """
    def __init__(self, client: QueueClient):
        self.client = client
        self.message_handler = HandleMessage()
        self.logger = logging.getLogger("queue_listener")
        # Keeps track of whether there is currently a message being processed.
        # Just a raw bool is OK because the subscription is configured to
        # prefetch 1 message at a time - i.e. this function should NOT run in parallel
        self._processing = False

    def is_processing_message(self) -> bool:
        """
        Check if a message is currently being processed
        :return: (bool) True if message is being processed, False otherwise
        """
        return self._processing

    @contextmanager
    def mark_processing(self) -> None:
        """
        Context manager to mark the listener as processing as a message.
        """
        self._processing = True
        try:
            yield
        finally:
            self._processing = False

    def on_message(self, headers: dict, body: str) -> None:
        """
        Implementation of stomp.ConnectionListener.on_message. Called when a message is consumed. The message will be
        transformed into a Message object and given to the message handler
        :param headers: The header of the message
        :param body: The message body
        """
        with self.mark_processing():
            destination = headers["destination"]
            priority = headers["priority"]
            self.logger.info("Recieved message with Destination: %s, Priority: %s", destination, priority)
            try:
                json_str = body
                message = Message()
                message.populate(json_str)
            except ValueError:
                self.logger.error("Could not decode message from %s\n\n%s", destination, traceback.format_exc)
                return

            self.client.ack(headers["message-id"], headers["subscription"])

            try:
                if destination == "/queue/DataReady":
                    self.message_handler.data_ready(message)
                else:
                    self.logger.warning("Recieved message on unknown topic: %s", destination)
            except Exception as ex:  # pylint:disable=broad-except
                self.logger.error("An unhandled exception occured: %s\n\n%s",
                                  type(ex).__name__, traceback.format_exc())


    def connect_and_subscribe(self) -> None:
        """
        Connect to ActiveMQ and resubscribe to the data ready queue
        """
        self.client.connect()
        self.client.subscribe_autoreduce("queue_processor", self)

    def on_disconnected(self) -> None:
        """
         Implementation of stomp.ConnectionListener.on_disconnected and is automatically called if connection to
         ActiveMQ is lost. This will attempt to reconnect and resubscribe. If this fails it will wait 60 seconds and
         try again. This will repeat until the Listener is killed.
        """
        try:
            self.logger.error("Lost connection to ActiveMQ, attempting reconnect")
            self.connect_and_subscribe()
        except ConnectionException:
            self.logger.error("Failed to reconnect, trying again in 60 seconds...")
            time.sleep(60)
            self.on_disconnected()


def main() -> None:
    """
    main function. Sets up an amq client and listener, then connects and subscribes.
    """
    amq_client = QueueClient()
    listener = QueueListener(amq_client)
    listener.connect_and_subscribe()


if __name__ == '__main__':
    try:
        main()
    except ConnectionException as exp:
        logging.getLogger("queue_listener").error("Exception occured while connecting: %s %s \n\n%s",

                                                  type(exp).__name__, exp, traceback.format_exc())
        raise

    print("QueueClient connected and QueueListener Active")
    while True:
        time.sleep(0.5)
