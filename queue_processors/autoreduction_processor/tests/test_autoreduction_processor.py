# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for the autoreduction processor
This includes the Listener and Consumer class
"""
import unittest
import json
import os
import sys

from mock import patch, Mock, call

from queue_processors.autoreduction_processor.autoreduction_processor import (Listener,
                                                                              Consumer,
                                                                              main)
from queue_processors.autoreduction_processor.settings import MISC, ACTIVEMQ


# pylint:disable=missing-docstring,too-many-arguments,no-self-use,protected-access
class TestAutoreductionProcessorListener(unittest.TestCase):

    def setUp(self):
        self.listener = Listener(None)
        self.headers = {'destination': '/queue/topic',
                        'priority': '1',
                        'message-id': 'test-id',
                        'subscription': '/queue/subscription'}
        self.data = {'cancel': False,
                     'reduction_script': 'test',
                     'rb_number': '222',
                     'run_number': '111',
                     'run_version': None}
        self.json_data = json.dumps(self.data)

    def test_init(self):
        listener = Listener(None)
        self.assertIsNone(listener._client)
        self.assertEqual(listener.proc_list, [])
        self.assertEqual(listener.rb_list, [])
        self.assertEqual(listener.cancel_list, [])

    @patch('queue_processors.autoreduction_processor.autoreduction_logging_setup.logger.error')
    def test_on_error(self, mock_err_log):
        self.listener.on_error('test error')
        mock_err_log.assert_called_once_with("Error message received - %s", 'test error')

    @patch('queue_processors.autoreduction_processor.autoreduction_processor.Listener.hold_message')
    def test_on_message(self, mock_hold_message):
        self.listener.on_message(self.headers, self.json_data)
        mock_hold_message.assert_called_once_with('/queue/topic', self.json_data, self.headers)

    @patch('queue_processors.autoreduction_processor.autoreduction_processor.Listener.add_cancel')
    def test_on_message_cancel(self, mock_add_cancel):
        self.data['cancel'] = True
        self.listener.on_message(self.headers, json.dumps(self.data))
        mock_add_cancel.assert_called_once_with(self.data)

    if os.name != 'nt':  # pragma: no cover
        @patch('queue_processors.autoreduction_processor.'
               'autoreduction_processor.Listener.should_proceed',
               return_value=False)
        @patch('twisted.internet.reactor.callLater')
        def test_hold_message_no_proceed(self, mock_call_later, mock_should_proceed):
            self.listener.hold_message('/queue/topic', self.json_data, self.headers)
            mock_should_proceed.assert_called_once()
            mock_call_later.assert_called_once_with(10, self.listener.hold_message,
                                                    '/queue/topic', self.json_data,
                                                    self.headers)

    @patch('queue_processors.autoreduction_processor.autoreduction_processor.'
           'Listener.should_proceed', return_value=True)
    @patch('queue_processors.autoreduction_processor.autoreduction_processor.'
           'Listener.should_cancel', return_value=True)
    @patch('queue_processors.autoreduction_processor.autoreduction_processor.Listener.cancel_run')
    def test_hold_message_cancel(self, mock_cancel_run, mock_should_cancel, mock_should_proceed):
        self.listener.hold_message('/queue/topic', self.json_data, self.headers)
        mock_should_proceed.assert_called_once()
        mock_should_cancel.assert_called_once()
        mock_cancel_run.assert_called_once_with(self.data)

    @patch('queue_processors.autoreduction_processor.autoreduction_processor.Listener.add_process')
    @patch('subprocess.Popen')
    @patch('queue_processors.autoreduction_processor.autoreduction_logging_setup.logger.warning')
    @patch('queue_processors.autoreduction_processor.autoreduction_processor.'
           'Listener.should_proceed', return_value=True)
    @patch('queue_processors.autoreduction_processor.autoreduction_processor.'
           'Listener.should_cancel', return_value=False)
    @patch('os.path.isfile', return_value=False)
    def test_hold_message_invalid_dir(self, mock_is_file, mock_should_cancel, mock_should_proceed,
                                      mock_log, mock_popen, mock_add_process):
        mock_client = Mock()
        listener = Listener(mock_client)
        listener.hold_message('/queue/topic', self.json_data, self.headers)
        mock_should_cancel.assert_called_once()
        mock_should_proceed.assert_called_once()
        mock_is_file.assert_called_once()
        mock_log.assert_called_once_with("Could not find autoreduction post processing file -"
                                         " please contact a system administrator")
        mock_client.ack.assert_called_once_with(self.headers['message-id'],
                                                self.headers['subscription'])
        mock_popen.assert_called_once_with([sys.executable,
                                            MISC['post_process_directory'],
                                            self.headers['destination'],
                                            self.json_data])
        mock_add_process.assert_called_once()

    def test_update_child_process_list(self):
        proc_one = Mock()
        proc_two = Mock()
        proc_one.poll = Mock(return_value=None)
        proc_two.poll = Mock(return_value='something')
        self.listener.proc_list = [proc_one, proc_two]
        self.listener.rb_list = ['888', '999']
        self.listener.update_child_process_list()
        self.assertEqual(self.listener.proc_list, [proc_one])
        self.assertEqual(self.listener.rb_list, ['888'])

    def test_add_process(self):
        self.listener.add_process('fake-process', self.data)
        self.assertEqual(self.listener.proc_list, ['fake-process'])
        self.assertEqual(self.listener.rb_list, [self.data['rb_number']])

    def test_should_proceed_false(self):
        self.listener.rb_list = [self.data['rb_number']]
        self.assertFalse(self.listener.should_proceed(self.data))

    def test_should_proceed_true(self):
        self.assertTrue(self.listener.should_proceed(self.data))

    def test_run_tuple_no_version(self):
        self.assertEqual(('111', 0), self.listener.run_tuple(self.data))

    def test_run_tuple_with_version(self):
        self.data['run_version'] = '1'
        self.assertEqual(('111', '1'), self.listener.run_tuple(self.data))

    def test_add_cancel(self):
        self.listener.add_cancel(self.data)
        self.assertEqual(self.listener.cancel_list, [(self.data['run_number'], 0)])

    def test_add_cancel_when_exists(self):
        """ Ensure that runs are not duplicated in the cancel list """
        self.listener.cancel_list = [(self.data['run_number'], 0)]
        self.listener.add_cancel(self.data)
        self.assertEqual(self.listener.cancel_list, [(self.data['run_number'], 0)])

    def test_should_cancel_false(self):
        self.assertFalse(self.listener.should_cancel(self.data))

    def test_should_cancel_true(self):
        self.listener.cancel_list = [(self.data['run_number'], 0)]
        self.assertTrue(self.listener.should_cancel(self.data))

    def test_cancel_run(self):
        self.listener.cancel_list = [(self.data['run_number'], 0)]
        self.listener.cancel_run(self.data)
        self.assertEqual(self.listener.cancel_list, [])


# pylint:disable=missing-docstring
class TestAutoReductionProcessorConsumer(unittest.TestCase):    # <stomp>

    def setUp(self):
        self.consumer = Consumer()

    def test_init(self):
        self.assertEqual(self.consumer.consumer_name, 'queueProcessor')

    @patch('stomp.Connection.subscribe')
    @patch('stomp.Connection.connect')
    @patch('stomp.Connection.set_listener')
    @patch('stomp.Connection.__init__', return_value=None)
    def test_run(self, mock_connection, mock_set_listener,
                 mock_connect, mock_subscribe):
        self.consumer.run()
        init_args = {'host_and_ports': [(ACTIVEMQ['brokers'].split(':')[0],
                                         int(ACTIVEMQ['brokers'].split(':')[1]))],
                     'use_ssl': False}
        mock_connection.assert_called_once_with(**init_args)
        mock_set_listener.assert_called_once()
        connect_args = {'wait': False,
                        'header': {'activemq.prefetchSize': '1'}}
        mock_connect.assert_called_once_with(ACTIVEMQ['amq_user'],
                                             ACTIVEMQ['amq_pwd'],
                                             **connect_args)
        subcription_calls = []
        for queue in ACTIVEMQ['amq_queues']:
            subscribe_args = {'destination': queue,
                              'id': '1',
                              'ack': 'client-individual',
                              'header': {'activemq.prefetchSize': '1'}
                             }
            subcription_calls.append(call(**subscribe_args))
        mock_subscribe.assert_has_calls(subcription_calls)


if os.name != 'nt':  # pragma: no cover
    class TestAutoreductionProcessor(unittest.TestCase):

        @patch('twisted.internet.reactor.run')
        @patch('twisted.internet.reactor.callWhenRunning')
        def test_main(self, mock_call_when_running, mock_run):
            main()
            mock_call_when_running.assert_called_once()
            mock_run.assert_called_once()
