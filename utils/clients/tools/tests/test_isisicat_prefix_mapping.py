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

from utils.clients.tools.isisicat_prefix_mapping import fetch_instrument_fullname_mapping


# pylint:disable=no-self-use,too-few-public-methods,too-many-public-methods
class MockInstrumentQueryResult:
    """
    Mocks result of isisicat_prefix_mapping.client.execute_query for an instrument
    """

    def __init__(self, name, full_name):
        self.name = name
        self.fullName = full_name  # pylint:disable=invalid-name


class TestICATPrefixMapping(unittest.TestCase):
    """
    Test ICAT prefix mapping
    """

    @patch('icat.Client.__init__', return_value=None)
    @patch('utils.clients.tools.isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES',
           ['ENGINGX'])
    @patch('utils.clients.icat_client.ICATClient.execute_query')
    def test_fetch_instrument_fullname_mapping_executes_icat_query(self, mock_execute_query, _):
        """
        Test: If instruments are fetched through a query
        When: Testing if fetch_instrument_fullname_mapping executes an ICAT query
        """
        fetch_instrument_fullname_mapping()
        mock_execute_query.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch('utils.clients.tools.isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES',
           ['INVALIDINSTUMENT'])
    @patch('logging.Logger.warning')
    @patch('utils.clients.icat_client.ICATClient.execute_query',
           returns_value=[MockInstrumentQueryResult("ABCDE", "ABC")])
    def test_fetch_instrument_fullname_mapping_log_invalid_instrument(self, _mock_execute_query,
                                                                      mock_logger_warning, _):
        """
        Test: If invalid instrument name in utils.settings.VALID_INSTRUMENTS is logged as not found
        When: Testing if fetch_instrument_fullname_mapping picks up invalid instruments
        """
        fetch_instrument_fullname_mapping()
        mock_logger_warning.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch("utils.clients.tools.isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES",
           ["ENGINX", "GEM"])
    @patch('utils.clients.icat_client.ICATClient.execute_query',
           return_value=[MockInstrumentQueryResult("ENG", "ENGINX"),
                         MockInstrumentQueryResult("GEM", "GEM")])
    def test_icat_prefix_mapping_length(self, _mock_instruments, _mock_execute_query):
        """
        Test: fetch_instrument_fullname_mapping produces the same number of results as stored in
              utils.settings.VALID_INSTRUMENTS
        When: Called when testing to see if the correct number of instruments in prefix mapping
        """
        prefix_map = fetch_instrument_fullname_mapping()
        self.assertEqual(2, len(prefix_map.keys()))

    @patch('icat.Client.__init__', return_value=None)
    @patch('utils.clients.icat_client.ICATClient.execute_query')
    @patch("utils.clients.tools.isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES", ["ENGINX"])
    def test_icat_prefix_mapping(self, mock_execute_query, _):
        """
        Test: If fetch_instrument_fullname_mapping properly maps instrument names map to ICAT
              instrument prefixes using utils.settings.VALID_INSTRUMENTS
        When: Called when testing correct mapping
        """
        icat_test_instrument = ("ENG", "ENGINX")
        mock_execute_query.return_value = [MockInstrumentQueryResult(*icat_test_instrument)]

        prefix_map = fetch_instrument_fullname_mapping()
        self.assertEqual(icat_test_instrument[0], prefix_map[icat_test_instrument[1]])
