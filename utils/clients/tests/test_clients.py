"""
Test cases for all the clients
ActiveMQ
Database
ICAT
"""
import unittest

from utils.settings import ACTIVEMQ, MYSQL
from utils.clients.queue_client import QueueClient
from utils.clients.database_client import DatabaseClient


class TestDatabaseClient(unittest.TestCase):
    """
    Exercises the database client
    """
    # pylint:disbale=protected-access
    def test_database_client_default_init(self):
        """ Database client: test default values for initialisation """
        client = DatabaseClient()
        self.assertEqual(MYSQL['HOST'], client._host)
        self.assertEqual(MYSQL['USER'], client._user)
        self.assertEqual(MYSQL['PASSWD'], client._password)
        self.assertEqual(MYSQL['DB'], client._database_name)
        self.assertIsNone(client._connection)
        self.assertIsNone(client._meta_data)
        self.assertIsNone(client._engine)

    # pylint:disbale=protected-access
    def test_database_client_non_default_init(self):
        """ Database client: test non-default values for initialisation """
        client = DatabaseClient('test_user', 'test_pass', 'test_host', 'test_db_name')
        self.assertEqual('test_user', client._user)
        self.assertEqual('test_pass', client._password)
        self.assertEqual('test_host', client._host)
        self.assertEqual('test_db_name', client._database_name)
        self.assertIsNone(client._connection)
        self.assertIsNone(client._meta_data)
        self.assertIsNone(client._engine)

    # pylint:disbale=protected-access
    def test_valid_database_connection(self):
        """ Database client: test access is established with valid connection """
        client = DatabaseClient()
        client.get_connection()
        self.assertTrue(client._test_connection())

    def test_invalid_database_connection(self):
        """ Database client: test access is rejected with invalid credentials """
        client = DatabaseClient('not_user', 'not_pass', 'not_host', 'not_db_name')
        with self.assertRaises(RuntimeError):
            client.get_connection()

    # pylint:disbale=protected-access
    def test_stop_connection(self):
        """ Database client: test connection can be successfully stopped gracefully """
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
        """ Not yet implemented """
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_icat_client_non_default_init(self):
        """ Not yet implemented """
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_valid_icat_connection(self):
        """ Not yet implemented """
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_invalid_icat_connection(self):
        """ Not yet implemented """
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_stop_connection(self):
        """ Not yet implemented """
        self.fail("Not implemented")

    @unittest.skip("Not yet implemented")
    def test_query_icat(self):
        """ Not yet implemented """
        self.fail("Not implemented")


class TestQueueClient(unittest.TestCase):
    """
    Exercises the queue client
    """

    # pylint:disbale=protected-access
    def test_queue_client_default_init(self):
        """ Queue client: test default values for initialisation """
        client = QueueClient()
        expected_broker = [(ACTIVEMQ['brokers'].split(':')[0],
                            int(ACTIVEMQ['brokers'].split(':')[1]))]
        self.assertEqual(expected_broker, client._brokers)
        self.assertEqual(ACTIVEMQ['amq_user'], client._user)
        self.assertEqual(ACTIVEMQ['amq_pwd'], client._password)
        self.assertEqual(None, client._connection)
        self.assertEqual('QueueProcessor', client._consumer_name)

    # pylint:disbale=protected-access
    def test_queue_client_non_default_init(self):
        """ Queue client: test non-default values for initialisation """
        client = QueueClient('test_broker', 'test_user', 'test_pass', 'test_consumer')
        self.assertEqual('test_broker', client._brokers)
        self.assertEqual('test_user', client._user)
        self.assertEqual('test_pass', client._password)
        self.assertEqual(None, client._connection)
        self.assertEqual('test_consumer', client._consumer_name)

    # pylint:disbale=protected-access
    def test_valid_queue_connection(self):
        """
        Queue client: Test connection with valid credentials
        This by proxy will also test the get_connection function
        """
        client = QueueClient()
        client.connect()
        self.assertTrue(client._connection.is_connected())

    def test_invalid_queue_connection(self):
        """ Queue client: test connection with invalid credentials """
        client = QueueClient('not_a_broker', 'not_a_user', 'not_a_pass')
        with self.assertRaises(ValueError):
            client.connect()

    # pylint:disbale=protected-access
    def test_stop_connection(self):
        """ Queue client: test connection can be stopped gracefully """
        client = QueueClient()
        client.connect()
        self.assertTrue(client._connection.is_connected())
        client.stop()
        self.assertIsNone(client._connection)

    def test_send_data(self):
        """ Queue client: test data can be sent without error """
        client = QueueClient()
        client.send('dataready', 'test-message')

