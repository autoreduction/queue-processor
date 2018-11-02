"""
Threading class to check the health of the End of Run Monitor service
"""
from datetime import datetime
import logging
import time
import threading

from monitors import end_of_run_monitor
from monitors import icat_monitor
from monitors.settings import INSTRUMENTS
from utils.clients.database_client import DatabaseClient
from utils.clients.connection_exception import ConnectionException


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
    def last_run_query(db_cli, inst):
        """
        Wraps the database query used to get the latest run on an instrument
        :param db_cli: Database client
        :param inst: Instrument name
        :return: Row from the reduction database
        """
        conn = db_cli.get_connection()
        return conn.query(db_cli.reduction_run()) \
            .join(db_cli.reduction_run().instrument) \
            .filter(db_cli.reduction_run().run_version == 0) \
            .filter(db_cli.instrument().name == inst) \
            .order_by(db_cli.reduction_run().created.desc()) \
            .first()

    @staticmethod
    def get_db_last_run(db_cli, inst):
        """
        Get the last run from the reduction database
        :param db_cli: Database client
        :param inst: Instrument name
        :return: Last run as an integer
        """
        db_run_result = HealthCheckThread.last_run_query(db_cli, inst)

        if not db_run_result:
            return None
        return db_run_result.run_number

    @staticmethod
    def get_db_client():
        """
        Login to the database
        :return: Database client
        """
        db_cli = DatabaseClient()
        try:
            db_cli.connect()
        except ConnectionException:
            logging.error("Unable to connect to MySQL")
        return db_cli

    @staticmethod
    def health_check():
        """
        Check to see if the service is still running as expected
        :return: True: Service is okay, False: Service requires restart
        """
        logging.info('Performing Health Check at %s', datetime.now())
        db_cli = HealthCheckThread.get_db_client()

        for inst in INSTRUMENTS:
            db_last_run = HealthCheckThread.get_db_last_run(db_cli, inst['name'])
            icat_last_run = icat_monitor.get_last_run(inst['name'])

            if db_last_run and icat_last_run:
                logging.info("Found last run from database on %s of %i",
                             inst['name'], db_last_run)
                logging.info("Found last run from ICAT on %s of %i",
                             inst['name'], int(icat_last_run))

                # Compare them and make sure the database isn't
                # too far behind. There is a tolerance of 2 runs
                if db_last_run < int(icat_last_run) - 2:
                    db_cli.disconnect()
                    return False

        db_cli.disconnect()
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
