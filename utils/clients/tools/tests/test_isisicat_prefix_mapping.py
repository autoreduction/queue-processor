# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test ICAT prefix mapping
"""
import unittest
from unittest.mock import patch

from utils.clients.tools.isisicat_prefix_mapping import fetch_instrument_fullname_mappings


class MockInstrumentQueryResult:
    """
    Mocks result of isisicat_prefix_mapping.client.execute_query for an instrument
    """

    def __init__(self, name, full_name):
        self.name = name
        self.fullName = full_name


class TestICATPrefixMappings(unittest.TestCase):
    """
    Test ICAT prefix mapping
    """

    @patch('icat.Client.__init__', return_value=None)
    @patch('utils.clients.tools.isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES',
           ['ENGINGX'])
    @patch('utils.clients.icat_client.ICATClient.execute_query')
    def test_fetch_instrument_fullname_mappings_executes_icat_query(self, mock_exe, _):
        """
        Test: If fetch_instrument_fullname_mappings executes a query from an instrument in
              utils.settings.VALID_INSTRUMENTS
        When: Testing if fetch_instrument_fullname_mappings executes a ICAT query
        """
        fetch_instrument_fullname_mappings()
        mock_exe.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch('utils.clients.tools.isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES',
           ['UNVALIDINSTUMENT'])
    @patch('logging.Logger.warning')
    @patch('utils.clients.icat_client.ICATClient.execute_query')
    def test_fetch_instrument_fullname_mappings_log_invalid_instrument(self, mock_exe,
                                                                       mock_logger_warning, _):
        """
        Test: If invalid instrument name in utils.settings.VALID_INSTRUMENTS is logged as not found
        When: Testing if fetch_instrument_fullname_mappings picks up invalid instruments
        """
        mock_exe.side_effect = Exception()

        fetch_instrument_fullname_mappings()
        mock_logger_warning.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch("utils.clients.tools.isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES",
           ["ENGINX", "GEM"])
    @patch('utils.clients.icat_client.ICATClient.execute_query',
           return_value=[MockInstrumentQueryResult("N", "FN")])
    def test_icat_prefix_mappings_length(self, _mock_instruments, _mock_exe):
        """
        Test: fetch_instrument_fullname_mappings produces the same number of results as stored in
              utils.settings.VALID_INSTRUMENTS
        When: Called when testing to see if the correct number of instruments in prefix mapping
        """
        prefix_map = fetch_instrument_fullname_mappings()
        self.assertEqual(2, len(prefix_map.keys()))

    @patch('icat.Client.__init__', return_value=None)
    @patch('utils.clients.icat_client.ICATClient.execute_query')
    @patch("utils.clients.tools.isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES", ["ENGINX"])
    def test_icat_prefix_mappings(self, mock_exe, _):
        """
        Test: If fetch_instrument_fullname_mappings properly maps instrument names map to ICAT
              instrument prefixes using utils.settings.VALID_INSTRUMENTS
        When: Called when testing correct mappings
        """
        icat_test_instrument = ("ENG", "ENGINX")
        mock_exe.return_value = [MockInstrumentQueryResult(*icat_test_instrument)]

        prefix_map = fetch_instrument_fullname_mappings()
        self.assertEqual(icat_test_instrument[0], prefix_map[icat_test_instrument[1]])
