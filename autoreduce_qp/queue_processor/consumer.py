import threading
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import logging
import os
import time

TRANSACTIONS_TOPIC = os.getenv('KAFKA_TOPIC')
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")


class Consumer(threading.Thread):
    """ A class to read messages from a Kafka topic """

    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.debug("Initializing the consumer")
        self.consumer = None
        self.stop_event = threading.Event()

        while self.consumer is None:
            self.logger.debug("Getting the kafka consumer")
            try:
                self.consumer = KafkaConsumer(bootstrap_servers=KAFKA_BROKER_URL,
                                              consumer_timeout_ms=1000,
                                              auto_offset_reset='earliest',
                                              group_id=None)
            except NoBrokersAvailable as err:
                self.logger.error("Unable to find a broker: %s".format(err))
                time.sleep(1)

    def run(self):
        self.consumer.subscribe([TRANSACTIONS_TOPIC])

        while not self.stop_event.is_set():
            self.logger.debug("Reading a message")
            for message in self.consumer:
                self.logger.debug("Read a message")
                return (message)

        self.consumer.close()
