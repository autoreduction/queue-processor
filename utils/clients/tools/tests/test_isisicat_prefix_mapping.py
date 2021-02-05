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

from utils.clients.tools.isisicat_prefix_mapping import get_icat_instrument_prefix


# pylint:disable=no-self-use,too-few-public-methods,too-many-public-methods
class MockInstrumentQueryResult:
    """
    Mocks result of isisicat_prefix_mapping.client.execute_query for an instrument
    """
    def __init__(self, name, full_name):
        self.name = name
        # camelCase used due to mocking of external class
        self.fullName = full_name  # pylint:disable=invalid-name


class TestICATPrefixMapping(unittest.TestCase):
    """
    Test ICAT prefix mapping
    """
    DIR = "utils.clients.tools.isisicat_prefix_mapping"

    @patch('icat.Client.__init__', return_value=None)
    @patch('utils.clients.icat_client.ICATClient.execute_query',
           return_value=[MockInstrumentQueryResult("ENG", "ENGINX")])
    def test_get_icat_instrument_prefix_executes_icat_query(self, mock_execute_query, _):
        """
        Test: If instruments are fetched through a query
        When: Testing if get_icat_instrument_prefix executes an ICAT query
        """
        self.assertEqual("ENG", get_icat_instrument_prefix("ENGINX"))
        mock_execute_query.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch('utils.clients.icat_client.ICATClient.execute_query', side_effect=Exception)
    def test_get_icat_instrument_prefix_icat_query_raises(self, mock_execute_query, _):
        """
        Test: If the query raises due to a connection issue or wrong credentials
        When: Testing if get_icat_instrument_prefix executes an ICAT query
        """
        self.assertRaises(RuntimeError, get_icat_instrument_prefix, "ENGINX")
        mock_execute_query.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch('logging.Logger.warning')
    @patch('utils.clients.icat_client.ICATClient.execute_query',
           return_value=[MockInstrumentQueryResult("ENG", "ENGINX")])
    def test_get_icat_instrument_prefix_log_invalid_instrument(self, _mock_execute_query, mock_logger_warning, _):
        """
        Test: If invalid instrument name in utils.settings.VALID_INSTRUMENTS is logged as not found
        When: Testing if get_icat_instrument_prefix picks up invalid instruments
        """
        self.assertRaises(RuntimeError, get_icat_instrument_prefix, "INVALIDINSTRUMENT")
        mock_logger_warning.assert_called_once()
