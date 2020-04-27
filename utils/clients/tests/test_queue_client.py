# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test functionality for the activemq client
"""
import unittest

from mock import patch, call

from utils.clients.connection_exception import ConnectionException
from utils.clients.queue_client import QueueClient
from utils.clients.settings.client_settings_factory import ClientSettingsFactory


# pylint:disable=protected-access,invalid-name,missing-docstring
class TestQueueClient(unittest.TestCase):
    """
    Exercises the queue client
    """

    def setUp(self):
        self.incorrect_credentials = ClientSettingsFactory().create('queue',
                                                                    username='not-user',
                                                                    password='not-pass',
                                                                    host='not-host',
                                                                    port='1234')

    def test_default_init(self):
        """
        Test: Class variables are created and set
        When: QueueClient is initialised with default credentials
        """
        client = QueueClient()
        self.assertIsNotNone(client.credentials)
        self.assertIsNone(client._connection)
        self.assertEqual('QueueProcessor', client._consumer_name)

    def test_invalid_init(self):
        """
        Test: A TypeError is raised
        When: QueueClient is initialised with invalid credentials
        """
        self.assertRaises(TypeError, QueueClient, 'string')

    def test_valid_connection(self):
        """
        Test: Access is established with a valid connection
        (This by proxy will also test the get_connection function)
        When: connect is called while valid credentials are held
        """
        client = QueueClient()
        client.connect()
        self.assertTrue(client._test_connection())

    @patch('stomp.connect.StompConnection11.is_connected', return_value=False)
    def test_invalid_connection_raises_on_test(self, _):
        """
        Test: A ConnectionException is raised
        When: _test_connection is called while a valid connection is not held
        """
        client = QueueClient()
        client.connect()
        self.assertRaises(ConnectionException, client._test_connection)

    def test_invalid_credentials(self):
        """
        Test: A ConnectionException is raised
        When: _test_connection is called while invalid credentials are held
        """
        client = QueueClient(self.incorrect_credentials)
        with self.assertRaises(ConnectionException):
            client.connect()

    def test_stop_connection(self):
        """
        Test: Connection is stopped and connection variables are set to None
        When: disconnect is called while a valid connection is currently established
        """
        client = QueueClient()
        client.connect()
        self.assertTrue(client._connection.is_connected())
        client.disconnect()
        self.assertIsNone(client._connection)

    def test_serialise_message(self):
        """
        Test: Data is correctly serialised
        When: serialise_data is called with valid arguments
        """
        client = QueueClient()
        data = client.serialise_data('123', 'WISH', 'file/path', '001', 0)
        self.assertEqual(data['rb_number'], '123')
        self.assertEqual(data['instrument'], 'WISH')
        self.assertEqual(data['data'], 'file/path')
        self.assertEqual(data['run_number'], '001')
        self.assertEqual(data['facility'], 'ISIS')
        self.assertEqual(data['started_by'], 0)

    # pylint:disable=no-self-use
    @patch('stomp.connect.StompConnection11.send')
    def test_send_data(self, mock_stomp_send):
        """
        Test: send establishes a connection and sends given data using stomp.send
        When: send is called while a valid connection is not held
        """
        client = QueueClient()
        client.send('dataready', 'test-message')
        (args, _) = mock_stomp_send.call_args
        self.assertEqual(args[0], 'dataready')
        self.assertEqual(args[1], 'message')

    @patch('stomp.connect.StompConnection11.ack')
    def test_ack(self, mock_stomp_ack):
        """
        Test: ack sends an ack frame using stomp.ack
        When: ack is called while a valid connection is held
        """
        client = QueueClient()
        client.connect()
        client.ack('test')
        mock_stomp_ack.assert_called_once_with('test')

    @patch('utils.clients.queue_client.QueueClient.subscribe_queues')
    def test_subscribe_to_pending(self, mock_subscribe):
        """
        Test: subscribe_amq calls subscribe_queues with given arguments,
        including a single queue (ReductionPending)
        When: subscribe_amq is called once with the arguments given
        """
        client = QueueClient()
        client.subscribe_amq('consumer', None, 'auto')
        # due to default params these have to be supplied to the mock in a dictionary
        expected_args = {'queue_list': '/queue/ReductionPending',
                         'ack': 'auto',
                         'listener': None,
                         'consumer_name': 'consumer'}
        mock_subscribe.assert_called_once_with(**expected_args)

    @patch('utils.clients.queue_client.QueueClient.subscribe_queues')
    def test_subscribe_to_all_queues(self, mock_subscribe):
        """
        Test: subscribe_autoreduce calls subscribe_queues with given arguments,
        including a list of multiple queues (all)
        When: subscribe_autoreduce is called once with the arguments given
        """
        client = QueueClient()
        client.subscribe_autoreduce('consumer', None, 'auto')
        expected_args = {'queue_list': ['/queue/DataReady',
                                        '/queue/ReductionStarted',
                                        '/queue/ReductionComplete',
                                        '/queue/ReductionError',
                                        '/queue/ReductionSkipped'],
                         'ack': 'auto',
                         'listener': None,
                         'consumer_name': 'consumer'}
        mock_subscribe.assert_called_once_with(**expected_args)

    @patch('stomp.connect.StompConnection11.set_listener')
    @patch('stomp.connect.StompConnection11.subscribe')
    def test_subscribe_to_queue(self, mock_stomp_subscribe, mock_stomp_set_listener):
        """
        Test: subscribe_queues calls stomp.subscribe_queues twice, once for each queue given
        When: subscribe_queues is called with a queue_list length of 2
        """
        client = QueueClient()
        client.connect()
        client.subscribe_queues(['test', 'queues'], 'consumer', None, 'auto')
        mock_stomp_set_listener.assert_called_once_with('consumer', None)
        test_expected_args = {'destination': 'test',
                              'id': '1',
                              'ack': 'auto',
                              'header': {'activemq.prefetchSize': '1'}}
        queue_expected_args = {'destination': 'queues',
                               'id': '1',
                               'ack': 'auto',
                               'header': {'activemq.prefetchSize': '1'}}
        mock_stomp_subscribe.assert_has_calls([call(**test_expected_args), call(**queue_expected_args)])
