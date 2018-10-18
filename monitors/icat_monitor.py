"""
Monitor ICAT for the latest run on each instrument. If end of run monitor is out of sync
then restart it.
"""

import datetime
import logging

from settings import INSTRUMENTS, ICAT_MON_LOG_FILE
from utils.clients.icat_client import ICATClient


logging.basicConfig(filename=ICAT_MON_LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')


def get_run_number(file_name, instrument_prefix):
    """
    Extract the run number from a RAW or nexus file
    """
    file_name = file_name.replace(instrument_prefix, '')
    run_number = ''.join([s for s in file_name if s.isdigit()])
    return run_number


def get_cycle_dates(icat_client):
    """
    What cycles could the last run have been in?
    """
    date = datetime.datetime.today().strftime("%Y-%m-%d")
    logging.info("Getting nearest cycles to current date (%s)" % date)
    cycles = (icat_client.execute_query("SELECT c.startDate FROM FacilityCycle c"
                                        " WHERE '%s' > c.endDate"
                                        " ORDER BY c.startDate DESC"
                                        " LIMIT 0,1" % date)[0],
              icat_client.execute_query("SELECT c.endDate FROM FacilityCycle c"
                                        " WHERE '%s' < c.startDate"
                                        " ORDER BY c.endDate ASC"
                                        " LIMIT 0,1" % date)[0])
    # Convert them to strings
    cycles_str = (cycles[0].strftime('%Y-%m-%d'), cycles[1].strftime('%Y-%m-%d'))
    logging.info("Found nearest cycle dates: %s and %s" % cycles_str)
    return cycles_str


def get_instrument_run(icat_client, inst_name, cycle_dates):
    """
    Returns the last run on the named instrument in ICAT
    """
    logging.info("Grabbing recent data files for instrument: %s" % inst_name)
    datafiles = icat_client.execute_query("SELECT df FROM InvestigationInstrument ii"
                                          " JOIN ii.investigation.datasets AS ds"
                                          " JOIN ds.datafiles AS df"
                                          " WHERE ii.instrument.fullName = '%s'"
                                          " AND ii.investigation.startDate BETWEEN '%s' AND '%s'"
                                          " AND (df.name LIKE '%%.nxs' OR df.name LIKE '%%.RAW')"
                                          " ORDER BY df.datafileCreateTime DESC"
                                          " LIMIT 0,1"
                                          % (inst_name, cycle_dates[0], cycle_dates[1]))
    run_number = u'0'
    if len(datafiles) == 0:
        logging.error("No files returned for instrument: %s" % inst_name)
    else:
        # Return the run number
        run_number = get_run_number(datafiles[0].name, inst_name)
        logging.info("Found last run for instrument: %s" % run_number)
    return run_number


def get_last_runs():
    """
    Retrieves the last run from ICAT on an instrument.
    """
    logging.info("Connecting to ICAT")
    icat_client = ICATClient()
    last_runs = {}

    # First, constrain the search space by getting recent cycle dates
    cycle_dates = get_cycle_dates(icat_client)

    # Loop through the instruments, finding the latest run number for each
    for instrument in INSTRUMENTS:
        run_number = get_instrument_run(icat_client, instrument['name'], cycle_dates)
        last_runs[instrument['name']] = run_number

    logging.info("Last run dictionary: %s" % last_runs)
    return last_runs


get_last_runs()
