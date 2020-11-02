# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
get_icat_instrument_prefix() can be used to map Autoreduction to ICAT instrument prefixes
"""
from utils.clients.icat_client import ICATClient
from utils.clients.tools.isisicat_prefix_mapping_logging_setup import logger


def get_icat_instrument_prefix(instrument_fullname: str) -> str:
    """
    Queries ICAT for shorter names for all Autoreduction instruments or only selection if passed in
    :param autoreduction_instruments: Optionally input custom list of autoreduction instrument names
    :return: A map of Autoreduction to ICAT instrument prefixes
    """
    client = ICATClient()

    try:
        icat_instruments = client.execute_query("SELECT i FROM Instrument i")
    except Exception as exc:
        warning_message = "ICAT instrument query failed"
        print(warning_message)
        logger.warning(warning_message)
        raise RuntimeError(warning_message) from exc

    icat_instrument = next((x for x in icat_instruments if x.fullName == instrument_fullname), None)

    if not icat_instrument:
        warning_message = f"No instrument in ICAT with fullName {instrument_fullname}"
        print(warning_message)
        logger.warning(warning_message)
        raise RuntimeError(f"Instrument with fullname {instrument_fullname} not found in ICAT.")

    return icat_instrument.name
