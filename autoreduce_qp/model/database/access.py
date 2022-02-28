# ############################################################################### #
# Autoreduction Repository : https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""Common functions for accessing and creating records in the database."""
# pylint:disable=no-member
import os
from typing import List, Union
from django.db import transaction

from autoreduce_db.reduction_viewer.models import Software, Status, Experiment, Instrument


@transaction.atomic
def get_instrument(instrument_name: str) -> Instrument:
    """
    Find the instrument record associated with the name provided in the
    database.

    Args:
        instrument_name: The name of the instrument to search for.

    Returns:
        The instrument object from the database.
    """
    instrument, _ = Instrument.objects.get_or_create(name=instrument_name)
    return instrument


def is_instrument_flat_output(instrument_name: str) -> bool:
    """
    Given an instrument name return if it is a flat output instrument.

    Args:
        instrument_name: The name of the instrument.

    Returns:
        True if flat instrument, otherwise False.
    """
    return Instrument.objects.filter(name=instrument_name).first().is_flat_output


def get_all_instrument_names() -> List[str]:
    """Return the names of all instruments in the database."""
    return list(Instrument.objects.values_list("name", flat=True))


@transaction.atomic
def get_status(status_value: str) -> Status:
    """
    Find the status record associated with the value provided in the database.

    Args:
        status_value: The value of the status record e.g. 'Completed'.

    Returns:
        The Status object from the database.

    Raises:
        ValueError: If status_value is not Error, Queued, Processing,
        Completed, or Skipped
    """
    # Verbose values = ["Error", "Queued", "Processing", "Completed", "Stopped"]
    if status_value not in ['e', 'q', 'p', 'c', 's']:
        raise ValueError("Invalid status value passed")

    return Status.objects.get_or_create(value=status_value)[0]


@transaction.atomic
def get_experiment(rb_number: str) -> Experiment:
    """
    Find the Experiment record associated with the rb_number provided in the
    database.

    Args:
        rb_number: The rb_number of the Experiment record e.g. 12345.

    Return:
        The Experiment object from the database.
    """
    return Experiment.objects.get_or_create(reference_number=rb_number)[0]


@transaction.atomic
def get_software(name: str, version: str) -> Software:
    """
    Find the Software record associated with the name and version provided.

    Args:
        name: The name of the software.
        version: The version number of the software.

    Return:
        The Software object from the database
    """
    # If running in test env, create and delete a test software record
    if not "AUTOREDUCTION_PRODUCTION" in os.environ:
        return Software.objects.get_or_create(name=name, version=version)[0]
    else:
        if Software.objects.filter(name=name, version=version).count() == 0:
            raise ValueError(f"Software {name} version {version} is not supported.")
        return Software.objects.get(name=name, version=version)


def find_highest_run_version(experiment: str, run_number: Union[int, List[int]]) -> int:
    """
    Search for the highest run version in the database.

    Args:
        experiment: The experiment number associated with the run.
        run_number: The run number to search for.

    Returns:
        The highest known run version for a given run number.
    """
    last_run = None
    if isinstance(run_number, int):
        last_run = experiment.reduction_runs.filter(run_numbers__run_number=run_number).order_by('-run_version').first()
    else:
        # filter the batch runs that contain any of the run numbers in the list
        runs_containing_run_numbers = experiment.reduction_runs.filter(
            batch_run=True, run_numbers__run_number__in=run_number).order_by('-run_version').distinct()

        # now find one that matches all run numbers inside the list.
        # If any mismatch then this is is considered a new batch run
        for run in runs_containing_run_numbers:
            # converts the RunNumber DB objects to a list of run numbers,
            # then compares with the ones we are looking for
            if [run_number_obj.run_number for run_number_obj in run.run_numbers.all()] == run_number:
                last_run = run
                # the runs are ordered by highest run_number, so we can break out
                # as soon as a matching run_number list is found
                break

    if last_run:  # previous run exists - increment version by 1 for this run
        return last_run.run_version + 1
    else:  # previous run doesn't exist - start at 0
        return 0


def save_record(record):
    """
    Save a record to the database.

    Args:
        record: (DbObject) The record to save.

    Note:
        This is mostly a wrapper to aid unit testing.
    """
    record.save()
