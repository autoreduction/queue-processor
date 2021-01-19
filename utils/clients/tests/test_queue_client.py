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
from unittest import mock

from mock import patch, call

from model.message.message import Message
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
        self.assertEqual('queue_client', client._consumer_name)

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
        mocked_connection = mock.Mock()
        client._connection = mocked_connection

        with mock.patch("uuid.uuid4") as patched_uuid:
            patched_uuid.return_value = 1
            client.disconnect()

        mocked_connection.disconnect.assert_called_with(receipt=str(1))
        self.assertIsNone(client._connection)

    # pylint:disable=no-self-use
    @patch('stomp.connect.StompConnection11.send')
    def test_send_with_raw_string(self, mock_stomp_send):
        """
        Test: send sends the given data using stomp.send
        When: send is called with a string argument for message
        """
        client = QueueClient()
        client.send('dataready', 'raw_json_dump')
        (args, _) = mock_stomp_send.call_args
        self.assertEqual(args[0], 'dataready')
        self.assertEqual(args[1], 'raw_json_dump')

    @patch('stomp.connect.StompConnection11.send')
    def test_send_with_message_instance(self, mock_stomp_send):
        """
        Test: send sends the given data using stomp.send
        When: send is called with a Message instance argument for message
        """
        client = QueueClient()
        message = Message(description="test-message")
        client.send('dataready', message)
        (args, _) = mock_stomp_send.call_args
        self.assertEqual(args[0], 'dataready')
        self.assertEqual(args[1], message.serialize())

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
    def test_subscribe_to_queue_list(self, mock_stomp_subscribe, mock_stomp_set_listener):
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
        mock_stomp_subscribe.assert_has_calls([call(**test_expected_args),
                                               call(**queue_expected_args)])

    @patch('stomp.connect.StompConnection11.set_listener')
    @patch('stomp.connect.StompConnection11.subscribe')
    def test_subscribe_to_single_queue(self, mock_stomp_subscribe, mock_stomp_set_listener):
        """
        Test: subscribe_queues handles a single queue (non-list)
        and calls stomp.subscribe_queues for it
        When: subscribe_queues is called a single queue passed as queue_list
        """
        client = QueueClient()
        client.connect()
        client.subscribe_queues('single-queue', 'consumer', None, 'auto')
        mock_stomp_set_listener.assert_called_once_with('consumer', None)
        test_expected_args = {'destination': 'single-queue',
                              'id': '1',
                              'ack': 'auto',
                              'header': {'activemq.prefetchSize': '1'}}
        mock_stomp_subscribe.assert_called_once_with(**test_expected_args)
