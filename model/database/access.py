# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Common functions for accessing and creating records in the database
"""
from utils.clients.django_database_client import DatabaseClient


def start_database():
    """
    Create and connect a database client
    :return: The connected database client
    """
    database = DatabaseClient()
    database.connect()
    return database


def get_instrument(instrument_name):
    """
    Find the instrument record associated with the name provided in the database
    :param instrument_name: (str) The name of the instrument to search for
    :return: (Instrument) The instrument object from the database
    """
    database = start_database()
    instrument, _ = database.data_model.Instrument.objects.get_or_create(name=instrument_name)
    return instrument


def get_status(status_value):
    """
    Find the status record associated with the value provided in the database
    :param status_value: (str) The value of the status record e.g. 'Completed'
    :return: (Status) The Status object from the database
    :raises: (ValueError): If status_value is not: Error, Queued, Processing, Completed or Skipped
    """
    # verbose values = ["Error", "Queued", "Processing", "Completed", "Stopped"]
    if status_value not in ['e', 'q', 'p', 'c', 's']:
        raise ValueError("Invalid status value passed")

    database = start_database()
    return database.data_model.Status.objects.get_or_create(value=status_value)[0]


def get_experiment(rb_number):
    """
    Find the Experiment record associated with the rb_number provided in the database
    :param rb_number: (str) The rb_number of the Experiment record e.g. 12345
    :return: (Experiment) The Experiment object from the database
    """
    database = start_database()
    return database.data_model.Experiment.objects.get_or_create(reference_number=rb_number)[0]


def get_software(name, version):
    """
    Find the Software record associated with the name and version provided
    :param name: (str) The name of the software
    :param version: (str) The version number of the software
    :param create: (bool) If True, then create the record if it does not exist
    :return: (Software) The Software object from the database
    """
    database = start_database()
    return database.data_model.Software.objects.get_or_create(name=name, version=version)[0]


def get_reduction_run(instrument, run_number):
    """
    Returns a QuerySet of all ReductionRun versions that have the given instrument/run_number
    :param instrument: (str) The name of the instrument to search for
    :param run_number: (str/int) The run number to search for
    :return: (QuerySet[ReductionRun,]) ReductionRun records that match the criteria

    Note: The query set could contain multiple records or None
    """
    database = start_database()
    instrument_record = get_instrument(instrument)
    return database.data_model.ReductionRun.objects.filter(instrument=instrument_record.id, run_number=run_number)


def find_highest_run_version(experiment, run_number) -> int:
    """
    Search for the highest run version in the database
    :param experiment: (str) The experiment number associated
    :param run_number: (int) The run number to search for
    :return: (int) The highest known run version for a given run number
    """
    last_run = experiment.reduction_runs.filter(run_number=run_number).order_by('-run_version').first()
    if last_run:  # previous run exists - increment version by 1 for this run
        return last_run.run_version + 1
    else:  # previous run doesn't exist - start at 0
        return 0


def save_record(record):
    """
    Save a record to the database
    :param record: (DbObject)The record to save

    Note: This is mostly a wrapper to aid unit testing
    """
    record.save()
