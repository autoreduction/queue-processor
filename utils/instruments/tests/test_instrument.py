import unittest

from utils.instruments import Instrument


class TestInstrument(unittest.TestCase):

    def setUp(self):
        self.instrument = Instrument('Test', True, '{}{}-{}')

    def test_init(self):
        self.assertEqual(self.instrument.name, 'Test')
        self.assertTrue(self.instrument.use_nexus)
        self.assertEqual(self.instrument.output_directory, '{}{}-{}')

    def test_format_output_directory(self):
        meta_data = {
            'rb': '12345',
            'run': '00000'
        }
        self.assertEqual(self.instrument.format_output_directory(meta_data), 'Test12345-00000')
