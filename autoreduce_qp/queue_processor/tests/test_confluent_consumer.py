import os
from unittest import TestCase, main, mock
from autoreduce_qp.queue_processor.confluent_consumer import Consumer

TRANSACTIONS_TOPIC = os.getenv('KAFKA_TOPIC')
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")
GROUP_ID = 1


# This tests if a message sent to Kafka is successfully consumed.
class KafkaTestCase(TestCase):

    @classmethod
    @mock.patch('autoreduce_qp.queue_processor.confluent_consumer.DeserializingConsumer')
    def test_init_consumer(cls, mock_kafka_consumer):
        """ Test if the consumer is initialized and subscribed to the topic """
        Consumer(mock_kafka_consumer)
        mock_kafka_consumer.subscribe.assert_called_once_with([TRANSACTIONS_TOPIC])

    @classmethod
    @mock.patch('autoreduce_qp.queue_processor.confluent_consumer.DeserializingConsumer')
    def test_consume(cls, mock_confluent_consumer):
        """ Test if the consumer is able to consume messages from Kafka """
        # Mocking whole class since mock cannot set
        # properties in cimpl.Consumer
        confluent_consumer = mock_confluent_consumer.return_value
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
