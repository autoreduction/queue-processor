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
from mock import patch

from utils.settings import VALID_INSTRUMENTS
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

    #@patch('logging.Logger.warning')
    @patch("utils.clients.tools.isisicat_prefix_mapping")
    @patch("utils.clients.tools.isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES", ["ABCDE"])
    def test_prefix_mappings_num_instruments_not_found(self, mock_isisicat_prefix_mapping):
        """
        Test:
        When:
        """

        fetch_instrument_fullname_mappings()
        # mock_logger.assert_called_once()
        mock_isisicat_prefix_mapping.client.execute_query.assert_called_once()

    @patch("utils.clients.tools.isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES", ["ENGINX", "GEM"])
    def test_icat_prefix_mappings_length(self):
        """
        Test: ICAT_PREFIX_MAP produces the same number of results as stored in isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES
        When: Called when testing to see if the correct number of instruments is in ICAT_PREFIX_MAP
        """
        prefix_map = fetch_instrument_fullname_mappings()
        self.assertEqual(2, len(prefix_map.keys()))

    @patch("utils.clients.tools.isisicat_prefix_mapping")
    @patch("utils.clients.tools.isisicat_prefix_mapping.AUTOREDUCTION_INSTRUMENT_NAMES", ["ENGINX"])
    def test_icat_prefix_mappings(self, mock_isisicat_prefix_mapping):
        """
        Test: If a selection of instrument names map to ICAT instrument prefixes using ICAT_PREFIX_MAP
        When: Called when testing correct mappings
        """
        icat_test_instrument = ("ENGINX", "ENG")
        mock_isisicat_prefix_mapping.client.execute_query.return_value = MockInstrumentQueryResult(
            *icat_test_instrument)

        prefix_map = fetch_instrument_fullname_mappings()
        self.assertEqual(icat_test_instrument[1], prefix_map[icat_test_instrument[0]])
