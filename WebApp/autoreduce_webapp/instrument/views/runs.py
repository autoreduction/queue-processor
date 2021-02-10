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
    if request.method != 'POST':
        return redirect('runs_list', instrument=instrument.name)

    range_string = request.POST.get('run_range')

    # pylint:disable=no-member
    queue_count = ReductionRun.objects.filter(instrument__name=instrument, status=STATUS.get_queued()).count()
    context_dictionary = {
        'runs': [],
        'variables': None,
        'queued': queue_count,
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

    use_current_script = request.POST.get('use_current_script', u"true").lower() == u"true"
    if use_current_script:
        script_text = InstrumentVariablesUtils.get_current_script_text(instrument)
        default_variables = InstrumentVariablesUtils.get_default_variables(instrument)
    else:
        raise NotImplementedError("TODO this branch")
        script_text = most_recent_run.script
        default_variables = most_recent_run.run_variables.all()

    for run_number in run_numbers:
        matching_previous_runs_queryset = related_runs.filter(run_number=run_number).order_by('-run_version')
        run_suitable, reason = find_reason_to_avoid_re_run(matching_previous_runs_queryset)
        if not run_suitable:
            context_dictionary['error'] = reason
            break

        try:
            new_script_arguments = make_reduction_arguments(request.POST.items(), default_variables)
        except ValueError as err:
            context_dictionary['error'] = err
            break

        # run_description gets stored in run_name in the ReductionRun object
        run_description = request.POST.get('run_description')
        max_run_name_length = ReductionRun._meta.get_field('run_name').max_length
        if len(run_description) > max_run_name_length:
            context_dictionary["error"] = "The description contains {0} characters, " \
                                          "a maximum of {1} are allowed".\
                format(len(run_description), max_run_name_length)
            return context_dictionary

        most_recent_run: ReductionRun = matching_previous_runs_queryset.first()
        # User can choose whether to overwrite with the re-run or create new data
        overwrite_previous_data = bool(request.POST.get('overwrite_checkbox') == 'on')
        ReductionRunUtils.send_retry_message(request.user.id, most_recent_run, script_text, new_script_arguments,
                                             overwrite_previous_data)

    return context_dictionary

    return context_dictionary


def find_reason_to_avoid_re_run(matching_previous_runs_queryset):
    """
    Che
    """
    most_recent_run = matching_previous_runs_queryset.first()

    # Check old run exists - if it doesn't exist there's nothing to re-run!
    if most_recent_run is None:
        return False, f"Run number {most_recent_run.run_number} hasn't been ran by autoreduction yet."

    # Prevent multiple queueings of the same re-run
    queued_runs = matching_previous_runs_queryset.filter(status=STATUS.get_queued()).first()
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
