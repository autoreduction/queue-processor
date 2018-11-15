import unittest

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



