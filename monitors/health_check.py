"""
Threading class to check the health of the End of Run Monitor service
"""
from datetime import datetime
import logging
import time
import threading
import csv
import os

from monitors import icat_monitor
from monitors import end_of_run_monitor
from monitors.settings import (EORM_LAST_RUN_FILE, INSTRUMENTS, INST_FOLDER,
                               LAST_RUN_LOC)


# pylint:disable=missing-docstring
class HealthCheckThread(threading.Thread):

    def __init__(self, time_interval):
        threading.Thread.__init__(self)
        self.time_interval = time_interval
        self.exit = False

    def run(self):
        """
        Perform a service health check every time_interval
        """
        # Create initial last runs CSV
        HealthCheckThread.create_last_runs_csv()

        while self.exit is False:
            service_okay = self.health_check()
            if service_okay:
                logging.info("No Problems detected with service")
            else:
                logging.warning("Problem detected with service. Restarting service...")
                self.restart_service()
            time.sleep(self.time_interval)
        logging.info('Main Health check thread loop stopped')

    @staticmethod
    def create_last_runs_csv():
        """
        Populate the last runs CSV with initial data
        """
        for inst in INSTRUMENTS:
            last_run_file = os.path.join((INST_FOLDER % inst['name']), LAST_RUN_LOC)
            try:
                with open(last_run_file, 'r') as last_run_file:
                    line = last_run_file.readline()
                    parts = line.split(' ')
                    write_last_run(EORM_LAST_RUN_FILE, inst['name'], parts[1])
            except IOError:
                logging.error("Couldn't find last_run.txt for instrument: %s", inst['name'])

    @staticmethod
    def health_check():
        """
        Check to see if the service is still running as expected
        :return: True: Service is okay, False: Service requires restart
        """
        logging.info('Performing Health Check at %s', datetime.now())
        # Loop through the instrument list, getting the last run on each
        with open(EORM_LAST_RUN_FILE, 'rb') as last_run_file:
            last_run_reader = csv.reader(last_run_file)
            for row in last_run_reader:
                # Query the ICAT
                icat_last_run = icat_monitor.get_last_run(row[0])
                if icat_last_run:
                    if int(icat_last_run) > int(row[1]):
                        return False
        return True

    @staticmethod
    def restart_service():
        """
        Restart the end of run monitor service
        """
        end_of_run_monitor.stop()
        end_of_run_monitor.main()

    def stop(self):
        """
        Send a signal to stop the main thread loop
        """
        logging.info('Received stop signal for the Health Check thread')
        self.exit = True
