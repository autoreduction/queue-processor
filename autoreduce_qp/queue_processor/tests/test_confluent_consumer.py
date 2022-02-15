import os
from unittest import TestCase, main, mock

from autoreduce_qp.queue_processor.tests.test_handle_message import make_test_message
from autoreduce_qp.queue_processor.confluent_consumer import Consumer

from autoreduce_utils.clients.producer import Publisher

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL")


# This tests if a message sent to Kafka is successfully consumed.
class KafkaTestCase(TestCase):

    @mock.patch('autoreduce_qp.queue_processor.confluent_consumer.Consumer.run')
    def test_message(self, mock_method):
        with mock.patch.object(Consumer, 'on_message', return_value="test"):
            # Make test message
            message = make_test_message("test_instrument")

            # Send message
            publisher = Producer()
            p_msg = publisher.publish(message)

            # Consume message
            consumer = Consumer()
            c_msg = consumer.start()

            # Assert mock_method was called at least once
            self.assertTrue(mock_method.called)

            # Check if the messages are the same
            self.assertTrue(p_msg == c_msg)

            publisher.stop()
            consumer.stop()


if __name__ == '__main__':
    main()
