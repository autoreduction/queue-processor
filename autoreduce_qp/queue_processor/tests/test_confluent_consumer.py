import os
from unittest import TestCase, main, mock
import confluent_kafka
from autoreduce_utils.clients.producer import Publisher
from autoreduce_utils.message.message import Message
from autoreduce_qp.queue_processor.confluent_consumer import Consumer
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

    def test_init_consumer(self):
        """ Test if the consumer is initialized and subscribed to the topic """
        Consumer(self.mock_confluent_consumer)
        self.mock_confluent_consumer.subscribe.assert_called_with([TRANSACTIONS_TOPIC])


if __name__ == '__main__':
    main()
