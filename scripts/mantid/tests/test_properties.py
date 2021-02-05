# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test that the Mantid properties file is generated correctly
"""
import unittest
import os

from scripts.mantid.properties import generate_mantid_properties_file


class TestProperties(unittest.TestCase):
    """
    Ensure that the Mantid Properties script is generated correctly
    """
    def setUp(self):
        """ Store the path that the Mantid Properties file will be written to """
        self.expected_path = os.path.join(os.getcwd(), 'Mantid.user.properties')

    def test_generate_default(self):
        """
        Test: A Mantid Properties file is generated that contains the default paths
        When: generate is called with no arguments
        """
        generate_mantid_properties_file()
        self.validate([r'/isis/NDXGEM/Instrument/data/cycle_19_3', r'/isis/NDXGEM/Instrument/data/cycle_19_4'])

    def test_instrument_subset(self):
        """
        Test: A Mantid Properties file is generated for a given set of instruments
        When: generate is called with an instruments argument
        """
        generate_mantid_properties_file(instruments=['test', 'other'])
        self.validate([
            r'/isis/NDXtest/Instrument/data/cycle_19_3', r'/isis/NDXtest/Instrument/data/cycle_19_4',
            r'/isis/NDXother/Instrument/data/cycle_19_3', r'/isis/NDXother/Instrument/data/cycle_19_3'
        ])

    def test_cycle_subset(self):
        """
        Test: A Mantid Properties file is generated for a given set of years/cycles
        When: generate is called with a cycles argument
        """
        generate_mantid_properties_file(cycles=['11_1', '14_3'])
        self.validate([r'/isis/NDXGEM/Instrument/data/cycle_11_1', r'/isis/NDXGEM/Instrument/data/cycle_14_3'])

    def validate(self, should_exist):
        """
        Ensure that the file is generated at the expected
        location and contains the expected lines
        """
        self.assertTrue(os.path.exists(self.expected_path))
        with open(self.expected_path, 'r') as actual_file:
            actual_text = actual_file.readlines()
        actual_text = ''.join(actual_text)
        for line in should_exist:
            self.assertTrue(line in actual_text, '{} not found in {}'.format(line, actual_text))

    def tearDown(self):
        """ Delete the Mantid Properties file that was created """
        if os.path.exists(self.expected_path):
            os.remove(self.expected_path)
