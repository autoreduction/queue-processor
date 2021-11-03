# ############################################################################ #
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################ #
"""Contains various helper methods for managing or creating ORM records."""
# pylint:disable=no-member
import json
import logging
import socket
from typing import List, Tuple, Union

from django.utils import timezone
import requests
from requests.exceptions import ConnectionError

from autoreduce_db.reduction_viewer.models import (DataLocation, Experiment, Instrument, ReductionArguments,
                                                   ReductionScript, RunNumber, ReductionRun, Status)
from autoreduce_qp.queue_processor.reduction.service import ReductionScript as ReductionScriptFile
from autoreduce_qp.queue_processor.variable_utils import VariableUtils

logger = logging.getLogger(__file__)


def _make_data_locations(reduction_run, message_data_loc: Union[str, List[str]]):
    """
    Create a new data location entry which has a foreign key linking it to the
    current reduction run. The file path itself will point to a datafile e.g.
    "/isis/inst$/NDXWISH/Instrument/data/cycle_17_1/WISH00038774.nxs"
    """
    if isinstance(message_data_loc, str):
        DataLocation.objects.create(file_path=message_data_loc, reduction_run=reduction_run)
    else:
        DataLocation.objects.bulk_create(
            [DataLocation(file_path=data_loc, reduction_run=reduction_run) for data_loc in message_data_loc])


def _make_run_numbers(reduction_run, message_run_number: Union[int, List[int]]):
    """Create the related RunNumber objects."""
    if isinstance(message_run_number, int):
        RunNumber.objects.create(reduction_run=reduction_run, run_number=message_run_number)
    else:
        RunNumber.objects.bulk_create(
            [RunNumber(reduction_run=reduction_run, run_number=run_number) for run_number in message_run_number])


def get_script_and_arguments(instrument: Instrument, script: str, arguments: dict) -> Tuple[str, str]:
    """
    Load the reduction script, reduce.py, as a string. If arguments are not
    provided load them from reduce_vars.py as a module which is then converted
    to a dictionary.

    Args:
        instrument: Instrument name for which the scripts will be loaded.
        script: Contents of the reduction script to be used.
        arguments: Reduction arguments that will be used for the reduction. If
        None, the default arguments will be loaded from reduce_vars.py.

    Returns:
        The reduction script as a string, the reduction arguments as a
        dictionary, and any error messages encountered.
    """
    if not script:
        rscript = ReductionScriptFile(instrument)
        script = rscript.text()

    if not arguments:
        arguments = VariableUtils.get_default_variables(instrument)

    error_msgs = fetch_from_remote_source(arguments)
    arguments_str = json.dumps(arguments, separators=(',', ':'))
    return script, arguments_str, error_msgs


def fetch_from_remote_source(arguments: dict) -> str:
    """
    Search through a supplied dictionary and fetch the values for any variables
    that match the remote syntax expected in reduce_vars.py.

    Args:
        arguments: Reduction arguments that will be used for the reduction.

    Returns:
        A string of comma separated error messages, if any, otherwise None.

    Examples of variable values:
        category: 'standard_vars', 'advanced_vars'
        headings: 'monovan_mapfile', 'hard_mask_file'
        heading_value: {'url': <GitHub path>, 'default': 'mari_res2013.map'}
    """
    error_msgs = []

    for category, headings in arguments.items():
        for heading, heading_value in headings.items():
            if isinstance(heading_value, dict):
                if all(key in heading_value for key in ("url" and "default")):
                    url = heading_value["url"] + heading_value["default"]

                    try:
                        req = requests.get(url)
                        status = req.status_code
                        if status == requests.codes.ok:
                            arguments[category][heading]["value"] = req.text
                        else:
                            error_msgs.append(f"{status} error at {url} for {heading} under {category}")

                    except ConnectionError:
                        error_msgs.append(f"Could not connect to remote source at {url} for {heading} under {category}")

    return ", ".join(error_msgs) if error_msgs else None


def _make_script_and_arguments(experiment: Experiment, instrument: Instrument, message, batch_run: bool):
    script, arguments_json, error_msgs = get_script_and_arguments(instrument, message.reduction_script,
                                                                  message.reduction_arguments)
    script, _ = ReductionScript.objects.get_or_create(text=script)

    if message.reduction_arguments is None and not batch_run:
        # Branch when a new run is submitted - find args from pre-configured new
        # runs for an experiment as experiment variables override any other ones

        # Note: this does NOT and should NOT update the value of
        # experiemnt_reference or start_run arguments as this is done in the
        # autoreduce_frontend configure_new_runs view
        try:
            arguments = instrument.arguments.get(experiment_reference__isnull=False,
                                                 experiment_reference=experiment.reference_number)
        except ReductionArguments.DoesNotExist:
            # No pre-configured new runs for this experiment, so try to find
            # pre-configured ones for this run
            arguments = instrument.arguments.filter(start_run__isnull=False,
                                                    start_run__lte=message.run_number).order_by("start_run").last()
            if not arguments:
                # The arguments don't seem to exist, create a new object with
                # the defaults from reduce_vars get_or_create is used so that if
                # they match with any previous args they are still re-used
                arguments, _ = instrument.arguments.get_or_create(raw=arguments_json)
    else:
        # Branch for reruns and batch runs
        arguments, _ = instrument.arguments.get_or_create(raw=arguments_json)

    return script, arguments, error_msgs


def create_reduction_run_record(experiment: Experiment, instrument: Instrument, message, run_version: int,
                                status: Status):
    """
    Create an ORM record for the given reduction run and return this record
    without saving it to the DB.
    """
    time_now = timezone.now()
    batch_run = isinstance(message.run_number, list)
    script, arguments, error_msgs = _make_script_and_arguments(experiment, instrument, message, batch_run)
    reduction_run = ReductionRun.objects.create(run_version=run_version,
                                                run_title=message.run_title,
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

    # Changes the message values as they are used going forwards in the
    # ReductionRunner
    message.reduction_script = script.text
    message.reduction_arguments = arguments.as_dict()

    # Amends the run_version in the message, as the reduction_run object is not
    # passed into the reduction execution and there is no other source of a
    # run_version. The run_version is used to create the output folder name, if
    # flat_output is False
    message.run_version = run_version
    message.flat_output = instrument.is_flat_output

    message.message = error_msgs
    return reduction_run, message
