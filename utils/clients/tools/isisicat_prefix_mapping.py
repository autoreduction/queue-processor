# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
ICAT_PREFIX_MAP is exposed to map Autoreduction to ICAT instrument prefixes
"""

from utils.clients.icat_client import ICATClient
from utils.settings import VALID_INSTRUMENTS as AUTOREDUCTION_INSTRUMENT_NAMES


def fetch_instrument_fullname_mappings():
    """
    Queries ICAT for shorter names of all autoreduction instruments
    """
    client = ICATClient()
    instrument_fullname_to_short_name_map = {}

    for instrument_fullname in AUTOREDUCTION_INSTRUMENT_NAMES:
        try:
            icat_instrument = client.execute_query(
                "SELECT i FROM Instrument i WHERE i.fullName = '{}'".format(instrument_fullname))[0]
        except:
            print("Warning: No instrument in ICAT with fullName", instrument_fullname)
            continue

        instrument_fullname_to_short_name_map[instrument_fullname] = icat_instrument.name

    return instrument_fullname_to_short_name_map


ICAT_PREFIX_MAP = fetch_instrument_fullname_mappings()
