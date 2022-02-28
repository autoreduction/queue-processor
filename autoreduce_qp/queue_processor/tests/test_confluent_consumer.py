import os
import threading
from unittest import TestCase, main, mock
import confluent_kafka
from autoreduce_utils.clients.producer import Publisher
from autoreduce_utils.message.message import Message
from autoreduce_utils.clients.connection_exception import ConnectionException
from autoreduce_qp.queue_processor.confluent_consumer import Consumer, setup_connection
from autoreduce_qp.queue_processor.handle_message import HandleMessage

TRANSACTIONS_TOPIC = os.getenv('KAFKA_TOPIC')
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")
GROUP_ID = 1


class KafkaTestCase(TestCase):

    def setUp(self):
        self.mocked_producer = mock.Mock(spec=Publisher)
        self.mocked_handler = mock.MagicMock(spec=HandleMessage)
        self.bad_message = "bad_message"
        self.good_message = Message()
        self.mock_confluent_message = mock.MagicMock(spec=confluent_kafka.Message)

        with mock.patch("autoreduce_qp.queue_processor.confluent_consumer.HandleMessage",
                        return_value=self.mocked_handler), \
mock.patch("autoreduce_qp.queue_processor.confluent_consumer.DeserializingConsumer") as mock_confluent_consumer, \
mock.patch("logging.getLogger") as patched_logger:
            self.consumer = Consumer()
            self.mocked_logger = patched_logger.return_value
            self.mock_confluent_consumer = mock_confluent_consumer.return_value
            self.mock_confluent_consumer.subscribe.assert_called_with([TRANSACTIONS_TOPIC])

    def test_on_message_unknown_topic(self):
        """Test receiving a message on an unknown topic"""
        fake_topic = "fake_topic"
        self.mock_confluent_message.topic.return_value = fake_topic
        self.mock_confluent_message.value.return_value = self.good_message.json()
        self.consumer.on_message(self.mock_confluent_message)
        self.mocked_logger.error.assert_called_with("Received a message on an unknown topic '%s'", fake_topic)

    def test_on_message_bad_message(self):
        """Test receiving a bad (corrupt) message"""
        fake_topic = "fake_topic"
        self.mock_confluent_message.topic.return_value = fake_topic
        self.mock_confluent_message.value.return_value = self.bad_message
        self.consumer.on_message(self.mock_confluent_message)
        self.mocked_logger.error.assert_called_with("Could not decode message: %s", self.bad_message)

    def test_on_message_handler_catches_exceptions(self):
        """Test on_message correctly handles an exception being raised"""

        def raise_expected_exception(msg):
            raise Exception(msg)

        self.mocked_handler.data_ready.side_effect = raise_expected_exception
        self.mock_confluent_message.value.return_value = self.good_message.json()
        self.consumer.on_message(self.mock_confluent_message)
        self.mocked_logger.error.assert_called_once()

    def test_success_run(self):
        """ Test that the poll loop runs successfully """
        self.mock_confluent_message.error.return_value = None
        self.mock_confluent_consumer.poll.return_value = self.mock_confluent_message
        # Don't call the on_message method
        self.consumer.on_message = mock.Mock()
        # Stop the thread after 5 seconds
        run = threading.Timer(5, self.consumer.stop)
        run.start()
        # Start the thread
        self.consumer.run()
        self.mock_confluent_consumer.poll.assert_called_with(timeout=1.0)
        self.consumer.on_message.assert_called_with(self.mock_confluent_message)
        self.consumer.stop()

    def test_run_error_message(self):
        """ Test that the poll loop runs successfully """
        self.mock_confluent_consumer.poll.return_value = self.mock_confluent_message
        # Don't call the on_message method
        self.consumer.on_message = mock.Mock()
        # Stop the thread after 10 seconds
        run = threading.Timer(5, self.consumer.stop)
        run.start()
        # Start the thread
        self.assertRaises(confluent_kafka.KafkaException, self.consumer.run)
        self.mock_confluent_consumer.poll.assert_called_with(timeout=1.0)
        self.mocked_logger.error.assert_called_with("Undefined error in consumer loop")

    def test_stop_method(self):
        """ Test that the stop method works """
        self.consumer.stop()
        self.assertTrue(self.consumer.stopped)

    def test_stop_consumer(self):
        """ Test if the consumer is stopped via Event.set() """
        self.mock_confluent_message.error.return_value = None
        self.mock_confluent_consumer.poll.return_value = self.mock_confluent_message
        # Don't call the on_message method
        self.consumer.on_message = mock.Mock()
        run = threading.Timer(5, self.consumer.stop)
        run.start()
        self.consumer.run()
        self.mocked_logger.info.assert_called_with("Stopping the consumer")

    def test_setup_connection_exception(self):
        """ Test that the init of Consumer can handle not being able to connect to Kafka """
        with mock.patch("autoreduce_qp.queue_processor.confluent_consumer.DeserializingConsumer",
                        side_effect=confluent_kafka.KafkaException):
            self.assertRaises(ConnectionException, setup_connection)


if __name__ == '__main__':
    main()
