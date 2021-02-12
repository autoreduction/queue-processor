# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import logging

from autoreduce_webapp.view_utils import (check_permissions, login_and_uows_valid, render_with)
from django.db.models.query import QuerySet
from django.shortcuts import redirect
from utilities import input_processing

from reduction_viewer.models import Instrument, ReductionRun
from reduction_viewer.utils import ReductionRunUtils
from instrument.models import InstrumentVariable
from instrument.utils import InstrumentVariablesUtils, STATUS

LOGGER = logging.getLogger("app")


# pylint:disable=inconsistent-return-statements
@login_and_uows_valid
@check_permissions
@render_with('submit_runs.html')
def submit_runs(request, instrument=None):
    """
    Handles run submission request
    """
    LOGGER.info('Submitting runs')
    # pylint:disable=no-member
    instrument = Instrument.objects.prefetch_related('reduction_runs').get(name=instrument)
    if request.method == 'GET':
        processing_status = STATUS.get_processing()
        queued_status = STATUS.get_queued()
        skipped_status = STATUS.get_skipped()

        # pylint:disable=no-member
        runs_for_instrument = instrument.reduction_runs.all()
        last_run = runs_for_instrument.exclude(status=skipped_status).last()

        kwargs = ReductionRunUtils.make_kwargs_from_runvariables(last_run)
        standard_vars = kwargs["standard_vars"]
        advanced_vars = kwargs["advanced_vars"]

        # pylint:disable=no-member
        context_dictionary = {
            'instrument': instrument,
            'last_instrument_run': last_run,
            'processing': runs_for_instrument.filter(status=processing_status),
            'queued': runs_for_instrument.filter(status=queued_status),
            'standard_variables': standard_vars,
            'advanced_variables': advanced_vars,
            'default_standard_variables': standard_vars,
            'default_advanced_variables': advanced_vars,
        }

        return context_dictionary


# pylint:disable=too-many-return-statements,too-many-branches,too-many-statements
@login_and_uows_valid
@check_permissions
@render_with('run_confirmation.html')
def run_confirmation(request, instrument: str):
    """
    Handles request for user to confirm re-run
    """
    range_string = request.POST.get('run_range')
    run_description = request.POST.get('run_description')

    # pylint:disable=no-member
    queue_count = ReductionRun.objects.filter(instrument__name=instrument, status=STATUS.get_queued()).count()
    context_dictionary = {
        # list stores (run_number, run_version)
        'runs': [],
        'variables': None,
        'queued': queue_count,
        'instrument_name': instrument,
        'run_description': run_description
    }

    try:
        run_numbers = input_processing.parse_user_run_numbers(range_string)
    except SyntaxError as exception:
        context_dictionary['error'] = exception.msg
        return context_dictionary

    # Determine user level to set a maximum limit to the number of runs that can be re-queued
    if request.user.is_superuser:
        max_runs = 500
    elif request.user.is_staff:
        max_runs = 50
    else:
        max_runs = 20

    if len(run_numbers) > max_runs:
        context_dictionary["error"] = "{0} runs were requested, but only {1} runs can be " \
                                      "queued at a time".format(len(run_numbers), max_runs)
        return context_dictionary

    related_runs: QuerySet[ReductionRun] = ReductionRun.objects.filter(instrument__name=instrument,
                                                                       run_number__in=run_numbers)
    # Check that RB numbers are the same for the range entered
    # pylint:disable=no-member
    rb_number = related_runs.values_list('experiment__reference_number', flat=True).distinct()
    if len(rb_number) > 1:
        context_dictionary['error'] = 'Runs span multiple experiment numbers ' \
                                      '(' + ','.join(str(i) for i in rb_number) + ')' \
                                      ' please select a different range.'
        return context_dictionary

    script_text = InstrumentVariablesUtils.get_current_script_text(instrument)
    default_variables = InstrumentVariablesUtils.get_default_variables(instrument)
    try:
        new_script_arguments = make_reduction_arguments(request.POST.items(), default_variables)
        context_dictionary['variables'] = new_script_arguments
    except ValueError as err:
        context_dictionary['error'] = err
        return context_dictionary

    for run_number in run_numbers:
        matching_previous_runs = related_runs.filter(run_number=run_number).order_by('-run_version')
        run_suitable, reason = find_reason_to_avoid_re_run(matching_previous_runs, run_number)
        if not run_suitable:
            context_dictionary['error'] = reason
            break

        # run_description gets stored in run_name in the ReductionRun object
        max_run_name_length = ReductionRun._meta.get_field('run_name').max_length
        if len(run_description) > max_run_name_length:
            context_dictionary["error"] = "The description contains {0} characters, " \
                                          "a maximum of {1} are allowed".\
                format(len(run_description), max_run_name_length)
            return context_dictionary

        most_recent_run: ReductionRun = matching_previous_runs.first()
        # User can choose whether to overwrite with the re-run or create new data
        overwrite_previous_data = bool(request.POST.get('overwrite_checkbox') == 'on')
        ReductionRunUtils.send_retry_message(request.user.id, most_recent_run, script_text, new_script_arguments,
                                             overwrite_previous_data)
        # list stores (run_number, run_version)
        context_dictionary["runs"].append((run_number, most_recent_run.run_version + 1))

    return context_dictionary


def find_reason_to_avoid_re_run(matching_previous_runs, run_number):
    """
    Che
    """
    most_recent_run = matching_previous_runs.first()

    # Check old run exists - if it doesn't exist there's nothing to re-run!
    if most_recent_run is None:
        return False, f"Run number {run_number} hasn't been ran by autoreduction yet."

    # Prevent multiple queueings of the same re-run
    queued_runs = matching_previous_runs.filter(status=STATUS.get_queued()).first()
    if queued_runs is not None:
        return False, f"Run number {queued_runs.run_number} is already queued to run"

    return True, ""


def make_reduction_arguments(POST_arguments, default_variables):
    new_script_arguments = {"standard_vars": {}, "advanced_vars": {}}
    for key, value in POST_arguments:
        if 'var-' in key:
            if 'var-advanced-' in key:
                name = key.replace('var-advanced-', '').replace('-', ' ')
                dict_key = "advanced_vars"
            elif 'var-standard-' in key:
                name = key.replace('var-standard-', '').replace('-', ' ')
                dict_key = "standard_vars"
            else:
                continue

            if name is not None:
                if len(value) > InstrumentVariable._meta.get_field('value').max_length:
                    raise ValueError(f'Value given in {name} is too long.')

                # TODO how much do we care about this
                if name not in default_variables[dict_key]:
                    continue  # TODO we just ignore the variable if it has been removed? Can this even happen?

                new_script_arguments[dict_key][name] = value

    if not new_script_arguments:
        raise ValueError('No variables were found to be submitted.')

    return new_script_arguments


# pylint:disable=too-many-statements,too-many-branches
@login_and_uows_valid
@check_permissions
@render_with('configure_new_runs.html')
def configure_new_runs(request, instrument=None, start=0, end=0, experiment_reference=0):
    """
    Handles request to view instrument variables
    """
    instrument_name = instrument
    start, end = int(start), int(end)

    if request.method == 'POST':
        return configure_new_runs_POST(request, instrument_name, start, end, experiment_reference)
    else:
        return configure_new_runs_GET(request, instrument, start, end, experiment_reference)


def configure_new_runs_POST(request, instrument_name, start=0, end=0, experiment_reference=0):
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
    """

    _find_or_make_variables for start with track_script = False
    and _find_or_make_variables for end with track_script = True

    so that once we're past end the variables get updated automatically

    but this makes track_script=True useless in the web app,
    because their values will be overwritten immediatelly?

    or will they? try it

    this is a lot easier for experiment_reference.. just make the variables for it and that's it
    extend _find_or_make_variables to experiment ref number?
    """
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


def configure_new_runs_GET(request, instrument_name, start=0, end=0, experiment_reference=0):
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
        last_run = instrument.reduction_runs.exclude(status=STATUS.get_skipped()).last()
    except AttributeError:
        # TODO this instrument hasn't had a non-skipped run so what do
        last_run = 0
        raise ValueError("Nema takava durjava")

    current_variables = ReductionRunUtils.make_kwargs_from_runvariables(last_run)
    standard_vars = current_variables["standard_vars"]
    advanced_vars = current_variables["advanced_vars"]

    # TODO how to use this?
    # if experiment_reference > 0:
    #     current_variables = instrument.instrumentvariable_set.filter(experiment_reference=experiment_reference)
    # else:
    #     current_variables = last_run.filter(start_run=last_variable_run_number)

    upcoming_variables = instrument.instrumentvariable_set.filter(start_run=last_run.run_number + 1)
    # variables = InstrumentVariablesUtils().\
    # show_variables_for_run(instrument_name, start)

    # if not editing or not variables:
    #     variables = InstrumentVariablesUtils().\
    #         show_variables_for_run(instrument.name)
    #     if not variables:
    #         variables = InstrumentVariablesUtils().get_default_variables(instrument.name)
    #     editing = False

    # TODO pretty sure we do this somewhere else

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
        'last_instrument_run': last_run,
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
