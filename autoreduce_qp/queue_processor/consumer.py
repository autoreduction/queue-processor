import threading
import traceback
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import logging
import os
import time
from typing import Tuple

from autoreduce_qp.queue_processor.handle_message import HandleMessage
from autoreduce_utils.clients.producer import Publisher
from autoreduce_utils.clients.connection_exception import ConnectionException
from autoreduce_utils.message.message import Message

TRANSACTIONS_TOPIC = os.getenv('KAFKA_TOPIC')
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")


class Consumer(threading.Thread):
    """ A class to read messages from a Kafka topic """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__package__)
        self.logger.debug("Initializing the consumer")
        self.consumer = None
        self.message_handler = HandleMessage()
        self._stop_event = threading.Event()

        while self.consumer is None:
            self.logger.debug("Getting the kafka consumer")
            try:
                self.consumer = KafkaConsumer(bootstrap_servers=KAFKA_BROKER_URL, auto_offset_reset='earliest')
            except NoBrokersAvailable as err:
                self.logger.error("Unable to find a broker: %s".format(err))
                time.sleep(1)

    def run(self):
        self.consumer.subscribe([TRANSACTIONS_TOPIC])

        while not self._stop_event.is_set():
            self.logger.debug("Reading a message")
            for message in self.consumer:
                self.logger.debug("Read a message")
                #on_message(message)
                if self._stop_event.is_set():
                    break

        self.consumer.close()

    def stop(self):
        """ Stop the consumer """
        self._stop_event.set()

    def stopped(self):
        """ Return whether the consumer has been stopped """
        return self._stop_event.is_set()

    def on_message(self, message):
        """ Handle a message """
        topic = message.topic
        try:
            message = Message()
            message.populate(message)
        except ValueError:
            self.logger.error("Could not decode message from %s\n\n%s", topic, traceback.format_exc())
            return

        try:
            if topic == '/queue/DataReady':
                self.message_handler.data_ready(message)
            else:
                self.logger.error("Received a message on an unknown topic '%s'", topic)
        except Exception as exp:  # pylint:disable=broad-except
            self.logger.error("Unhandled exception encountered: %s %s\n\n%s",
                              type(exp).__name__, exp, traceback.format_exc())


def setup_connection() -> Tuple[Consumer]:
    """
    Starts the Kafka producer and consumer.
    
    Returns:
        A client connected and subscribed to the queue specified in credentials,
        and a listener instance which will handle incoming messages.
    """
    consumer = Consumer()

    t1 = threading.Thread(target=consumer.run)
    t1.start()
    time.sleep(3)
    consumer._stop_event.set()
    t1.join()

    return consumer


def main():
    """Entry point for the module."""
    logger = logging.getLogger(__package__)
    try:
        setup_connection()
    except ConnectionException as exp:
        logger.error("Exception occurred while connecting: %s %s\n\n%s",
                     type(exp).__name__, exp, traceback.format_exc())
        raise

    logger.info("Kafka producer connected and consumer activated.")


if __name__ == '__main__':
    main()
