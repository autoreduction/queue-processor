import unittest
from MySQLdb import OperationalError
from stomp import exception

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

    '''def test_invalid_queue_connection(self):
        client = QueueClient('not_a_broker', 'not_a_user', 'not_a_pass')
        self.assertRaises(exception, client.connect)

    def test_stop_connection(self):
        client = QueueClient()
        client.connect()
        self.assertTrue(client._connection.is_connected())
        client.stop()
        self.assertFalse(client._connection.is_connected())

    def test_send_data(self):
        client = QueueClient()
        client.send('dataready', 'test-message')'''


'''class TestClientConnections(unittest.TestCase):

    def test_db_conenction(self):
        try:
            from utils.clients.database import make_db_session
            _ = make_db_session()
        except OperationalError:
            raise

    def test_queue_connection(self):
        try:
            from utils.clients.queue_client import make_queue_session
            _ = make_queue_session()
        except exception.ConnectFailedException:
            raise

    def test_icat_connection(self):
        # ToDo: This simply passes for the moment
        # until we work out how to mock ICAT connection
        pass
        # try:
        #    from utils.clients.icat_client import ICATClient
        #    _ = make_queue_session()
        # except exception.ConnectFailedException:
        #    raise
'''
