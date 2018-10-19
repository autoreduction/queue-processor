"""
Monitor ICAT for the latest run on an instrument. If end of run monitor is out of sync
then restart it.
"""

import datetime
import logging

from monitors.settings import INSTRUMENTS, ICAT_MON_LOG_FILE
from utils.clients.icat_client import ICATClient


logging.basicConfig(filename=ICAT_MON_LOG_FILE,
                    level=logging.INFO,
                    format='%(asctime)s %(message)s')


def get_run_number(file_name, instrument_prefix):
    """
    Extract the run number from a RAW or Nexus file
    """
    file_name = file_name.replace(instrument_prefix, '')
    run_number = ''.join([s for s in file_name if s.isdigit()])
    return run_number


def get_cycle_dates(icat_client):
    """
    What cycles could the last run have been in?
    If the search space isn't constrained in some way then it takes far too long
    to sort the list of data files. Narrowing down the dates is part of this.
    """
    date = datetime.datetime.today().strftime("%Y-%m-%d")
    logging.info("Getting nearest cycles to current date (%s)", date)
    last_cycle = icat_client.execute_query("SELECT c.startDate FROM FacilityCycle c"
                                           " WHERE '%s' > c.endDate"
                                           " ORDER BY c.startDate DESC"
                                           " LIMIT 0,1" % date)
    next_cycle = icat_client.execute_query("SELECT c.endDate FROM FacilityCycle c"
                                           " WHERE '%s' < c.startDate"
                                           " ORDER BY c.endDate ASC"
                                           " LIMIT 0,1" % date)
    if not last_cycle or not next_cycle:
        logging.error("No cycles returned for date")
        return None

    # Return the cycle date range as a pair of strings
    cycles_str = (last_cycle[0].strftime('%Y-%m-%d'), next_cycle[0].strftime('%Y-%m-%d'))
    logging.info("Found nearest cycle dates: %s and %s", cycles_str[0], cycles_str[1])
    return cycles_str


def get_last_run_in_dates(icat_client, instrument, cycle_dates):
    """
    Returns the last run on the named instrument in ICAT.
    Gets the list of investigations on the provided instrument within the
    previously established cycle dates. The query then descends the investigation
    tree until it reaches the files.
    """
    inst_name = instrument['name']
    inst_prefix = instrument['file_prefix']

    logging.info("Grabbing recent data files for instrument: %s", inst_name)
    datafiles = icat_client.execute_query("SELECT df FROM InvestigationInstrument ii"
                                          " JOIN ii.investigation.datasets AS ds"
                                          " JOIN ds.datafiles AS df"
                                          " WHERE ii.instrument.fullName = '%s'"
                                          " AND ii.investigation.startDate BETWEEN '%s' AND '%s'"
                                          " AND (df.name LIKE '%%.nxs' OR df.name LIKE '%%.RAW')"
                                          " ORDER BY df.datafileCreateTime DESC"
                                          " LIMIT 0,1"
                                          % (inst_name, cycle_dates[0], cycle_dates[1]))

    if not datafiles:
        logging.error("No files returned for instrument: %s", inst_name)
        return None

    # Return the run number
    run_number = get_run_number(datafiles[0].name, inst_prefix)
    logging.info("Found last run for instrument: %s", run_number)
    return run_number


def get_last_run(instrument):
    """
    Retrieves the last run from ICAT for an instrument
    """
    logging.info("Connecting to ICAT")
    icat_client = ICATClient()

    # First, constrain the search space by getting recent cycle dates
    cycle_dates = get_cycle_dates(icat_client)
    if not cycle_dates:
        return None

    # Find the last run number for the instrument
    last_run = get_last_run_in_dates(icat_client, instrument, cycle_dates)
    return last_run


for inst in INSTRUMENTS:
    print inst['name']
    print get_last_run(inst)
