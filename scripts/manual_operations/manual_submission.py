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

import json
import sys
import argparse

# The below is only a template on the repo
# pylint: disable=import-error, no-name-in-module
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
    data_dict = active_mq_client.serialise_data(rb_number=rb_number,
                                                instrument=instrument,
                                                location=data_file_location,
                                                run_number=run_number,
                                                started_by=-1)

    active_mq_client.send('/queue/DataReady', json.dumps(data_dict), priority=1)
    print("Submitted run: \r\n" + json.dumps(data_dict, indent=1))

def get_location_and_rb_from_database(database_client, run_number):
    db_connection = database_client.get_connection()
    location_query = f"SELECT file_path " \
                     f"FROM reduction_viewer_reductionlocation " \
                     f"WHERE reduction_run_id = {run_number}"
    location_result = db_connection.execute(location_query).fetchall()
    if len(location_result) == 0:
        return None

    # NOTE: where is RB number stored?
    rb_query = f"SELECT r " \
                     f"FROM reduction_viewer_reductionrun " \
                     f"WHERE reduction_run_id = {run_number}"





def get_location_and_rb_from_icat(icat_client, instrument, run_number, file_ext):
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
    TODO: update this properly
    Attempts to retrieve the datafile from the auto-reduction database.
    If the datafile does not exist within the database, attempts to retrieve it's
    location and investigation from ICAT.
    :param icat_client: client to access ICAT service
    :param instrument: name of instrument
    :param run_number: run number to be processed
    :param file_ext: expected file extension
    :return The resulting data_file
    """

    result = get_location_and_rb_from_database(database_client, run_number)
    if result:
        return result
    print(f"Cannot find datafile for run_number {run_number} in Auto-reduction database."
          f"Will try ICAT...")

    result = get_location_and_rb_from_icat(icat_client, instrument, run_number, file_ext)
    return result

def main():
    """
    File usage description, validation and running mechanism
    :return:
    """
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
    icat_client.connect()

    print("Logging into ActiveMQ")
    activemq_client = QueueClient()
    activemq_client.connect()

    print("Logging into Database")
    database_client = DatabaseClient()
    database_client.connect()

    instrument = args.instrument.upper()

    for run in run_numbers:
        location, rb_num = get_location_and_rb(database_client, icat_client, instrument, run, "nxs")
        submit_run(activemq_client, rb_num, instrument, location, run)


if __name__ == "__main__":
    main()
