import unittest

from utils.clients.settings import ACTIVEMQ
from utils.clients.queue_client import QueueClient


class TestQueueClient(unittest.TestCase):

    def test_queue_client_default_init(self):
        client = QueueClient()
        expected_broker = [(ACTIVEMQ['brokers'].split(':')[0],
                            int(ACTIVEMQ['brokers'].split(':')[1]))]
        self.assertEqual(expected_broker, client._brokers)
        self.assertEqual(ACTIVEMQ['amq_user'], client._user)
        self.assertEqual(ACTIVEMQ['amq_pwd'], client._password)
        self.assertEqual(None, client._connection)
        self.assertEqual('QueueProcessor', client._consumer_name)

    def test_queue_client_non_default_init(self):
        client = QueueClient('test_broker', 'test_user', 'test_pass', 'test_consumer')
        self.assertEqual('test_broker', client._brokers)
        self.assertEqual('test_user', client._user)
        self.assertEqual('test_pass', client._password)
        self.assertEqual(None, client._connection)
        self.assertEqual('test_consumer', client._consumer_name)

    def test_valid_queue_connection(self):
        """
        This by proxy will also test the get_connection function
        """
        client = QueueClient()
        client.connect()
        self.assertTrue(client._connection.is_connected())

    def test_invalid_queue_connection(self):
        client = QueueClient('not_a_broker', 'not_a_user', 'not_a_pass')
        with self.assertRaises(ValueError):
            client.connect()

    def test_stop_connection(self):
        client = QueueClient()
        client.connect()
        self.assertTrue(client._connection.is_connected())
        client.stop()
        self.assertIsNone(client._connection)

    def test_send_data(self):
        client = QueueClient()
        client.send('dataready', 'test-message')


class TestDatabaseClient(unittest.TestCase):

    @unittest.skip("Not yet implemented")
    def test_database_client_default_init(self):
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_database_client_non_default_init(self):
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_valid_database_connection(self):
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_invalid_database_connection(self):
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_stop_connection(self):
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_query_data(self):
        self.fail("Not implemented")


class TestICATClient(unittest.TestCase):
    """
    Some thought will be required here as we can't use icat credentials
    """
    @unittest.skip("Not yet implemented")
    def test_icat_client_default_init(self):
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_icat_client_non_default_init(self):
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_valid_icat_connection(self):
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_invalid_icat_connection(self):
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_stop_connection(self):
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_query_icat(self):
        self.fail("Not implemented")