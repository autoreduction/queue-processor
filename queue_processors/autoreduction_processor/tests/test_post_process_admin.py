# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for post process admin and helper functionality
"""
import unittest
import os
import shutil
import sys

import json
from tempfile import mkdtemp, NamedTemporaryFile
from mock import patch, call, Mock

from message.job import Message
from paths.path_manipulation import append_path
from utils.settings import ACTIVEMQ_SETTINGS
from utils.project.structure import get_project_root
from queue_processors.autoreduction_processor.settings import MISC
from queue_processors.autoreduction_processor.post_process_admin import (windows_to_linux_path,
                                                                         prettify,
                                                                         PostProcessAdmin,
                                                                         main)


# pylint:disable=missing-docstring,invalid-name,protected-access,no-self-use,too-many-arguments
class TestPostProcessAdminHelpers(unittest.TestCase):

    def test_windows_to_linux_data_path(self):
        windows_path = "\\\\isis\\inst$\\some\\more\\path.nxs"
        actual = windows_to_linux_path(windows_path, '')
        self.assertEqual(actual, '/isis/some/more/path.nxs')

    def test_windows_to_linux_autoreduce_path(self):
        windows_path = "\\\\autoreduce\\data\\some\\more\\path.nxs"
        actual = windows_to_linux_path(windows_path, '/temp')
        self.assertEqual(actual, '/temp/data/some/more/path.nxs')


# pylint:disable=too-many-public-methods
class TestPostProcessAdmin(unittest.TestCase):
    DIR = "queue_processors.autoreduction_processor"

    def setUp(self):
        self.data = {'data': '\\\\isis\\inst$\\data.nxs',
                     'facility': 'ISIS',
                     'instrument': 'GEM',
                     'rb_number': '1234',
                     'run_number': '4321',
                     'reduction_script': 'print(\'hello\')',
                     'reduction_arguments': 'None'}
        self.test_fname = "111.txt"
        self.test_root = os.path.join("instrument", "GEM", "RBNumber",
                                      "RB2010163", "autoreduced", "111")
        self.test_paths = [os.path.join(self.test_root, "0"),
                           os.path.join(self.test_root, "1"),
                           os.path.join(self.test_root, "2")]
        self.message = Message()
        self.message.populate(self.data)

    def tearDown(self):
        self.teardown_test_dir_structure()

    def teardown_test_dir_structure(self):
        """
        Removes test directory structure (if one exists) from the root
        """
        abs_test_root = os.path.join(os.getcwd(), self.test_root)
        if os.path.isdir(abs_test_root):
            shutil.rmtree(self.test_root)

    def setup_test_dir_structure(self, test_dirs):
        """
        Sets up a directory structure within the test environment.
        Writes a file within each each directory given
        :param test_dirs: The directories to create
        """
        for d in test_dirs:
            abs_dir = os.path.join(os.getcwd(), d)
            if not os.path.isdir(abs_dir):
                os.makedirs(abs_dir)

            abs_path = os.path.join(abs_dir, self.test_fname)
            with open(abs_path, 'w') as file:
                file.write("test file")

    def test_init(self):
        ppa = PostProcessAdmin(self.data, None)
        self.assertEqual(ppa.data, self.data)
        self.assertEqual(ppa.client, None)
        self.assertIsNotNone(ppa.reduction_log_stream)
        self.assertIsNotNone(ppa.admin_log_stream)

        self.assertEqual(ppa.data_file, '/isis/data.nxs')
        self.assertEqual(ppa.facility, 'ISIS')
        self.assertEqual(ppa.instrument, 'GEM')
        self.assertEqual(ppa.proposal, '1234')
        self.assertEqual(ppa.run_number, '4321')
        self.assertEqual(ppa.reduction_script, 'print(\'hello\')')
        self.assertEqual(ppa.reduction_arguments, 'None')

    def test_replace_variables(self):
        pass

    def test_load_reduction_script(self):
        ppa = PostProcessAdmin(self.data, None)
        file_path = ppa._load_reduction_script('WISH')
        self.assertEqual(file_path, os.path.join(MISC['scripts_directory'] % 'WISH',
                                                 'reduce.py'))

    def test_reduction_script_location(self):
        location = PostProcessAdmin._reduction_script_location('WISH')
        self.assertEqual(location, MISC['scripts_directory'] % 'WISH')

    @patch(DIR + '.post_process_admin.PostProcessAdmin._remove_directory')
    @patch(DIR + '.post_process_admin.PostProcessAdmin._copy_tree')
    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    def test_copy_temp_dir(self, mock_logger, mock_copy, mock_remove):
        result_dir = mkdtemp()
        copy_dir = mkdtemp()
        ppa = PostProcessAdmin(self.data, None)
        ppa.instrument = 'POLARIS'
        ppa.data['reduction_data'] = ['']
        ppa.copy_temp_directory(result_dir, copy_dir)
        mock_remove.assert_called_once_with(copy_dir)
        mock_logger.assert_called_with("Moving %s to %s", result_dir, copy_dir)
        mock_copy.assert_called_once_with(result_dir, copy_dir)
        shutil.rmtree(result_dir)
        shutil.rmtree(copy_dir)

    @patch(DIR + '.post_process_admin.PostProcessAdmin._copy_tree')
    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    def test_copy_temp_dir_with_excitation(self, _, mock_copy):
        result_dir = mkdtemp()
        ppa = PostProcessAdmin(self.data, None)
        ppa.instrument = 'WISH'
        ppa.data['reduction_data'] = ['']
        ppa.copy_temp_directory(result_dir, 'copy-dir')
        mock_copy.assert_called_once_with(result_dir, 'copy-dir')
        shutil.rmtree(result_dir)

    @patch(DIR + '.post_process_admin.PostProcessAdmin._copy_tree')
    @patch(DIR + '.post_process_admin.PostProcessAdmin.log_and_message')
    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    def test_copy_temp_dir_with_error(self, _, mock_log_and_msg, mock_copy):
        # pylint:disable=unused-argument
        def raise_runtime(arg1, arg2):  # pragma : no cover
            raise RuntimeError('test')
        mock_copy.side_effect = raise_runtime
        result_dir = mkdtemp()
        ppa = PostProcessAdmin(self.data, None)
        ppa.instrument = 'WISH'
        ppa.data['reduction_data'] = ['']
        ppa.copy_temp_directory(result_dir, 'copy-dir')
        mock_log_and_msg.assert_called_once_with("Unable to copy to %s - %s" % ('copy-dir',
                                                                                'test'))
        shutil.rmtree(result_dir)

    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    def test_send_error_and_log(self, mock_logger):
        activemq_client_mock = Mock()
        ppa = PostProcessAdmin(self.data, activemq_client_mock)
        ppa._send_message_and_log(ACTIVEMQ_SETTINGS.reduction_error)
        mock_logger.assert_called_with("\nCalling " + ACTIVEMQ_SETTINGS.reduction_error +
                                       " --- " + prettify(self.data))
        activemq_client_mock.send.assert_called_once_with(ACTIVEMQ_SETTINGS.reduction_error,
                                                          json.dumps(ppa.data))

    @patch('shutil.rmtree')
    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    def test_delete_temp_dir_valid(self, mock_logger, mock_remove_dir):
        temp_dir = mkdtemp()
        PostProcessAdmin.delete_temp_directory(temp_dir)
        rm_args = {'ignore_errors': True}
        mock_remove_dir.assert_called_once_with(temp_dir, **rm_args)
        mock_logger.assert_called_once_with('Remove temp dir %s', temp_dir)
        shutil.rmtree(temp_dir)

    @patch('shutil.rmtree')
    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    def test_delete_temp_dir_invalid(self, mock_logger, mock_remove_dir):
        def raise_runtime():  # pragma: no cover
            raise RuntimeError('test')
        mock_remove_dir.side_effect = raise_runtime
        PostProcessAdmin.delete_temp_directory('not-a-file-path.test')
        mock_logger.assert_has_calls([call('Remove temp dir %s', 'not-a-file-path.test'),
                                      call('Unable to remove temporary directory - %s',
                                           'not-a-file-path.test')])

    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    def test_empty_log_and_message(self, mock_logger):
        ppa = PostProcessAdmin(self.data, None)
        ppa.data['message'] = ''
        ppa.log_and_message('test')
        self.assertEqual(ppa.data['message'], 'test')
        mock_logger.assert_called_with('test')

    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    def test_load_and_message_with_preexisting_message(self, mock_logger):
        ppa = PostProcessAdmin(self.data, None)
        ppa.data['message'] = 'Old message'
        ppa.log_and_message('New message')
        self.assertEqual(ppa.data['message'], 'Old message')
        mock_logger.assert_called_with('New message')

    def test_remove_with_wait_folder(self):
        directory_to_remove = mkdtemp()
        self.assertTrue(os.path.exists(directory_to_remove))
        ppa = PostProcessAdmin(self.data, None)
        ppa._remove_with_wait(True, directory_to_remove)
        self.assertFalse(os.path.exists(directory_to_remove))

    def test_remove_with_wait_file(self):
        file_to_remove = NamedTemporaryFile(delete=False).name
        self.assertTrue(os.path.exists(str(file_to_remove)))
        ppa = PostProcessAdmin(self.data, None)
        ppa._remove_with_wait(False, file_to_remove)
        self.assertFalse(os.path.exists(file_to_remove))

    def test_copy_tree_folder(self):
        directory_to_copy = mkdtemp(prefix='test-dir')
        with open(os.path.join(directory_to_copy, 'test-file.txt'), 'w+') as test_file:
            test_file.write('test content')
        ppa = PostProcessAdmin(self.data, None)
        ppa._copy_tree(directory_to_copy, os.path.join(get_project_root(), 'test-dir'))
        self.assertTrue(os.path.exists(os.path.join(get_project_root(), 'test-dir')))
        self.assertTrue(os.path.isdir(os.path.join(get_project_root(), 'test-dir')))
        self.assertTrue(os.path.exists(os.path.join(get_project_root(), 'test-dir',
                                                    'test-file.txt')))
        self.assertTrue(os.path.isfile(os.path.join(get_project_root(), 'test-dir',
                                                    'test-file.txt')))
        shutil.rmtree(os.path.join(get_project_root(), 'test-dir'))

    def test_remove_directory(self):
        directory_to_remove = mkdtemp()
        self.assertTrue(os.path.exists(directory_to_remove))
        ppa = PostProcessAdmin(self.data, None)
        ppa._remove_directory(directory_to_remove)
        self.assertFalse(os.path.exists(directory_to_remove))

    @patch(DIR + '.post_process_admin.windows_to_linux_path', return_value='path')
    @patch(DIR + '.post_process_admin.PostProcessAdmin.reduce')
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.__init__', return_value=None)
    def test_main(self, mock_init, mock_connect, mock_reduce, _):
        """
        Test: A QueueClient is initialised and connected and ppa.reduce is called
        When: The main method is called
        """
        sys.argv = ['', '/queue/ReductionPending', json.dumps(self.data)]
        main()
        mock_init.assert_called_once()
        mock_connect.assert_called_once()
        mock_reduce.assert_called_once()

    @patch(DIR + '.post_process_admin.prettify', return_value='test')
    @patch('sys.exit')
    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    @patch(DIR + '.post_process_admin.PostProcessAdmin.__init__', return_value=None)
    @patch('utils.clients.queue_client.QueueClient.send')
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.__init__', return_value=None)
    def test_main_inner_value_error(self, mock_client_init, mock_connect, mock_send, mock_ppa_init,
                                    mock_logger, mock_exit, _):
        """
        Test: The correct message is sent from the exception handlers in main
        When: A ValueError exception is raised from ppa.reduce
        """
        def raise_value_error(arg1, _):
            self.assertEqual(arg1, self.data)
            raise ValueError('error-message')
        mock_ppa_init.side_effect = raise_value_error
        sys.argv = ['', '/queue/ReductionPending', json.dumps(self.data)]
        main()
        mock_connect.assert_called_once()
        mock_client_init.assert_called_once()
        mock_logger.assert_has_calls([call('JSON data error: %s', 'test')])
        mock_exit.assert_called_once()
        self.data['error'] = 'error-message'
        mock_send.assert_called_once_with(ACTIVEMQ_SETTINGS.reduction_error,
                                          json.dumps(self.data))

    @patch('sys.exit')
    @patch(DIR + '.autoreduction_logging_setup.logger.info')
    @patch(DIR + '.post_process_admin.PostProcessAdmin.__init__', return_value=None)
    @patch('utils.clients.queue_client.QueueClient.send')
    @patch('utils.clients.queue_client.QueueClient.connect')
    @patch('utils.clients.queue_client.QueueClient.__init__', return_value=None)
    def test_main_inner_exception(self, mock_client_init, mock_connect, mock_send, mock_ppa_init,
                                  mock_logger, mock_exit):
        """
        Test: The correct message is sent from the exception handlers in main
        When: A bare Exception is raised from ppa.reduce
        """
        def raise_exception(arg1, _):
            self.assertEqual(arg1, self.data)
            raise Exception('error-message')
        mock_ppa_init.side_effect = raise_exception
        sys.argv = ['', '/queue/ReductionPending', json.dumps(self.data)]
        main()
        mock_connect.assert_called_once()
        mock_client_init.assert_called_once()
        mock_logger.assert_has_calls([call('PostProcessAdmin error: %s', 'error-message')])
        mock_exit.assert_called_once()
        mock_send.assert_called_once_with(ACTIVEMQ_SETTINGS.reduction_error,
                                          json.dumps(self.data))

    def test_new_reduction_data_path_no_overwrite_paths_exist(self):
        """
        Test: A path is returned with a final directory one higher than the current highest
        When: _new_reduction_data_path is called on an existing path with overwrite: None
        """
        self.setup_test_dir_structure(self.test_paths)
        mock_self = Mock()
        mock_self.data = {'overwrite': None}

        expected = append_path(self.test_root, "3")
        actual = PostProcessAdmin._new_reduction_data_path(mock_self, self.test_root)
        self.assertEqual(expected, actual)

    def test_new_reduction_data_path_overwrite_paths_exist(self):
        """
        Test: The given path is returned with a 0 directory appended
        When: _new_reduction_data_path is called on an existing path with overwrite: True
        """
        self.setup_test_dir_structure(self.test_paths)
        mock_self = Mock()
        mock_self.data = {'overwrite': True}

        expected = append_path(self.test_root, "0")
        actual = PostProcessAdmin._new_reduction_data_path(mock_self, self.test_root)
        self.assertEqual(expected, actual)

    def test_new_reduction_data_only_root_path_exists(self):
        """
        Test: The given path is returned with a 0 directory appended
        When: _new_reduction_data_path is called on a path without version sub-directories
        """
        self.setup_test_dir_structure([self.test_root])
        mock_self = Mock()
        mock_self.data = {'overwrite': None}

        expected = append_path(self.test_root, "0")
        actual = PostProcessAdmin._new_reduction_data_path(mock_self, self.test_root)
        self.assertEqual(expected, actual)

    @patch(DIR + '.post_process_admin.PostProcessAdmin.__init__', return_value=None)
    def test_check_message_attributes_populated_success(self, mock_ppa_init):
        mock_self = Mock()
        mock_self.message = self.message
        attributes = self.data.keys()
        actual = PostProcessAdmin.check_message_attributes_populated(mock_self, attributes)
        self.assertTrue(actual)

    @patch(DIR + '.post_process_admin.PostProcessAdmin.__init__', return_value=None)
    def test_check_message_attributes_populated_failure(self, mock_ppa_init):
        mock_self = Mock()
        mock_self.message = self.message
        attributes = self.data.keys()
        mock_self.message.facility = None

        actual = PostProcessAdmin.check_message_attributes_populated(mock_self, attributes)
        self.assertFalse(actual)
