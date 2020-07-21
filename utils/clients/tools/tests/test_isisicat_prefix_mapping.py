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
        Test: If a selection of instrument names map to ICAT instrument prefixes using ICAT_PREFIX_MAP
        When: Called when testing correct mappings
        """
        ICAT_INSTRUMENTS_MOCK_SELECTION = [
            ("ENGINX", "ENG"),
            ("GEM", "GEM"),
            ("HRPD", "HRP"),
            ("MAPS", "MAP")
        ]

        for instrument in ICAT_INSTRUMENTS_MOCK_SELECTION:
            self.assertEqual(ICAT_PREFIX_MAP[instrument[0]], instrument[1])
