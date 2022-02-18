from contextlib import contextmanager
import json
import threading
import traceback
import logging
import os
import time
from typing import Tuple
from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
from kafka.admin import NewTopic
from autoreduce_utils.clients.connection_exception import ConnectionException
from autoreduce_utils.message.message import Message
from autoreduce_utils.clients.producer import Publisher
from autoreduce_qp.queue_processor.handle_message import HandleMessage

TRANSACTIONS_TOPIC = os.getenv('KAFKA_TOPIC')
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")
GROUP_ID = 1


class Consumer(threading.Thread):
    """ A class to read messages from a Kafka topic """

    def __init__(self):
        """ Initialize the consumer """
        threading.Thread.__init__(self)

        admin = KafkaAdminClient(bootstrap_servers=KAFKA_BROKER_URL)
        topics = admin.list_topics()

        if not topics:
            topic = NewTopic(name=TRANSACTIONS_TOPIC, num_partitions=2, replication_factor=1)
            admin.create_topics([topic])

        self.message_handler = HandleMessage()
        self._stop_event = threading.Event()

        # Track whether there is currently a message being processed. Just a raw
        # bool is OK because the subscription is configured to prefetch 1
        # message at a time - i.e. this function should NOT run in parallel
        self._processing = False

        try:
            self.consumer = KafkaConsumer(bootstrap_servers=KAFKA_BROKER_URL,
                                          auto_offset_reset='latest',
                                          value_deserializer=lambda m: json.loads(m.decode('utf-8')))
        except NoBrokersAvailable as err:
            time.sleep(1)

        self.consumer.subscribe([TRANSACTIONS_TOPIC])

    def run(self):
        """ Run the consumer """
        while not self._stop_event.is_set():
            for msg in self.consumer:
                if msg is None:
                    continue
                else:
                    self.on_message(msg)
                    if self._stop_event.is_set():
                        break

        self.consumer.close()

    def stop(self):
        """ Stop the consumer """
        self._stop_event.set()

    def stopped(self):
        """ Return whether the consumer has been stopped """
        return self._stop_event.is_set()

    def manual_consume(self, batch_size, timeout=1.0):
        """ Consume a batch of messages. Used for testing purposes """
        return [message.value() for message in self.consumer.consume(batch_size, timeout=timeout)]

    def on_commit(self, error, partition_list):
        """ Called when the consumer commits it's new offset """
        pass
        #self.logger.info("On Commit: Error: %s Partitions: %s", error, partition_list)

    def on_message(self, incoming_message):
        """ Handle a message """
        with self.mark_processing():
            topic = incoming_message.topic
            data = incoming_message.value
            try:
                message = Message.parse_obj(data)
            except ValueError:
                #self.logger.error("Could not decode message from %s\n\n%s", topic, traceback.format_exc())
                return

            try:
                if topic == 'data_ready':
                    self.message_handler.data_ready(message)
                else:
                    pass
                    #self.logger.error("Received a message on an unknown topic '%s'", topic)
            except Exception as exp:  # pylint:disable=broad-except
                pass

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


def setup_connection() -> Consumer:
    """
    Starts the Kafka consumer.
    """
    consumer = Consumer()

    consumer_thread = threading.Thread(target=consumer.run)
    consumer_thread.start()

    return consumer


def setup_kafka_connections() -> Tuple[Publisher, Consumer]:
    """
    Starts the Kafka consumer and publisher.
    """

    consumer = Consumer()
    publisher = Publisher()

    consumer_thread = threading.Thread(target=consumer.run)
    consumer_thread.start()

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
