import unittest

from utils.instruments import EnginX


class TestEnginX(unittest.TestCase):

    def setUp(self):
        self.enginx = EnginX(True, '{}{}')

    def test_name(self):
        self.assertEqual(self.enginx.name, 'ENGINX')

    def test_format_output_directory(self):
        meta_data = {
            'rb': '12345'
        }
        self.assertEqual(self.enginx.format_output_directory(meta_data), 'ENGINX12345')
