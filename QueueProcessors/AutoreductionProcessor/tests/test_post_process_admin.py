import unittest
import os
import shutil

import json
from tempfile import mkdtemp
from mock import patch, call, Mock

from utils.settings import ACTIVEMQ_SETTINGS
from QueueProcessors.AutoreductionProcessor.settings import MISC
from QueueProcessors.AutoreductionProcessor.post_process_admin import (linux_to_windows_path,
                                                                       windows_to_linux_path,
                                                                       prettify,
                                                                       channels_redirected,
                                                                       PostProcessAdmin)


class TestPostProcessAdminHelpers(unittest.TestCase):

    def test_linux_to_windows_path(self):
        linux_path = "/isis/some/more/path.nxs"
        actual = linux_to_windows_path(linux_path)
        self.assertEqual(actual, "\\\\isis\\inst$\\some\\more\\path.nxs")

    def test_windows_to_linux_data_path(self):
        windows_path = "\\\\isis\\inst$\\some\\more\\path.nxs"
        actual = windows_to_linux_path(windows_path, '')
        self.assertEqual(actual, '/isis/some/more/path.nxs')

    def test_windows_to_linux_autoreduce_path(self):
        windows_path = "\\\\autoreduce\\data\\some\\more\\path.nxs"
        actual = windows_to_linux_path(windows_path, '/temp')
        self.assertEqual(actual, '/temp/data/some/more/path.nxs')


class TestPostProcessAdmin(unittest.TestCase):

    def setUp(self):
        self.data = {'data': '\\\\isis\\inst$\\data.nxs',
                     'facility': 'ISIS',
                     'instrument': 'GEM',
                     'rb_number': '1234',
                     'run_number': '4321',
                     'reduction_script': 'print(\'hello\')',
                     'reduction_arguments': 'None'}

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
        # ToDo: Should use archive explorer
        location = PostProcessAdmin._reduction_script_location('WISH')
        self.assertEqual(location, MISC['scripts_directory'] % 'WISH')

    @patch('QueueProcessors.AutoreductionProcessor.post_process_admin.PostProcessAdmin._remove_directory')
    @patch('QueueProcessors.AutoreductionProcessor.post_process_admin.PostProcessAdmin._copy_tree')
    @patch('QueueProcessors.AutoreductionProcessor.autoreduction_logging_setup.logger.info')
    def test_copy_temp_dir(self, mock_logger, mock_copy, mock_remove):
        result_dir = mkdtemp()
        copy_dir = mkdtemp()
        ppa = PostProcessAdmin(self.data, None)
        ppa.instrument = 'POLARIS'
        ppa.data['reduction_data'] = ['']
        ppa.copy_temp_directory(result_dir, copy_dir)
        mock_remove.assert_called_once_with(copy_dir)
        mock_logger.assert_called_once_with("Moving %s to %s", result_dir, copy_dir)
        mock_copy.assert_called_once_with(result_dir, copy_dir)
        shutil.rmtree(result_dir)
        shutil.rmtree(copy_dir)

    @patch('QueueProcessors.AutoreductionProcessor.post_process_admin.PostProcessAdmin._copy_tree')
    @patch('QueueProcessors.AutoreductionProcessor.autoreduction_logging_setup.logger.info')
    def test_copy_temp_dir_with_excitation(self, _, mock_copy):
        result_dir = mkdtemp()
        ppa = PostProcessAdmin(self.data, None)
        ppa.instrument = 'WISH'
        ppa.data['reduction_data'] = ['']
        ppa.copy_temp_directory(result_dir, 'copy-dir')
        mock_copy.assert_called_once_with(result_dir, 'copy-dir')
        shutil.rmtree(result_dir)

    @patch('QueueProcessors.AutoreductionProcessor.post_process_admin.PostProcessAdmin._copy_tree')
    @patch('QueueProcessors.AutoreductionProcessor.post_process_admin.PostProcessAdmin.log_and_message')
    @patch('QueueProcessors.AutoreductionProcessor.autoreduction_logging_setup.logger.info')
    def test_copy_temp_dir_with_error(self, _, mock_log_and_msg, mock_copy):
        def raise_runtime(arg1, arg2):  # pragma : no cover
            raise RuntimeError('test')
        mock_copy.side_effect = raise_runtime
        result_dir = mkdtemp()
        ppa = PostProcessAdmin(self.data, None)
        ppa.instrument = 'WISH'
        ppa.data['reduction_data'] = ['']
        ppa.copy_temp_directory(result_dir, 'copy-dir')
        mock_log_and_msg.assert_called_once_with("Unable to copy to %s - %s" % ('copy-dir', 'test'))
        shutil.rmtree(result_dir)

    @patch('QueueProcessors.AutoreductionProcessor.autoreduction_logging_setup.logger.info')
    def test_send_error_and_log(self, mock_logger):
        activemq_client_mock = Mock()
        ppa = PostProcessAdmin(self.data, activemq_client_mock)
        ppa._send_error_and_log()
        mock_logger.assert_called_once_with("\nCalling " + ACTIVEMQ_SETTINGS.reduction_error
                                            + " --- " + prettify(self.data))
        activemq_client_mock.send.assert_called_once_with(ACTIVEMQ_SETTINGS.reduction_error,
                                                          json.dumps(ppa.data))

    @patch('shutil.rmtree')
    @patch('QueueProcessors.AutoreductionProcessor.autoreduction_logging_setup.logger.info')
    def test_delete_temp_dir_valid(self, mock_logger, mock_remove_dir):
        temp_dir = mkdtemp()
        PostProcessAdmin.delete_temp_directory(temp_dir)
        rm_args = {'ignore_errors': True}
        mock_remove_dir.assert_called_once_with(temp_dir, **rm_args)
        mock_logger.assert_called_once_with('Remove temp dir %s', temp_dir)
        shutil.rmtree(temp_dir)

    @patch('shutil.rmtree')
    @patch('QueueProcessors.AutoreductionProcessor.autoreduction_logging_setup.logger.info')
    def test_delete_temp_dir_invalid(self, mock_logger, mock_remove_dir):
        def raise_runtime():  # pragma: no cover
            raise RuntimeError('test')
        mock_remove_dir.side_effect = raise_runtime
        PostProcessAdmin.delete_temp_directory('not-a-file-path.test')
        mock_logger.assert_has_calls([call('Remove temp dir %s', 'not-a-file-path.test'),
                                      call('Unable to remove temporary directory - %s',
                                           'not-a-file-path.test')])

    @patch('QueueProcessors.AutoreductionProcessor.autoreduction_logging_setup.logger.info')
    def test_empty_log_and_message(self, mock_logger):
        ppa = PostProcessAdmin(self.data, None)
        ppa.data['message'] = ''
        ppa.log_and_message('test')
        self.assertEqual(ppa.data['message'], 'test')
        mock_logger.assert_called_once_with('test')

    @patch('QueueProcessors.AutoreductionProcessor.autoreduction_logging_setup.logger.info')
    def test_load_and_message_with_preexisting_message(self, mock_logger):
        ppa = PostProcessAdmin(self.data, None)
        ppa.data['message'] = 'Old message'
        ppa.log_and_message('New message')
        self.assertEqual(ppa.data['message'], 'Old message')
        mock_logger.assert_called_once_with('New message')

    def test_remove_with_wait(self):
        pass

    def test_copy_tree(self):
        pass

    def test_remove_directory(self):
        pass
