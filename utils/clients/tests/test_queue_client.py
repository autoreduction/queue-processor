# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
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
        """ Test default values for initialisation """
        client = QueueClient()
        self.assertIsNotNone(client.credentials)
        self.assertIsNone(client._connection)
        self.assertEqual('QueueProcessor', client._consumer_name)

    def test_invalid_init(self):
        """ Test invalid values for initialisation """
        self.assertRaises(TypeError, QueueClient, 'string')

    def test_valid_connection(self):
        """
        Test connection with valid credentials
        This by proxy will also test the get_connection function
        """
        client = QueueClient()
        client.connect()
        self.assertTrue(client._test_connection())

    @patch('stomp.connect.StompConnection11.is_connected', return_value=False)
    def test_invalid_connection_raises_on_test(self, _):
        client = QueueClient()
        client.connect()
        self.assertRaises(ConnectionException, client._test_connection)

    def test_invalid_credentials(self):
        """ Test connection with invalid credentials """
        client = QueueClient(self.incorrect_credentials)
        with self.assertRaises(ConnectionException):
            client.connect()

    def test_stop_connection(self):
        """ Test connection can be stopped gracefully """
        client = QueueClient()
        client.connect()
        self.assertTrue(client._connection.is_connected())
        client.disconnect()
        self.assertIsNone(client._connection)

    def test_serialise_message(self):
        """ Test data is correctly serialised """
        client = QueueClient()
        data = client.serialise_data('123', 'WISH', 'file/path', '001')
        self.assertEqual(data['rb_number'], '123')
        self.assertEqual(data['instrument'], 'WISH')
        self.assertEqual(data['data'], 'file/path')
        self.assertEqual(data['run_number'], '001')
        self.assertEqual(data['facility'], 'ISIS')

    # pylint:disable=no-self-use
    @patch('stomp.connect.StompConnection11.send')
    def test_send_data(self, mock_send):
        """ Test data can be sent without error """
        client = QueueClient()
        client.send('dataready', 'test-message')
        mock_send.assert_called_once()

    @patch('stomp.connect.StompConnection11.ack')
    def test_ack(self, mock_ack):
        client = QueueClient()
        client.connect()
        client.ack('test')
        mock_ack.assert_called_once_with('test')

    @patch('utils.clients.queue_client.QueueClient.subscribe_queues')
    def test_subscribe_to_pending(self, mock_subscribe):
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
        client = QueueClient()
        client.subscribe_autoreduce('consumer', None, 'auto')
        expected_args = {'queue_list': ['/queue/DataReady',
                                        '/queue/ReductionStarted',
                                        '/queue/ReductionComplete',
                                        '/queue/ReductionError'],
                         'ack': 'auto',
                         'listener': None,
                         'consumer_name': 'consumer'}
        mock_subscribe.assert_called_once_with(**expected_args)

    @patch('stomp.connect.StompConnection11.set_listener')
    @patch('stomp.connect.StompConnection11.subscribe')
    def test_subscribe_to_queue(self, mock_subscribe, mock_set_listener):
        client = QueueClient()
        client.connect()
        client.subscribe_queues(['test', 'queues'], 'consumer', None, 'auto')
        mock_set_listener.assert_called_once_with('consumer', None)
        test_expected_args = {'destination': 'test',
                              'id': '1',
                              'ack': 'auto',
                              'header': {'activemq.prefetchSize': '1'}}
        queue_expected_args = {'destination': 'queues',
                               'id': '1',
                               'ack': 'auto',
                               'header': {'activemq.prefetchSize': '1'}}
        mock_subscribe.assert_has_calls([call(**test_expected_args), call(**queue_expected_args)])
