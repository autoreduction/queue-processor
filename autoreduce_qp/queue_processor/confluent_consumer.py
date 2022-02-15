import threading
import traceback
from typing import Tuple
from confluent_kafka import DeserializingConsumer, KafkaError, KafkaException
from confluent_kafka.serialization import StringDeserializer
import logging
import os

from autoreduce_qp.queue_processor.handle_message import HandleMessage
from autoreduce_utils.clients.connection_exception import ConnectionException
from autoreduce_utils.message.message import Message
from autoreduce_utils.clients.producer import Publisher

TRANSACTIONS_TOPIC = os.getenv('KAFKA_TOPIC')
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")
GROUP_ID = 1


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
            try:
                self.logger.debug("Getting the kafka consumer")

                config = {
                    'bootstrap.servers': KAFKA_BROKER_URL,
                    'group.id': GROUP_ID,
                    'auto.offset.reset': "latest",
                    "on_commit": self.on_commit,
                    'key.deserializer': StringDeserializer('utf_8'),
                    'value.deserializer': StringDeserializer('utf_8')
                }
                self.consumer = DeserializingConsumer(config)
                self.consumer.subscribe([TRANSACTIONS_TOPIC])
            except KafkaException as err:
                self.logger.error("Could not initialize the consumer: %s", err)
                raise ConnectionException("Could not initialize the consumer")

    def run(self):
        """ Run the consumer """
        while not self._stop_event.is_set():
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    self.logger.error(f'{msg.topic()} in partition {msg.partition} '
                                      f'{msg.partition()} reached end at offset '
                                      f'{msg.offset()}')
                else:
                    self.logger.error("Undefined error in consumer loop")
                    raise KafkaException(msg.error())
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

    # Called when the consumer commits it's new offset
    def on_commit(self, error, partition_list):
        self.logger.info(f"On Commit: Error: {error} Partitions: {partition_list}")

    def on_message(self, incoming_message):
        """ Handle a message """
        topic = incoming_message.topic()
        data = incoming_message.value()
        try:
            message = Message.parse_raw(data)
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
