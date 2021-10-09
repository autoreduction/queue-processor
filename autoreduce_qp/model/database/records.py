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
from typing import List, Optional, Tuple, Union
from django.utils import timezone

from autoreduce_utils.settings import SCRIPTS_DIRECTORY
from autoreduce_db.reduction_viewer.models import DataLocation, ReductionArguments, ReductionScript, RunNumber, ReductionRun

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


def get_script_and_arguments(instrument: str, arguments: dict) -> Tuple[str, str]:
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
    scripts_dir = Path(SCRIPTS_DIRECTORY % instrument)
    try:
        reduce_path = scripts_dir / "reduce.py"
        with io.open(reduce_path, 'r') as open_file:
            script = open_file.read()
    except IOError:
        script = ""

    if not arguments:
        arguments = {
            "standard_vars": {},
            "advanced_vars": {},
            "variable_help": {
                "standard_vars": {},
                "advanced_vars": {}
            }
        }
        vars_path = scripts_dir / "reduce_vars.py"
        try:
            spec = spec_from_file_location("reduce_vars.py", vars_path)
            if spec is None:
                raise ImportError(f"Module at {vars_path} does not exist.")
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
            for dict_name in ["standard_vars", "advanced_vars", "variable_help"]:
                arguments[dict_name] = getattr(module, dict_name, {})

        except ImportError as exc:
            logger.error("Unable to load reduction script %s due to missing import. (%s)", vars_path, exc)
            raise
        except SyntaxError as exc:
            logger.error("Syntax error in reduction script %s", vars_path)
            raise

        arguments = json.dumps(arguments, separators=(',', ':'))
    return script, arguments


def create_reduction_run_record(experiment, instrument, message, run_version, status):
    """
    Creates an ORM record for the given reduction run and returns
    this record without saving it to the DB
    """

    time_now = timezone.now()
    # TODO: fail nicely when reduce_vars.py is missing or has an error
    script, arguments_json = get_script_and_arguments(instrument, message.reduction_arguments)
    script, _ = ReductionScript.objects.get_or_create(text=script)
    message.reduction_script = script.text

    batch_run = isinstance(message.run_number, list)

    if message.reduction_arguments is None and not batch_run:
        # branch when a new run is submitted - find args from pre-configured new runs
        arguments = instrument.arguments.filter(start_run__isnull=False, start_run__lte=message.run_number)
        if not arguments:
            arguments = ReductionArguments.objects.create(raw=arguments_json, instrument=instrument)
    else:
        # branch for reruns and batch runs
        try:
            arguments = ReductionArguments.objects.get(raw=arguments_json)
        except ReductionArguments.DoesNotExist:
            arguments = ReductionArguments.objects.create(raw=arguments_json, start_run=None, instrument=instrument)
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
