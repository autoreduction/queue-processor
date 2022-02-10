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
