# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
fetch_instrument_fullname_mappings() can be used to map Autoreduction to ICAT instrument prefixes
"""
from utils.clients.icat_client import ICATClient
from utils.settings import VALID_INSTRUMENTS as AUTOREDUCTION_INSTRUMENT_NAMES
from utils.clients.tools.isisicat_prefix_mapping_logging_setup import logger


def fetch_instrument_fullname_mappings():
    """
    Queries ICAT for shorter names for all Autoreduction instruments
    :return: A map of full instrument names to shortened instrument names
    """
    client = ICATClient()
    instrument_fullname_to_short_name_map = {}
    my_list = AUTOREDUCTION_INSTRUMENT_NAMES
    for instrument_fullname in AUTOREDUCTION_INSTRUMENT_NAMES:
        try:
            icat_instrument = client.execute_query(
                f"SELECT i FROM Instrument i WHERE i.fullName = '{instrument_fullname}'")[0]
        except Exception:
            print("Warning: No instrument in ICAT with fullName", instrument_fullname)
            logger.warning("No instrument in ICAT with fullName %s", instrument_fullname)
            # Missing an instrument should also be picked up in the tests
            continue

        instrument_fullname_to_short_name_map[instrument_fullname] = icat_instrument.name

    return instrument_fullname_to_short_name_map
