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

import fire

from model.database import access as db
from model.message.message import Message
from scripts.manual_operations.util import get_run_range

from utils.clients.connection_exception import ConnectionException
from utils.clients.icat_client import ICATClient
from utils.clients.queue_client import QueueClient
from utils.clients.django_database_client import DatabaseClient
from utils.clients.tools.isisicat_prefix_mapping import get_icat_instrument_prefix


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
                      data=data_file_location,
                      run_number=run_number,
                      facility="ISIS",
                      started_by=-1)
    active_mq_client.send('/queue/DataReady', message, priority=1)
    print("Submitted run: \r\n" + message.serialize(indent=1))


def get_location_and_rb_from_database(database_client, instrument, run_number):
    """
    Retrieves a run's data-file location and rb_number from the auto-reduction database
    :param database_client: Client to access auto-reduction database
    :param instrument: (str) the name of the instrument associated with the run
    :param run_number: The run number of the data to be retrieved
    :return: The data file location and rb_number, or None if this information is not
    in the database
    """
    if database_client is None:
        print("Database not connected")
        return None

    all_reduction_run_records = db.get_reduction_run(instrument, run_number)

    if not all_reduction_run_records:
        return None

    reduction_run_record = all_reduction_run_records.order_by('run_version').first()
    data_location = reduction_run_record.data_location.first().file_path
    experiment_number = reduction_run_record.experiment.reference_number

    return data_location, experiment_number


def icat_datafile_query(icat_client, file_name):
    """
    Search for file name in icat and return it if it exist.
    :param icat_client: Client to access the ICAT service
    :param file_name: file name to search for in icat
    :return: icat datafile entry if found
    :raises SystemExit: If icat_client not connected
    """
    if icat_client is None:
        print("ICAT not connected")  # pragma: no cover
        sys.exit(1)  # pragma: no cover

    return icat_client.execute_query("SELECT df FROM Datafile df WHERE df.name = '" + file_name +
                                     "' INCLUDE df.dataset AS ds, ds.investigation")


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
        print("ICAT not connected")  # pragma: no cover
        sys.exit(1)  # pragma: no cover

    # look for file-name assuming file-name uses prefix instrument name
    icat_instrument_prefix = get_icat_instrument_prefix(instrument)
    file_name = f"{icat_instrument_prefix}{str(run_number).zfill(5)}.{file_ext}"
    datafile = icat_datafile_query(icat_client, file_name)

    if not datafile:
        print("Cannot find datafile '" + file_name + "' in ICAT. Will try with zeros in front of run number.")
        file_name = f"{icat_instrument_prefix}{str(run_number).zfill(8)}.{file_ext}"
        datafile = icat_datafile_query(icat_client, file_name)

    # look for file-name assuming file-name uses full instrument name
    if not datafile:
        print("Cannot find datafile '" + file_name + "' in ICAT. Will try using full instrument name.")
        file_name = f"{instrument}{str(run_number).zfill(5)}.{file_ext}"
        datafile = icat_datafile_query(icat_client, file_name)

    if not datafile:
        print("Cannot find datafile '" + file_name + "' in ICAT. Will try with zeros in front of run number.")
        file_name = f"{instrument}{str(run_number).zfill(8)}.{file_ext}"
        datafile = icat_datafile_query(icat_client, file_name)

    if not datafile:
        print("Cannot find datafile '" + file_name + "' in ICAT. Exiting...")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
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

    result = get_location_and_rb_from_database(database_client, instrument, run_number)
    if result:
        return result
    print(f"Cannot find datafile for run_number {run_number} in Auto-reduction database. " f"Will try ICAT...")

    return get_location_and_rb_from_icat(icat_client, instrument, run_number, file_ext)


def login_icat():
    """
    Log into the ICATClient
    :return: The client connected, or None if failed
    """
    print("Logging into ICAT")
    icat_client = ICATClient()
    try:
        icat_client.connect()
    except ConnectionException:
        print("Couldn't connect to ICAT. Continuing without ICAT connection.")
        icat_client = None
    return icat_client


def login_database():
    """
    Log into the DatabaseClient
    :return: The client connected, or None if failed
    """
    print("Logging into Database")
    database_client = DatabaseClient()
    try:
        database_client.connect()
    except ConnectionException:
        print("Couldn't connect to Database. Continuing without Database connection.")
        database_client = None
    return database_client


def login_queue():
    """
    Log into the QueueClient
    :return: The client connected, or raise exception
    """
    print("Logging into ActiveMQ")
    activemq_client = QueueClient()
    try:
        activemq_client.connect()
    except (ConnectionException, ValueError) as exp:
        raise RuntimeError("Unable to proceed. Unable to log in to ActiveMQ."
                           "This is required to perform a manual submission") from exp
    return activemq_client


def main(instrument, first_run, last_run=None):
    """
    Manually submit an instrument run from reduction.
    All run number between `first_run` and `last_run` are submitted
    :param instrument: (string) The name of the instrument to submit a run for
    :param first_run: (int) The first run to be submitted
    :param last_run: (int) The last run to be submitted
    """
    run_numbers = get_run_range(first_run, last_run=last_run)

    instrument = instrument.upper()
    icat_client = login_icat()
    database_client = login_database()
    if not icat_client and not database_client:
        raise RuntimeError("Unable to proceed. Unable to connect to ICAT or Database. "
                           "At least one connection is required to perform manual submission.")

    activemq_client = login_queue()

    for run in run_numbers:
        location, rb_num = get_location_and_rb(database_client, icat_client, instrument, run, "nxs")
        if location and rb_num is not None:
            submit_run(activemq_client, rb_num, instrument, location, run)
        else:
            print("Unable to find rb number and location for {}{}".format(instrument, run))


if __name__ == "__main__":
    fire.Fire(main)  # pragma: no cover
