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

from utils.clients.tools.isisicat_prefix_mapping import ICAT_PREFIX_MAP
from utils.settings import VALID_INSTRUMENTS as AUTOREDUCTION_INSTRUMENT_NAMES


class TestICATPrefixMappings(unittest.TestCase):
    """
    Test ICAT prefix mapping
    """

    def test_icat_prefix_mappings_produces_correct_amount(self):
        """
        Test: ICAT_PREFIX_MAP produces the same number of results as utils.settings.VALID_INSTRUMENTS
        When: Called when testing to see if the correct number of instruments is in ICAT_PREFIX_MAP
        """
        self.assertEqual(len(ICAT_PREFIX_MAP.keys()), len(AUTOREDUCTION_INSTRUMENT_NAMES))

    def test_icat_prefix_mappings(self):
        """
        Test: ICAT_PREFIX_MAP maps all Autoreduction instruments to ICAT instrument prefixes
        When: Called when testing correct mappings
        """
        ICAT_INSTRUMENTS_MOCK_QUERY_RESULTS = {
            "ENG": MockInstrumentQueryResult("ENGINX"),
            "GEM": MockInstrumentQueryResult("GEM"),
            "HRP": MockInstrumentQueryResult("HRPD"),
            "MAP": MockInstrumentQueryResult("MAPS"),
            "MAR": MockInstrumentQueryResult("MARI"),
            "MUSR": MockInstrumentQueryResult("MUSR"),
            "OSI": MockInstrumentQueryResult("OSIRIS"),
            "POL": MockInstrumentQueryResult("POLARIS"),
            "POLREF": MockInstrumentQueryResult("POLREF"),
            "WISH": MockInstrumentQueryResult("WISH"),
        }

        for autoreduction_instrument_name in AUTOREDUCTION_INSTRUMENT_NAMES:
            instrument_short_name = ICAT_PREFIX_MAP[autoreduction_instrument_name]
            self.assertEqual(
                ICAT_INSTRUMENTS_MOCK_QUERY_RESULTS[instrument_short_name].fullName, autoreduction_instrument_name)


class MockInstrumentQueryResult():
    """
    Mocks result of client.execute_query("SELECT i FROM Instrument i WHERE name = '....'))[0]
    """

    def __init__(self, fullName):
        self.fullName = fullName
