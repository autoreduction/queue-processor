# ############################################################################
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################
"""
Contains various helper methods for managing or creating ORM records
"""

import socket
from django.utils import timezone
from typing import List, Union

from autoreduce_db.instrument.models import ReductionRun
from autoreduce_db.reduction_viewer.models import DataLocation, RunNumber


def _make_data_locations(reduction_run, message_data_loc: Union[str, List[str]]):
    """
    Create a new data location entry which has a foreign key linking it to the current
    reduction run. The file path itself will point to a datafile
    (e.g. "/isis/inst$/NDXWISH/Instrument/data/cycle_17_1/WISH00038774.nxs")
    """
    if isinstance(message_data_loc, str):
        DataLocation.objects.create(file_path=message_data_loc, reduction_run=reduction_run)
    else:
        DataLocation.objects.bulk_create(
            [DataLocation(file_path=data_loc, reduction_run=reduction_run) for data_loc in message_data_loc])


def _make_run_numbers(reduction_run, message_run_number: Union[int, List[int]]):
    """
    Creates the related RunNumber objects
    """
    if isinstance(message_run_number, int):
        RunNumber.objects.create(reduction_run=reduction_run, run_number=message_run_number)
    else:
        RunNumber.objects.bulk_create(
            [RunNumber(reduction_run=reduction_run, run_number=run_number) for run_number in message_run_number])


def create_reduction_run_record(experiment, instrument, message, run_version, script_text, status):
    """
    Creates an ORM record for the given reduction run and returns
    this record without saving it to the DB
    """

    time_now = timezone.now()
    reduction_run = ReductionRun.objects.create(run_version=run_version,
                                                run_description=message.description,
                                                hidden_in_failviewer=0,
                                                admin_log='',
                                                reduction_log='',
                                                created=time_now,
                                                last_updated=time_now,
                                                experiment=experiment,
                                                instrument=instrument,
                                                status_id=status.id,
                                                script=script_text,
                                                started_by=message.started_by,
                                                reduction_host=socket.getfqdn(),
                                                batch_run=isinstance(message.run_number, list))
    _make_run_numbers(reduction_run, message.run_number)
    _make_data_locations(reduction_run, message.data)

    return reduction_run
