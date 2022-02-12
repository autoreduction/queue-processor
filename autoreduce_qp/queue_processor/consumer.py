from contextlib import contextmanager
import json
import threading
import traceback
from typing import Tuple
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import logging
import os
import time

from autoreduce_qp.queue_processor.handle_message import HandleMessage
from autoreduce_utils.clients.connection_exception import ConnectionException
from autoreduce_utils.message.message import Message
from autoreduce_utils.clients.producer import Publisher

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
        self._processing = False

        while self.consumer is None:
            self.logger.debug("Getting the kafka consumer")
            try:
                self.consumer = KafkaConsumer(bootstrap_servers=KAFKA_BROKER_URL,
                                              auto_offset_reset='latest',
                                              value_deserializer=lambda m: json.loads(m.decode('utf-8')))
            except NoBrokersAvailable as err:
                self.logger.error("Unable to find a broker: %s".format(err))
                time.sleep(1)

    def run(self):
        self.consumer.subscribe([TRANSACTIONS_TOPIC])

        while not self._stop_event.is_set():
            self.logger.debug("Reading a message")
            for message in self.consumer:
                self.logger.debug("Read a message")
                print(message)
                on_message(self, message)
                if self._stop_event.is_set():
                    break

        self.consumer.close()

    def stop(self):
        """ Stop the consumer """
        self._stop_event.set()

    def stopped(self):
        """ Return whether the consumer has been stopped """
        return self._stop_event.is_set()

    def is_processing_message(self):
        """Return the processing state."""
        return self._processing

    @contextmanager
    def mark_processing(self):
        """
        Function usable by using `with ...` for context management and to ensure
        processing is always set to false at the end.
        """
        self._processing = True
        try:
            yield
        finally:
            self._processing = False


def on_message(self, incoming_message):
    """ Handle a message """
    topic = incoming_message.topic
    try:
        message = Message()
        message.populate(incoming_message.value)
    except ValueError:
        self.logger.error("Could not decode message from %s\n\n%s", topic, traceback.format_exc())
        return

    try:
        if topic == 'data_ready':
            self.message_handler.data_ready(message)
        else:
            self.logger.error("Received a message on an unknown topic '%s'", topic)
    except Exception as exp:  # pylint:disable=broad-except
        self.logger.error("Unhandled exception encountered: %s %s\n\n%s",
                          type(exp).__name__, exp, traceback.format_exc())


def setup_connection() -> Consumer:
    """
    Starts the Kafka consumer.
    """
    consumer = Consumer()

    t1 = threading.Thread(target=consumer.run)
    t1.start()

    return consumer


def setup_kafka_connections() -> Tuple[Publisher, Consumer]:
    """
    Starts the Kafka consumer and publisher.
    """

    consumer = Consumer()
    publisher = Publisher()

    t1 = threading.Thread(target=consumer.run)
    t1.start()

    t2 = threading.Thread(target=publisher.run)
    t2.start()

    return publisher, consumer


def main():
    """Entry point for the module."""
    logger = logging.getLogger(__package__)
    try:
        setup_connection()
    except ConnectionException as exp:
        logger.error("Exception occurred while connecting: %s %s\n\n%s",
                     type(exp).__name__, exp, traceback.format_exc())
        raise

    logger.info("Kafka consumer started.")


if __name__ == '__main__':
    main()
