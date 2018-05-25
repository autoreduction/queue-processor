import unittest

from utils.settings import ACTIVEMQ, MYSQL
from utils.clients.queue_client import QueueClient
from utils.clients.database_client import DatabaseClient


class TestDatabaseClient(unittest.TestCase):
    class TestDatabaseClient(unittest.TestCase):
        def test_database_client_default_init(self):
            client = DatabaseClient()
            self.assertEqual(MYSQL['HOST'], client._host)
            self.assertEqual(MYSQL['USER'], client._user)
            self.assertEqual(MYSQL['PASSWD'], client._password)
            self.assertEqual(MYSQL['DB'], client._database_name)
            self.assertIsNone(client._connection)
            self.assertIsNone(client._meta_data)
            self.assertIsNone(client._engine)

        def test_database_client_non_default_init(self):
            client = DatabaseClient('test_user', 'test_pass', 'test_host', 'test_db_name')
            self.assertEqual('test_user', client._user)
            self.assertEqual('test_pass', client._password)
            self.assertEqual('test_host', client._host)
            self.assertEqual('test_db_name', client._database_name)
            self.assertIsNone(client._connection)
            self.assertIsNone(client._meta_data)
            self.assertIsNone(client._engine)

        def test_valid_database_connection(self):
            client = DatabaseClient()
            client.get_connection()
            self.assertTrue(client._test_connection())

        def test_invalid_database_connection(self):
            client = DatabaseClient('not_user', 'not_pass', 'not_host', 'not_db_name')
            with self.assertRaises(RuntimeError):
                client.get_connection()

        def test_stop_connection(self):
            client = DatabaseClient()
            client.get_connection()
            self.assertTrue(client._test_connection())
            client.stop()
            self.assertIsNone(client._connection)
            self.assertIsNone(client._engine)
            self.assertIsNone(client._meta_data)


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

