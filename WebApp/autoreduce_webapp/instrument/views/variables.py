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
from instrument.utils import InstrumentVariablesUtils, STATUS

LOGGER = logging.getLogger("app")


# pylint:disable=too-many-locals
def instrument_summary(request, instrument, last_run_object):
    """
    Handles view request for the instrument summary page
    """
    # pylint:disable=no-member
    instrument = Instrument.objects.get(name=instrument)

    # pylint:disable=invalid-name
    current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = \
        InstrumentVariablesUtils().get_current_and_upcoming_variables(instrument.name,
                                                                      last_run_object)

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
    for run_number in sorted(list(upcoming_variables_by_run_dict.keys()), reverse=True):
        upcoming_variables_by_run_dict[run_number]['run_end'] = run_end
        run_end = max(run_number - 1, 0)

    current_start = current_variables[0].start_run
    # pylint:disable=deprecated-lambda
    next_run_starts = list(filter(lambda start: start > current_start, sorted(upcoming_variables_by_run_dict.keys())))
    current_end = next_run_starts[0] - 1 if next_run_starts else 0

    current_vars = {
        'run_start': current_start,
        'run_end': current_end,
        'tracks_script': current_variables[0].tracks_script,
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
    instrument_name = instrument
    start, end = int(start), int(end)

    # We "save" an empty list to delete the previous variables.
    if experiment_reference is not None:
        InstrumentVariablesUtils().set_variables_for_experiment(instrument_name, [], experiment_reference)
    else:
        InstrumentVariablesUtils().set_variables_for_runs(instrument_name, [], start, end)

    return redirect('runs_list', instrument=instrument_name)


@login_and_uows_valid
@check_permissions
@render_with('variables_summary.html')
# pylint:disable=no-member
def instrument_variables_summary(request, instrument):
    """
    Handles request to view instrument variables
    """
    instrument = Instrument.objects.get(name=instrument)
    runs = (ReductionRun.objects.only('status', 'last_updated', 'run_number',
                                      'run_version').select_related('status').filter(instrument=instrument).order_by(
                                          '-run_number', 'run_version'))

    context_dictionary = {'instrument': instrument, 'last_instrument_run': runs[0]}
    return context_dictionary


# pylint:disable=too-many-statements,too-many-branches
@login_and_uows_valid
@check_permissions
@render_with('instrument_variables.html')
def instrument_variables(request, instrument=None, start=0, end=0, experiment_reference=0):
    """
    Handles request to view instrument variables
    """
    instrument_name = instrument
    start, end = int(start), int(end)

    if request.method == 'POST':
        return instrument_variables_POST(request, instrument_name, start, end, experiment_reference)
    else:
        return instrument_variables_GET(request, instrument, start, end, experiment_reference)


def instrument_variables_POST(request, instrument_name, start=0, end=0, experiment_reference=0):
    # Submission to modify variables.
    # [("var-standard-"+name, value) or ("var-advanced-"+name, value)]
    var_list = [t for t in request.POST.items() if t[0].startswith("var-")]
    # Remove the first two prefixes from the names to give {name: value}
    new_var_dict = {"".join(t[0].split("-")[2:]): t[1] for t in var_list}

    tracks_script = request.POST.get("track_script_checkbox") == "on"

    # Which variables should we modify?
    is_run_range = request.POST.get("variable-range-toggle-value", "True") == "True"
    start = int(request.POST.get("run_start", 1))
    end = int(request.POST.get("run_end", None)) if request.POST.get("run_end", None) else None

    experiment_reference = request.POST.get("experiment_reference_number", 1)

    def modify_vars(old_vars, new_values):
        """
        Update an old variable with values from the new variable
        """
        for item in old_vars:
            if item.name in new_values:
                item.value = new_values[item.name]
            item.tracks_script = tracks_script

    if is_run_range:
        # Get the variables for the first run, modify them, and set them for the given range.
        instr_vars = InstrumentVariablesUtils().show_variables_for_run(instrument_name, start)
        modify_vars(instr_vars, new_var_dict)
        InstrumentVariablesUtils().set_variables_for_runs(instrument_name, instr_vars, start, end)
    else:
        # Get the variables for the experiment, modify them, and set them for the experiment.
        instr_vars = InstrumentVariablesUtils().\
            show_variables_for_experiment(instrument_name,
                                            experiment_reference)
        if not instr_vars:
            instr_vars = InstrumentVariablesUtils().get_default_variables(instrument_name)
        modify_vars(instr_vars, new_var_dict)
        InstrumentVariablesUtils().set_variables_for_experiment(instrument_name, instr_vars, experiment_reference)

    return redirect('runs_list', instrument=instrument_name)


def instrument_variables_GET(request, instrument_name, start=0, end=0, experiment_reference=0):
    instrument = Instrument.objects.get(name__iexact=instrument_name)

    editing = (start > 0 or experiment_reference > 0)

    # TODO merge the lower 3 in one query.....
    try:
        # pylint:disable=no-member
        # TODO why run_version 0
        # TODO merge the two into a single query with Q(status) | Q(status)
        latest_completed_run = instrument.reduction_runs.filter(
            run_version=0, status=STATUS.get_completed()).order_by('-run_number').first().run_number
    except AttributeError:
        latest_completed_run = 0
    try:
        # pylint:disable=no-member
        latest_processing_run = instrument.reduction_runs.filter(
            run_version=0, status=STATUS.get_processing()).order_by('-run_number').first().run_number
    except AttributeError:
        latest_processing_run = 0

    try:
        last_inst_run = instrument.reduction_runs.exclude(status=STATUS.get_skipped()).order_by('-run_number')[0]
    except AttributeError:
        last_inst_run = 0

    last_variable_run_number = instrument.instrumentvariable_set.last().start_run
    if experiment_reference > 0:
        # variables = InstrumentVariablesUtils().\
        #     show_variables_for_experiment(instrument_name, experiment_reference)
        # TODO rename in model
        current_variables = instrument.instrumentvariable_set.filter(experiment_reference=experiment_reference)
    else:
        current_variables = instrument.instrumentvariable_set.filter(start_run=last_variable_run_number)

    upcoming_variables = instrument.instrumentvariable_set.filter(start_run=last_variable_run_number + 1)
    # variables = InstrumentVariablesUtils().\
    # show_variables_for_run(instrument_name, start)

    # if not editing or not variables:
    #     variables = InstrumentVariablesUtils().\
    #         show_variables_for_run(instrument.name)
    #     if not variables:
    #         variables = InstrumentVariablesUtils().get_default_variables(instrument.name)
    #     editing = False

    # TODO pretty sure we do this somewhere else
    vars_as_kwarg = ReductionRunUtils.make_kwargs_from_variables(current_variables)
    standard_vars = vars_as_kwarg["standard_vars"]
    advanced_vars = vars_as_kwarg["advanced_vars"]

    # # pylint:disable=invalid-name
    # _, upcoming_variables_by_run, _ = \
    #     InstrumentVariablesUtils().get_current_and_upcoming_variables(instrument.name)

    # Unique, comma-joined list of all start runs belonging to the upcoming variables.
    upcoming_run_variables = ','.join(list(set([str(var.start_run) for var in upcoming_variables])))

    # default_variables = InstrumentVariablesUtils().get_default_variables(instrument.name)
    # default_standard_variables = {}
    # default_advanced_variables = {}
    # for variable in default_variables:
    #     if variable.is_advanced:
    #         default_advanced_variables[variable.name] = variable
    #     else:
    #         default_standard_variables[variable.name] = variable
    # pylint:disable=no-member

    # pylint:disable=no-member
    context_dictionary = {
        'instrument': instrument,
        'last_instrument_run': last_inst_run,
        'processing': ReductionRun.objects.filter(instrument=instrument, status=STATUS.get_processing()),
        'queued': ReductionRun.objects.filter(instrument=instrument, status=STATUS.get_queued()),
        'standard_variables': standard_vars,
        'advanced_variables': advanced_vars,
        'default_standard_variables': standard_vars,
        'default_advanced_variables': advanced_vars,
        'run_start': start,
        'run_end': end,
        'experiment_reference': experiment_reference,
        'minimum_run_start': max(latest_completed_run, latest_processing_run),
        'upcoming_run_variables': upcoming_run_variables,
        'editing': editing,
        'tracks_script': '',
    }

    return context_dictionary


@login_and_uows_valid
@check_permissions
@render_with('snippets/edit_variables.html')
def current_default_variables(request, instrument=None):
    """
    Handles request to view default variables
    """
    variables = InstrumentVariablesUtils().get_default_variables(instrument)
    standard_vars = {}
    advanced_vars = {}
    for variable in variables:
        if variable.is_advanced:
            advanced_vars[variable.name] = variable
        else:
            standard_vars[variable.name] = variable
    context_dictionary = {
        'instrument': instrument,
        'standard_variables': standard_vars,
        'advanced_variables': advanced_vars,
    }
    return context_dictionary


def run_summary(request, instrument_name, run_number, run_version=0):
    """
    Handles request to view the summary of a run
    """
    # TODO this should be part of the WebApp/autoreduce_webapp/reduction_viewer/views.py::run_summary
    # pylint:disable=no-member
    reduction_run = ReductionRun.objects.get(instrument__name=instrument_name,
                                             run_number=run_number,
                                             run_version=run_version)

    vars_kwargs = ReductionRunUtils.make_kwargs_from_runvariables(reduction_run)
    standard_vars = vars_kwargs["standard_vars"]
    advanced_vars = vars_kwargs["advanced_vars"]

    current_variables = InstrumentVariablesUtils().get_default_variables(instrument_name)
    current_standard_variables = current_variables["standard_vars"]
    current_advanced_variables = current_variables["advanced_vars"]

    context_dictionary = {
        'run_number': run_number,
        'run_version': run_version,
        'standard_variables': standard_vars,
        'advanced_variables': advanced_vars,
        'default_standard_variables': standard_vars,
        'default_advanced_variables': advanced_vars,
        'current_standard_variables': current_standard_variables,
        'current_advanced_variables': current_advanced_variables,
        'instrument': reduction_run.instrument,
    }
    return render(request, 'snippets/run_variables.html', context_dictionary)
