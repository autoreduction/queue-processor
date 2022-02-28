from contextlib import contextmanager
import threading
import traceback
import logging
import os
from typing import Tuple
from pydantic import ValidationError
from confluent_kafka import DeserializingConsumer, KafkaException
from confluent_kafka.serialization import StringDeserializer
from confluent_kafka.admin import AdminClient, NewTopic
from autoreduce_utils.clients.connection_exception import ConnectionException
from autoreduce_utils.message.message import Message
from autoreduce_utils.clients.producer import Publisher
from autoreduce_qp.queue_processor.handle_message import HandleMessage

TRANSACTIONS_TOPIC = os.getenv('KAFKA_TOPIC')
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")
GROUP_ID = 'mygroup'


class Consumer(threading.Thread):
    """ A class to read messages from a Kafka topic """

    def __init__(self, consumer=None):
        super().__init__()
        self.logger = logging.getLogger(__package__)
        self.logger.debug("Initializing the consumer")

        kafka_broker = {'bootstrap.servers': KAFKA_BROKER_URL}
        admin_client = AdminClient(kafka_broker)
        topics = admin_client.list_topics().topics

        if not topics:
            # Create the topic
            self.logger.info("Creating the topic '%s'", TRANSACTIONS_TOPIC)
            new_topic = NewTopic(TRANSACTIONS_TOPIC, num_partitions=1, replication_factor=1)
            admin_client.create_topics([new_topic])

        self.consumer = consumer
        self.message_handler = HandleMessage()
        self._stop_event = threading.Event()

        # Track whether there is currently a message being processed. Just a raw
        # bool is OK because the subscription is configured to prefetch 1
        # message at a time - i.e. this function should NOT run in parallel
        self._processing = False

        while self.consumer is None:
            try:
                self.logger.debug("Getting the kafka consumer")

                config = {
                    'bootstrap.servers': KAFKA_BROKER_URL,
                    'group.id': GROUP_ID,
                    'auto.offset.reset': "earliest",
                    "on_commit": self.on_commit,
                    'key.deserializer': StringDeserializer('utf_8'),
                    'value.deserializer': StringDeserializer('utf_8')
                }
                self.consumer = DeserializingConsumer(config)
            except KafkaException as err:
                self.logger.error("Could not initialize the consumer: %s", err)
                raise ConnectionException("Could not initialize the consumer") from err

        self.consumer.subscribe([TRANSACTIONS_TOPIC])

    def run(self):
        """ Run the consumer """
        while not self._stop_event.is_set():
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if not msg.error():
                self.on_message(msg)
            else:
                self.logger.error("Undefined error in consumer loop")
                raise KafkaException(msg.error())
            if self._stop_event.is_set():
                self.logger.info("Stopping the consumer")
                break

        self.consumer.close()

    def stop(self):
        """ Stop the consumer """
        self._stop_event.set()

    def stopped(self):
        """ Return whether the consumer has been stopped """
        return self._stop_event.is_set()

    def on_commit(self, error, partition_list):
        """ Called when the consumer commits it's new offset """
        self.logger.info("On Commit: Error: %s Partitions: %s", error, partition_list)

    def on_message(self, incoming_message):
        """ Handle a message """
        with self.mark_processing():
            topic = incoming_message.topic()
            data = incoming_message.value()
            try:
                message = Message.parse_raw(data)
            except (ValidationError, TypeError):
                self.logger.error("Could not decode message: %s", data)
                return

            try:
                if topic == 'data_ready':
                    self.message_handler.data_ready(message)
                else:
                    self.logger.error("Received a message on an unknown topic '%s'", topic)
            except Exception as exp:  # pylint:disable=broad-except
                self.logger.error("Unhandled exception encountered: %s %s\n\n%s",
                                  type(exp).__name__, exp, traceback.format_exc())

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


def setup_connection(consumer=None) -> Consumer:
    """
    Starts the Kafka consumer.
    """
    consumer = Consumer(consumer=consumer)

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
