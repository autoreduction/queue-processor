"""
Threading class to check the health of the End of Run Monitor service
"""
from datetime import datetime
import os
import logging
import time
import threading
import json

from monitors import end_of_run_monitor
from monitors import icat_monitor
from monitors.settings import INSTRUMENTS
from utils.clients.database_client import DatabaseClient
from utils.clients.queue_client import QueueClient
from utils.clients.connection_exception import ConnectionException
from utils.settings import ACTIVEMQ_SETTINGS
from utils.project.structure import get_project_root


logging.basicConfig(filename=os.path.join(get_project_root(), 'logs', 'health_check.log'),
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s')


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
        try:
            while self.exit is False:
                if self.health_check():
                    logging.info("No Problems detected with service")
                else:
                    logging.warning("Problem detected with service. Restarting service...")
                    self.restart_service()
                time.sleep(self.time_interval)
            logging.info('Main Health check thread loop stopped')
        # pylint:disable=broad-except
        except Exception as exception:
            logging.error("Exception thrown in health check thread: %s", exception.message)

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
    def get_db_last_run(db_client, inst):
        """
        Get the last run from the reduction database
        :param db_client: Database client
        :param inst: Instrument name
        :return: Last run as an integer
        """
        db_run_result = HealthCheckThread.last_run_query(db_client, inst)

        if not db_run_result:
            return None
        return db_run_result.run_number

    @staticmethod
    def get_db_client():
        """
        Login to the database
        :return: Database client
        """
        db_client = DatabaseClient()
        try:
            db_client.connect()
        except ConnectionException:
            logging.error("Unable to connect to Database")
        return db_client

    @staticmethod
    def resubmit_run(icat_client, instrument, run_number):
        """
        Resubmit runs that are missing (have not been submitted by end of run monitor)
        :param icat_client: ICAT client
        :param instrument: Instrument name
        :param run_number: Run number as an integer
        """
        # Connect to the autoreduce queues
        queue_client = QueueClient()
        try:
            queue_client.connect()
        except ConnectionException:
            logging.error("Unable to connect to Queue")
            return False

        # Grab file location and RB number from ICAT
        rb_number, location = icat_monitor.get_file_rb_and_location(icat_client,
                                                                    instrument,
                                                                    run_number)
        if not location:
            logging.error("Unable to find RB number for run: %s%s", instrument, run_number)
            return False

        # Serialise and send to the queue processors
        data = queue_client.serialise_data(rb_number, instrument, location, run_number)
        logging.info("Resubmitting run with data: %s ", str(data))
        queue_client.send(ACTIVEMQ_SETTINGS.data_ready, json.dumps(data))
        queue_client.disconnect()
        return True

    @staticmethod
    def health_check():
        """
        Check to see if the service is still running as expected
        :return: True: Service is okay, False: Service requires restart
        """
        logging.info('Performing Health Check at %s', datetime.now())

        # Login to the reduction database and ICAT
        db_client = HealthCheckThread.get_db_client()
        icat_client = icat_monitor.icat_login()

        for inst in INSTRUMENTS:
            db_last_run = HealthCheckThread.get_db_last_run(db_client, inst['name'])
            icat_last_run = icat_monitor.get_last_run(icat_client, inst['name'])

            if db_last_run and icat_last_run:
                logging.info("%s - Database: %i , ICAT: %i",
                             inst['name'], db_last_run, icat_last_run)

                # Compare them and make sure the database isn't
                # too far behind. There is a tolerance of 2 runs
                if db_last_run < icat_last_run - 2:
                    logging.debug("Attempting to resubmit missing runs")

                    for run_number in range(db_last_run + 1, icat_last_run + 1):
                        HealthCheckThread.resubmit_run(icat_client, inst['name'], run_number)
                    db_client.disconnect()
                    return False

        db_client.disconnect()
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
