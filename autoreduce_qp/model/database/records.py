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

import io
import json
import socket
import logging
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from typing import List, Tuple, Union
from django.utils import timezone

from autoreduce_utils.settings import SCRIPTS_DIRECTORY
from autoreduce_qp.queue_processor.reduction.service import ReductionScript as ReductionScriptFile
from autoreduce_db.reduction_viewer.models import (DataLocation, ReductionArguments, ReductionScript, RunNumber,
                                                   ReductionRun)

# pylint:disable=no-member

logger = logging.getLogger(__file__)


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


def get_script_and_arguments(instrument: str, script: str, arguments: dict) -> Tuple[str, str]:
    """
    Loads the reduction script (reduce.py) as a string, and if arguments are not provided it loads
    them from reduce_vars.py as a module, which is then converted to a dictionary.

    Args:
        instrument: The name of the instrument for which the scripts will be loaded
        arguments: The reduction arguments that will be used for the reduction.
                   If None, the default arguments will be loaded from reduce_vars.py

    Returns:
        The reduction script as a string, the reduction arguments as a dictionary,
        and any error messages encountered
    """
    if not script:
        rscript = ReductionScriptFile(instrument)
        script = rscript.text()

    if not arguments:
        arguments = {
            "standard_vars": {},
            "advanced_vars": {},
            "variable_help": {
                "standard_vars": {},
                "advanced_vars": {}
            }
        }
        rargs = ReductionScriptFile(instrument, "reduce_vars.py")
        module = rargs.load()
        for dict_name in ["standard_vars", "advanced_vars", "variable_help"]:
            arguments[dict_name] = getattr(module, dict_name, {})

    arguments_str = json.dumps(arguments, separators=(',', ':'))
    return script, arguments_str


def _make_script_and_arguments(instrument, message, batch_run):
    script, arguments_json = get_script_and_arguments(instrument, message.reduction_script, message.reduction_arguments)
    script, _ = ReductionScript.objects.get_or_create(text=script)

    if message.reduction_arguments is None and not batch_run:
        # branch when a new run is submitted - find args from pre-configured new runs for an experiment
        # as experiment variables override any other ones
        try:
            arguments = instrument.arguments.get(experiment_reference__isnull=False,
                                                 experiment_reference=message.rb_number)
        except ReductionArguments.DoesNotExist:
            # no pre-configured new runs for this experiment, so try to find pre-configured ones for this run
            arguments = instrument.arguments.filter(start_run__isnull=False,
                                                    start_run__lte=message.run_number).order_by("start_run").last()
            if not arguments:
                # the arguments don't seem to exist, create a new object with the defaults from reduce_vars
                # get_or_create is used so that if they match with any previous args they are still re-used
                arguments, _ = ReductionArguments.objects.get_or_create(raw=arguments_json, instrument=instrument)
    else:
        # branch for reruns and batch runs
        try:
            arguments = ReductionArguments.objects.get(raw=arguments_json, instrument=instrument)
        except ReductionArguments.DoesNotExist:
            arguments = ReductionArguments.objects.create(raw=arguments_json, start_run=None, instrument=instrument)
    return script, arguments


def create_reduction_run_record(experiment, instrument, message, run_version, status):
    """
    Creates an ORM record for the given reduction run and returns
    this record without saving it to the DB
    """

    time_now = timezone.now()
    batch_run = isinstance(message.run_number, list)

    script, arguments = _make_script_and_arguments(instrument, message, batch_run)
    message.reduction_script = script.text
    message.reduction_arguments = arguments.as_dict()

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
                                                started_by=message.started_by,
                                                reduction_host=socket.getfqdn(),
                                                batch_run=batch_run,
                                                script=script,
                                                arguments=arguments)
    _make_run_numbers(reduction_run, message.run_number)
    _make_data_locations(reduction_run, message.data)

    return reduction_run, message
