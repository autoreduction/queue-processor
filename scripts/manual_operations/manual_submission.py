# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
A module for creating and submitting manual submissions to autoreduction
"""
from __future__ import print_function

import sys
import argparse

# The below is only a template on the repo
# pylint: disable=import-error, no-name-in-module
from icat import ICATSessionError

from message.job import Message
from utils.clients.connection_exception import ConnectionException
from utils.clients.icat_client import ICATClient
from utils.clients.queue_client import QueueClient
from utils.clients.database_client import DatabaseClient


def submit_run(active_mq_client, rb_number, instrument, data_file_location, run_number):
    """
    Submit a new run for autoreduction
    :param active_mq_client: The client for access to ActiveMQ
    :param rb_number: desired experiment rb number
    :param instrument: name of the instrument
    :param data_file_location: location of the data file
    :param run_number: run number fo the experiment
    """
    if active_mq_client is None:
        print("ActiveMQ not connected, cannot submit runs")
        return

    message = Message(rb_number=rb_number,
                      instrument=instrument,
                      file_path=data_file_location,
                      run_number=run_number,
                      started_by=-1)
    active_mq_client.send('/queue/DataReady', message, priority=1)
    print("Submitted run: \r\n" + message.serialize(indent=1))


def get_location_and_rb_from_database(database_client, run_number):
    """
    Retrieves a run's data-file location and rb_number from the auto-reduction database
    :param database_client: Client to access auto-reduction database
    :param run_number: The run number of the data to be retrieved
    :return: The data file location and rb_number, or None if this information is not
    in the database
    """
    if database_client is None:
        print("Database not connected")
        return None

    db_connection = database_client.connect()
    location_query = f"""
                    SELECT file_path
                    FROM reduction_viewer_datalocation
                    WHERE reduction_run_id = {run_number}
                    """
    location_result = db_connection.execute(location_query).fetchall()
    if len(location_result) == 0:
        return None

    rb_query = f"""
                SELECT reduction_viewer_experiment.reference_number
                FROM reduction_viewer_reductionrun
                    JOIN reduction_viewer_experiment
                    ON reduction_viewer_reductionrun.experiment_id = reduction_viewer_experiment.id
                WHERE reduction_viewer_reductionrun.id = {run_number}
                """

    rb_result = db_connection.execute(rb_query).fetchall()
    if len(rb_result) == 0:
        return None

    return location_result[0].file_path, rb_result[0].reference_number


def get_location_and_rb_from_icat(icat_client, instrument, run_number, file_ext):
    """
    Retrieves a run's data-file location and rb_number from ICAT.
    Attempts first with the default file name, then with prepended zeroes.
    :param icat_client: Client to access the ICAT service
    :param instrument: The name of instrument
    :param run_number: The run number to be processed
    :param file_ext: The expected file extension
    :return: The data file location and rb_number
    :raises SystemExit: If the given run information cannot return a location and rb_number
    """
    if icat_client is None:
        print("ICAT not connected")
        sys.exit(1)

    file_name = instrument + str(run_number).zfill(5) + "." + file_ext
    datafile = icat_client.execute_query("SELECT df FROM Datafile df WHERE df.name = '"
                                         + file_name +
                                         "' INCLUDE df.dataset AS ds, ds.investigation")

    if not datafile:
        print("Cannot find datafile '" + file_name +
              "' in ICAT. Will try with zeros in front of run number.")
        file_name = instrument + str(run_number).zfill(8) + "." + file_ext
        datafile = icat_client.execute_query("SELECT df FROM Datafile df WHERE df.name = '"
                                             + file_name +
                                             "' INCLUDE df.dataset AS ds, ds.investigation")

    if not datafile:
        print("Cannot find datafile '" + file_name + "' in ICAT. Exiting...")
        sys.exit(1)
    return datafile[0].location, datafile[0].dataset.investigation.name


def get_location_and_rb(database_client, icat_client, instrument, run_number, file_ext):
    """
    Retrieves a run's data-file location and rb_number from the auto-reduction database,
    or ICAT (if it is not in the database)
    :param database_client: Client to access auto-reduction database
    :param icat_client: Client to access the ICAT service
    :param instrument: The name of instrument
    :param run_number: The run number to be processed
    :param file_ext: The expected file extension
    :return: The data file location and rb_number
    :raises SystemExit: If the given run information cannot return a location and rb_number
    """
    try:
        run_number = int(run_number)
    except ValueError:
        print(f"Cannot cast run_number as an integer. Run number given: '{run_number}'. Exiting...")
        sys.exit(1)

    result = get_location_and_rb_from_database(database_client, run_number)
    if result:
        return result
    print(f"Cannot find datafile for run_number {run_number} in Auto-reduction database. "
          f"Will try ICAT...")

    return get_location_and_rb_from_icat(icat_client, instrument, run_number, file_ext)


def main():
    """ File usage description, validation and running mechanism """
    parser = argparse.ArgumentParser(description='Submit a run to the autoreduction service.',
                                     epilog='./manual_submission.py GEM 83880 [-e 83882]')
    parser.add_argument('instrument', metavar='instrument', type=str,
                        help='a string of the instrument name e.g "GEM"')
    parser.add_argument('-e', metavar='end_run_number', nargs='?', type=int,
                        help='if submitting a range, the end run number e.g. "83882"')
    parser.add_argument('start_run_number', metavar='start_run_number', type=int,
                        help='the start run number e.g. "83880"')
    args = parser.parse_args()

    run_numbers = [args.start_run_number]

    if args.e:
        # Range submission
        if not args.e > args.start_run_number:
            print("'end_run_number' must be greater than 'start_run_number'.")
            print("e.g './manual_submission.py GEM 83880 -e 83882'")
            sys.exit(1)
        run_numbers = range(args.start_run_number, args.e + 1)

    print("Logging into ICAT")
    icat_client = ICATClient()
    try:
        icat_client.connect()
    except ICATSessionError:
        print("Couldn't connect to ICAT. Continuing without ICAT connection.")
        icat_client = None

    print("Logging into Database")
    database_client = DatabaseClient()
    try:
        database_client.connect()
    except ConnectionException:
        print("Couldn't connect to Database. Continuing without Database connection.")
        database_client = None

    print("Logging into ActiveMQ")
    activemq_client = QueueClient()
    try:
        activemq_client.connect()
    except (ConnectionException, ValueError):
        print("Couldn't connect to ActiveMQ. Continuing without ActiveMQ connection.")
        activemq_client = None

    instrument = args.instrument.upper()

    for run in run_numbers:
        location, rb_num = get_location_and_rb(database_client, icat_client, instrument, run, "nxs")
        submit_run(activemq_client, rb_num, instrument, location, run)


if __name__ == "__main__":
    main()
