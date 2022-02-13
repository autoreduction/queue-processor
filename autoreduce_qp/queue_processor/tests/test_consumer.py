from unittest import TestCase, mock

from autoreduce_qp.queue_processor.consumer import Consumer


class TestConsumer(TestCase):
    """
    Test Kafka Consumer
    """

    def setUp(self):
        self.consumer = Consumer()

    def test_run(self):
        """
        Test: Connection to Kafka setup, along with subscription to queues
        When: setup_connection is called
        """
        self.consumer.run()

    def test_on_message_unknown_topic(self):
        """Test receiving a message on an unknown topic"""
        # Should it create a new topic?
        pass
