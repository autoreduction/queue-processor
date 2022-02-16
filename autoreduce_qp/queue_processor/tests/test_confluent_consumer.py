import os
from unittest import TestCase, main, mock

from confluent_kafka import DeserializingConsumer
from autoreduce_qp.queue_processor.handle_message import HandleMessage

from autoreduce_qp.queue_processor.tests.test_handle_message import make_test_message
from autoreduce_qp.queue_processor.confluent_consumer import Consumer, setup_connection
from confluent_kafka.serialization import StringDeserializer
from autoreduce_utils.clients.producer import Publisher

TRANSACTIONS_TOPIC = os.getenv('KAFKA_TOPIC')
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")
GROUP_ID = 1


# This tests if a message sent to Kafka is successfully consumed.
class KafkaTestCase(TestCase):

    @mock.patch('autoreduce_qp.queue_processor.confluent_consumer.DeserializingConsumer')
    def test_init_consumer(self, mock_kafka_consumer):
        consumer = Consumer(mock_kafka_consumer)
        mock_kafka_consumer.subscribe.assert_called_once_with([TRANSACTIONS_TOPIC])

    @mock.patch('autoreduce_qp.queue_processor.confluent_consumer.DeserializingConsumer')
    def test_consume(self, ConfluentConsumer):
        # Mocking whole class since mock cannot set
        # properties in cimpl.Consumer
        confluent_consumer = ConfluentConsumer.return_value
        message1 = mock.Mock()
        message1.value.return_value = 'foo'

        message2 = mock.Mock()
        message2.value.return_value = 'bar'

        confluent_consumer.consume.return_value = [message1, message2]

        consumer = Consumer()

        result = consumer.manual_consume(100, timeout=5)

        assert result == ['foo', 'bar']
        confluent_consumer.consume.assert_called_with(100, timeout=5)


if __name__ == '__main__':
    main()
