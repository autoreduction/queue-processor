# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
View functions for displaying Variable data
This imports into another view, thus no middleware
"""
import logging

from autoreduce_webapp.view_utils import (check_permissions, login_and_uows_valid, render_with)
from django.shortcuts import redirect, render
from reduction_viewer.models import Instrument, ReductionRun
from reduction_viewer.utils import ReductionRunUtils
from instrument.models import InstrumentVariable
from queue_processors.queue_processor.variable_utils import VariableUtils

LOGGER = logging.getLogger("app")


# pylint:disable=too-many-locals
def summarize_variables(request, instrument, last_run_object):
    """
    Handles view request for the instrument summary page
    """
    # pylint:disable=no-member
    instrument = Instrument.objects.get(name=instrument)

    # pylint:disable=invalid-name
    current_variables = [runvar.variable.instrumentvariable for runvar in last_run_object.run_variables.all()]

    upcoming_variables_by_run = InstrumentVariable.objects.filter(start_run__gt=last_run_object.run_number)
    upcoming_variables_by_experiment = InstrumentVariable.objects.filter(
        experiment_reference__gte=last_run_object.experiment.reference_number)

    # TODO the tracks_script that is being set is often innacurate
    # vars made from the web app DO NOT track the script
    # the view itself is innacurate as "tracks script" is set on a per-variable basis
    # rather than the whole configuration
    # Create a nested dictionary for by-run
    upcoming_variables_by_run_dict = {}
    for variable in upcoming_variables_by_run:
        if variable.start_run not in upcoming_variables_by_run_dict:
            upcoming_variables_by_run_dict[variable.start_run] = {
                'run_start': variable.start_run,
                'run_end': 0,  # We'll fill this in after
                'tracks_script': variable.tracks_script,
                'variables': [],
                'instrument': instrument,
            }
        upcoming_variables_by_run_dict[variable.start_run]['variables'].append(variable)

    # Fill in the run end numbers
    run_end = 0
    for run_number in sorted(upcoming_variables_by_run_dict.keys(), reverse=True):
        upcoming_variables_by_run_dict[run_number]['run_end'] = run_end
        run_end = max(run_number - 1, 0)

    current_start = current_variables[0].start_run
    # pylint:disable=deprecated-lambda
    next_run_starts = list(filter(lambda start: start > current_start, sorted(upcoming_variables_by_run_dict.keys())))
    current_end = next_run_starts[0] - 1 if next_run_starts else 0

    current_vars = {
        'run_start': current_start,
        'run_end': current_end,
        'tracks_script': not any((var.tracks_script for var in current_variables)),
        'variables': current_variables,
        'instrument': instrument,
    }

    # Move the upcoming vars into an ordered list
    upcoming_variables_by_run_ordered = []
    for key in sorted(upcoming_variables_by_run_dict):
        upcoming_variables_by_run_ordered.append(upcoming_variables_by_run_dict[key])

    # Create a nested dictionary for by-experiment
    upcoming_variables_by_experiment_dict = {}
    for variables in upcoming_variables_by_experiment:
        if variables.experiment_reference not in upcoming_variables_by_experiment_dict:
            upcoming_variables_by_experiment_dict[variables.experiment_reference] = {
                'experiment': variables.experiment_reference,
                'variables': [],
                'instrument': instrument,
            }
        upcoming_variables_by_experiment_dict[variables.experiment_reference]['variables'].\
            append(variables)

    # Move the upcoming vars into an ordered list
    upcoming_variables_by_experiment_ordered = []
    for key in sorted(upcoming_variables_by_experiment_dict):
        upcoming_variables_by_experiment_ordered.append(upcoming_variables_by_experiment_dict[key])
    sorted(upcoming_variables_by_experiment_ordered, key=lambda r: r['experiment'])

    context_dictionary = {
        'instrument': instrument,
        'current_variables': current_vars,
        'upcoming_variables_by_run': upcoming_variables_by_run_ordered,
        'upcoming_variables_by_experiment': upcoming_variables_by_experiment_ordered,
    }

    return render(request, 'snippets/instrument_summary_variables.html', context_dictionary)


# pylint:disable=unused-argument
@login_and_uows_valid
@check_permissions
def delete_instrument_variables(request, instrument=None, start=0, end=0, experiment_reference=None):
    """
    Handles request for deleting instrument variables
    """

    # We "save" an empty list to delete the previous variables.
    if experiment_reference is not None:
        InstrumentVariable.objects.filter(instrument__name=instrument,
                                          experiment_reference=experiment_reference).delete()
    else:
        start_run_kwargs = {"start_run__gte": start}
        if end > 0:
            start_run_kwargs["start_run__lte"] = end
        InstrumentVariable.objects.filter(instrument__name=instrument, **start_run_kwargs).delete()

    return redirect('instrument:variables_summary', instrument=instrument)


@login_and_uows_valid
@check_permissions
@render_with('variables_summary.html')
# pylint:disable=no-member
def instrument_variables_summary(request, instrument):
    """
    Handles request to view instrument variables
    """
    instrument = Instrument.objects.get(name=instrument)
    context_dictionary = {'instrument': instrument, 'last_instrument_run': instrument.reduction_runs.last()}
    return context_dictionary


@login_and_uows_valid
@check_permissions
@render_with('snippets/edit_variables.html')
def current_default_variables(request, instrument=None):
    """
    Handles request to view default variables
    """

    current_variables = VariableUtils.get_default_variables(instrument)
    standard_vars = current_variables["standard_vars"]
    advanced_vars = current_variables["advanced_vars"]

    context_dictionary = {
        'instrument': instrument,
        'standard_variables': standard_vars,
        'advanced_variables': advanced_vars,
    }
    return context_dictionary


def render_run_variables(request, instrument_name, run_number, run_version=0):
    """
    Handles request to view the summary of a run
    """
    # pylint:disable=no-member
    reduction_run = ReductionRun.objects.get(instrument__name=instrument_name,
                                             run_number=run_number,
                                             run_version=run_version)

    vars_kwargs = ReductionRunUtils.make_kwargs_from_runvariables(reduction_run)
    standard_vars = vars_kwargs["standard_vars"]
    advanced_vars = vars_kwargs["advanced_vars"]

    current_variables = VariableUtils.get_default_variables(instrument_name)
    current_standard_variables = current_variables["standard_vars"]
    current_advanced_variables = current_variables["advanced_vars"]

    context_dictionary = {
        'run_number': run_number,
        'run_version': run_version,
        'standard_variables': standard_vars,
        'advanced_variables': advanced_vars,
        'current_standard_variables': current_standard_variables,
        'current_advanced_variables': current_advanced_variables,
        'instrument': reduction_run.instrument,
    }
    return render(request, 'snippets/run_variables.html', context_dictionary)
