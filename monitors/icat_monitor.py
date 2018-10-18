"""
Monitor the ICAT for the latest run. If end of run monitor is out of sync
then restart it.
"""

import datetime

from utils.clients.icat_client import ICATClient

def get_run_number(file_name, instrument_prefix):
    """
    Extract the run number from a RAW or nexus file
    """
    file_name = file_name.replace(instrument_prefix, '')
    run_number = ''.join([s for s in file_name if s.isdigit()])
    return run_number

class ICATMonitor:
    """
    Monitors ICAT to ensure the end of run monitor is
    keeping up with the latest runs.
    """
    def __init__(self):
        self.last_runs = {}
        self.icat_client = ICATClient()

    def get_cycle_dates(self):
        """
        What cycles could the last run have been in?
        """
        date = datetime.datetime.today().strftime("%Y-%m-%d")
        cycles = (self.icat_client.execute_query("SELECT c.startDate FROM FacilityCycle c"
                                                 " WHERE '%s' > c.endDate"
                                                 " ORDER BY c.startDate DESC"
                                                 " LIMIT 0,1" % date)[0],
                  self.icat_client.execute_query("SELECT c.endDate FROM FacilityCycle c"
                                                 " WHERE '%s' < c.startDate"
                                                 " ORDER BY c.endDate ASC"
                                                 " LIMIT 0,1" % date)[0])
        # Convert them to strings
        cycles_str = (cycles[0].strftime('%Y-%m-%d'), cycles[1].strftime('%Y-%m-%d'))
        return cycles_str

    def get_last_runs(self):
        """
        Retrieves the last run from ICAT on an instrument.
        """
        # Grab investigations from the current cycle on the relevant instrument
        # Then sort the data files to find the last one written.
        cycle_dates = self.get_cycle_dates()

        datafile = self.icat_client.execute_query("SELECT df FROM InvestigationInstrument ii"
                                                  " JOIN ii.investigation.datasets AS ds"
                                                  " JOIN ds.datafiles AS df"
                                                  " WHERE ii.instrument.name = 'SANS2D'"
                                                  " AND ii.investigation.startDate BETWEEN '%s' AND '%s'"
                                                  " AND (df.name LIKE '%%.nxs' OR df.name LIKE '%%.RAW')"
                                                  " ORDER BY df.datafileCreateTime DESC"
                                                  " LIMIT 0,1" % cycle_dates)[0]

        # return the latest run number for each instrument
        run_number = get_run_number(datafile.name, 'SANS2D')
        print(run_number)

mon = ICATMonitor()
mon.get_last_runs()
