"""
View functions for displaying Variable data
This imports into another view, thus no middleware
"""
import json
import logging

from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from autoreduce_webapp.view_utils import (login_and_uows_valid, render_with, has_valid_login,
                                          handle_redirect, check_permissions)
from reduction_variables.models import InstrumentVariable, RunVariable
from reduction_variables.utils import VariableUtils, InstrumentVariablesUtils, MessagingUtils
from reduction_viewer.models import Instrument, ReductionRun
from reduction_viewer.utils import InstrumentUtils, StatusUtils, ReductionRunUtils
from utilities import input_processing


LOGGER = logging.getLogger("app")


# pylint:disable=too-many-locals
def instrument_summary(request, instrument):
    """
    Handles view request for the instrument summary page
    """
    # pylint:disable=no-member
    instrument = Instrument.objects.get(name=instrument)

    # pylint:disable=invalid-name
    current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = \
        InstrumentVariablesUtils().get_current_and_upcoming_variables(instrument.name)

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
    for run_number in sorted(upcoming_variables_by_run_dict.iterkeys(), reverse=True):
        upcoming_variables_by_run_dict[run_number]['run_end'] = run_end
        run_end = max(run_number - 1, 0)

    current_start = current_variables[0].start_run
    # pylint:disable=deprecated-lambda
    next_run_starts = filter(lambda start: start > current_start
                             , sorted(upcoming_variables_by_run_dict.keys()))
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
def delete_instrument_variables(request, instrument=None, start=0, end=0,
                                experiment_reference=None):
    """
    Handles request for deleting instrument variables
    """
    instrument_name = instrument
    start, end = int(start), int(end)

    # We "save" an empty list to delete the previous variables.
    if experiment_reference is not None:
        InstrumentVariablesUtils().set_variables_for_experiment(instrument_name,
                                                                [], experiment_reference)
    else:
        InstrumentVariablesUtils().set_variables_for_runs(instrument_name, [], start, end)

    return redirect('instrument_summary', instrument=instrument_name)


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
            InstrumentVariablesUtils().set_variables_for_runs(instrument_name, instr_vars,
                                                              start, end)
        else:
            # Get the variables for the experiment, modify them, and set them for the experiment.
            instr_vars = InstrumentVariablesUtils().\
                show_variables_for_experiment(instrument_name,
                                              experiment_reference)
            if not instr_vars:
                instr_vars = InstrumentVariablesUtils().get_default_variables(instrument_name)
            modify_vars(instr_vars, new_var_dict)
            InstrumentVariablesUtils().set_variables_for_experiment(instrument_name,
                                                                    instr_vars,
                                                                    experiment_reference)

        return redirect('instrument_summary', instrument=instrument_name)

    else:
        instrument = InstrumentUtils().get_instrument(instrument_name)

        editing = (start > 0 or experiment_reference > 0)
        completed_status = StatusUtils().get_completed()
        processing_status = StatusUtils().get_processing()
        queued_status = StatusUtils().get_queued()

        try:
            # pylint:disable=no-member
            latest_completed_run = ReductionRun.\
                objects.filter(instrument=instrument,
                               run_version=0,
                               status=completed_status).order_by('-run_number').first().run_number
        except AttributeError:
            latest_completed_run = 0
        try:
            # pylint:disable=no-member
            latest_processing_run = ReductionRun.\
                objects.filter(instrument=instrument,
                               run_version=0,
                               status=processing_status).order_by('-run_number').first().run_number
        except AttributeError:
            latest_processing_run = 0

        if experiment_reference > 0:
            variables = InstrumentVariablesUtils().\
                show_variables_for_experiment(instrument_name, experiment_reference)
        else:
            variables = InstrumentVariablesUtils().\
                show_variables_for_run(instrument_name, start)

        if not editing or not variables:
            variables = InstrumentVariablesUtils().\
                show_variables_for_run(instrument.name)
            if not variables:
                variables = InstrumentVariablesUtils().get_default_variables(instrument.name)
            editing = False

        standard_vars = {}
        advanced_vars = {}
        for variable in variables:
            if variable.is_advanced:
                advanced_vars[variable.name] = variable
            else:
                standard_vars[variable.name] = variable

        # pylint:disable=invalid-name
        _, upcoming_variables_by_run, _ = \
            InstrumentVariablesUtils().get_current_and_upcoming_variables(instrument.name)

        # Unique, comma-joined list of all start runs belonging to the upcoming variables.
        upcoming_run_variables = ','.join(list(set([str(var.start_run) for var in
                                                    upcoming_variables_by_run])))

        default_variables = InstrumentVariablesUtils().get_default_variables(instrument.name)
        default_standard_variables = {}
        default_advanced_variables = {}
        for variable in default_variables:
            if variable.is_advanced:
                default_advanced_variables[variable.name] = variable
            else:
                default_standard_variables[variable.name] = variable
        # pylint:disable=no-member
        last_inst_run = ReductionRun.objects.filter(instrument=instrument).\
            exclude(status=StatusUtils().get_skipped()).order_by('-run_number')[0]

        # pylint:disable=no-member
        context_dictionary = {
            'instrument': instrument,
            'last_instrument_run': last_inst_run,
            'processing': ReductionRun.objects.filter(instrument=instrument,
                                                      status=processing_status),
            'queued': ReductionRun.objects.filter(instrument=instrument,
                                                  status=queued_status),
            'standard_variables': standard_vars,
            'advanced_variables': advanced_vars,
            'default_standard_variables': default_standard_variables,
            'default_advanced_variables': default_advanced_variables,
            'run_start': start,
            'run_end': end,
            'experiment_reference': experiment_reference,
            'minimum_run_start': max(latest_completed_run, latest_processing_run),
            'upcoming_run_variables': upcoming_run_variables,
            'editing': editing,
            'tracks_script': variables[0].tracks_script,
        }

        return context_dictionary


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
    instrument = Instrument.objects.get(name=instrument)
    if request.method == 'GET':
        processing_status = StatusUtils().get_processing()
        queued_status = StatusUtils().get_queued()
        skipped_status = StatusUtils().get_skipped()

        # pylint:disable=no-member
        last_run = ReductionRun.\
            objects.filter(instrument=instrument).\
            exclude(status=skipped_status).order_by('-run_number').first()

        standard_vars = {}
        advanced_vars = {}

        default_variables = InstrumentVariablesUtils().get_default_variables(instrument.name)
        default_standard_variables = {}
        default_advanced_variables = {}
        for variable in default_variables:
            if variable.is_advanced:
                advanced_vars[variable.name] = variable
                default_advanced_variables[variable.name] = variable
            else:
                standard_vars[variable.name] = variable
                default_standard_variables[variable.name] = variable

        # pylint:disable=no-member
        context_dictionary = {
            'instrument': instrument,
            'last_instrument_run': last_run,
            'processing': ReductionRun.objects.filter(instrument=instrument,
                                                      status=processing_status),
            'queued': ReductionRun.objects.filter(instrument=instrument,
                                                  status=queued_status),
            'standard_variables': standard_vars,
            'advanced_variables': advanced_vars,
            'default_standard_variables': default_standard_variables,
            'default_advanced_variables': default_advanced_variables,
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
    # pylint:disable=no-member
    instrument = Instrument.objects.filter(name=instrument_name)
    # pylint:disable=no-member
    reduction_run = ReductionRun.objects.get(instrument=instrument,
                                             run_number=run_number,
                                             run_version=run_version)
    variables = reduction_run.run_variables.all()

    standard_vars = {}
    advanced_vars = {}
    for variable in variables:
        if variable.is_advanced:
            advanced_vars[variable.name] = variable
        else:
            standard_vars[variable.name] = variable

    current_variables = InstrumentVariablesUtils().\
        get_default_variables(reduction_run.instrument.name)
    current_standard_variables = {}
    current_advanced_variables = {}
    for variable in current_variables:
        if variable.is_advanced:
            current_advanced_variables[variable.name] = variable
        else:
            current_standard_variables[variable.name] = variable

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


# pylint:disable=too-many-return-statements,too-many-branches,too-many-statements
@login_and_uows_valid
@check_permissions
@render_with('run_confirmation.html')
def run_confirmation(request, instrument):
    """
    Handles request for user to confirm re-run
    """
    if request.method != 'POST':
        return redirect('instrument_summary', instrument=instrument.name)

    # POST
    # pylint:disable=no-member
    instrument = Instrument.objects.get(name=instrument)
    range_string = request.POST.get('run_range')

    queued_status = StatusUtils().get_queued()
    # pylint:disable=no-member
    queue_count = ReductionRun.objects.filter(instrument=instrument, status=queued_status).count()
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

    # Check that RB numbers are the same for the range entered
    # pylint:disable=no-member
    rb_number = ReductionRun.objects.filter(instrument=instrument, run_number__in=run_numbers) \
        .values_list('experiment__reference_number', flat=True).distinct()
    if len(rb_number) > 1:
        context_dictionary['error'] = 'Runs span multiple experiment numbers ' \
                                      '(' + ','.join(str(i) for i in rb_number) + ')' \
                                      ' please select a different range.'
        return context_dictionary

    for run_number in run_numbers:
        # pylint:disable=no-member
        matching_previous_runs_queryset = ReductionRun.objects.\
            filter(instrument=instrument,
                   run_number=run_number).order_by('-run_version')
        most_recent_previous_run = matching_previous_runs_queryset.first()

        # Check old run exists
        if most_recent_previous_run is None:
            context_dictionary['error'] = "Run number %s hasn't been" \
                                          "ran by autoreduction yet." % str(run_number)

        # Check it is not currently queued
        queued_runs = matching_previous_runs_queryset.filter(status=queued_status).first()
        if queued_runs is not None:
            context_dictionary['error'] = "Run number {0} is already queued to run".\
                format(queued_runs.run_number)
            return context_dictionary

        use_current_script = request.POST.get('use_current_script', u"true").lower() == u"true"
        if use_current_script:
            script_text = InstrumentVariablesUtils().get_current_script_text(instrument.name)[0]
            default_variables = InstrumentVariablesUtils().get_default_variables(instrument.name)
        else:
            script_text = most_recent_previous_run.script
            default_variables = most_recent_previous_run.run_variables.all()

        new_variables = []

        for key, value in request.POST.iteritems():
            if 'var-' in key:
                name = None
                if 'var-advanced-' in key:
                    name = key.replace('var-advanced-', '').replace('-', ' ')
                    is_advanced = True
                if 'var-standard-' in key:
                    name = key.replace('var-standard-', '').replace('-', ' ')
                    is_advanced = False

                if name is not None:
                    default_var = next((x for x in default_variables if x.name == name), None)
                    if not default_var:
                        continue
                    # pylint:disable=protected-access,no-member
                    if len(value) > InstrumentVariable._meta.get_field('value').max_length:
                        context_dictionary['error'] = 'Value given in {} is too long.'\
                            .format(str(name))
                    variable = RunVariable(name=default_var.name,
                                           value=value,
                                           is_advanced=is_advanced,
                                           type=default_var.type,
                                           help_text=default_var.help_text)
                    new_variables.append(variable)

        if not new_variables:
            context_dictionary['error'] = 'No variables were found to be submitted.'

        # User can choose whether to overwrite with the re-run or create new data
        overwrite_previous_data = bool(request.POST.get('overwrite_checkbox') == 'on')

        if 'error' in context_dictionary:
            return context_dictionary

        run_description = request.POST.get('run_description')
        max_desc_len = 200
        if len(run_description) > max_desc_len:
            context_dictionary["error"] = "The description contains {0} characters, " \
                                          "a maximum of {1} are allowed".\
                format(len(run_description), max_desc_len)
            return context_dictionary

        new_job = ReductionRunUtils().createRetryRun(most_recent_previous_run,
                                                     script=script_text,
                                                     overwrite=overwrite_previous_data,
                                                     variables=new_variables,
                                                     username=request.user.username,
                                                     description=run_description)

        try:
            MessagingUtils().send_pending(new_job)
            context_dictionary['runs'].append(new_job)
            context_dictionary['variables'] = new_variables

        # pylint:disable=broad-except
        except Exception as exception:
            new_job.delete()
            context_dictionary['error'] = 'Failed to send new job. (%s)' % str(exception)

    return context_dictionary


def preview_script(request, instrument=None, run_number=0, experiment_reference=0):
    """
    Handles request to view a preview of the user script
    """
    # Can't use login decorator as this is requested via AJAX;
    # need to return an error message on failure.
    if not has_valid_login(request):
        redirect_response = handle_redirect(request)
        if request.method == 'GET':
            return redirect_response
        error = {'redirect_url': redirect_response.url}
        return HttpResponseForbidden(json.dumps(error))

    @check_permissions
    def permission_test(request, run_number=0, experiment_reference=0):
        """
        Make our own function to use the permissions decorator on;
        if we catch a PermissionDenied, we should give a 403 error.

        We also don't want to check the instrument in this case,
        since run-specific scripts ought to be viewable without owning the instrument.
        """
        pass

    try:
        permission_test(request, run_number, experiment_reference)
    except PermissionDenied:
        return HttpResponseForbidden()

    # Find the reduction run to get the script for.
    if request.method == 'GET':
        # pylint:disable=no-member
        reduction_run = ReductionRun.objects.filter(run_number=run_number)
        use_current_script = False

    elif request.method == 'POST':
        lookup_run_number = request.POST.get('run_number', None)
        lookup_run_version = request.POST.get('run_version', None)
        use_current_script = request.POST.get('use_current_script',
                                              default=u"false").lower() == u"true"
        # pylint:disable=no-member
        reduction_run = ReductionRun.objects.filter(run_number=lookup_run_number,
                                                    run_version=lookup_run_version)

    # Get the script text and variables from the given run;
    # note the differing types of the variables in the two cases,
    # which don't matter (we only access the parent Variable attributes).
    if reduction_run and not use_current_script:
        script_text = reduction_run[0].script
        script_variables = reduction_run[0].run_variables.all()  # [InstrumentVariable]
    else:
        script_text = InstrumentVariablesUtils().get_current_script_text(instrument)[0]
        # [RunVariable]
        script_variables = InstrumentVariablesUtils().show_variables_for_run(instrument)

    def format_header(string):
        """
        Gives a #-enclosed string that looks header-y
        """
        lines = ["#" * (len(string) + 8)] * 4
        lines[2:2] = ["##" + " " * (len(string) + 4) + "##"] * 3
        lines[3] = lines[3][:4] + string + lines[3][-4:]
        lines += [""] * 1
        return lines

    def format_class(variables, name, indent):
        """
        Gives a Python class declaration with variable dicts as required
        """
        lines = ["class " + name + ":"]
        # pylint:disable=deprecated-lambda
        standard_vars, advanced_vars = filter(lambda var: not var.is_advanced, variables), filter(
            lambda var: var.is_advanced, variables)

        def make_dict(variables, name):
            """
            Create and return a dictionary for name, variable pairs
            """
            var_dict = {v.name: VariableUtils().convert_variable_to_type(v.value, v.type)
                        for v in variables}
            return indent + name + " = " + str(var_dict)

        lines.append(make_dict(standard_vars, "standard_vars"))
        lines.append(make_dict(advanced_vars, "advanced_vars"))
        lines += [""] * 3

        return lines

    def replace_variables(text):
        """
        Replace variables with user defined text
        """
        # Find the import/s for the reduction variables and remove them.
        lines = text.split("\n")
        # pylint:disable=deprecated-lambda
        imports = filter(lambda line: line.lstrip().startswith("import")
                         or line.lstrip().startswith("from"), lines)
        # pylint:disable=deprecated-lambda
        import_vars = filter(lambda line: "reduce_vars" in line, imports)
        lines = [line for line in lines if line not in import_vars]

        # Print the header for the reduce.py script
        lines = format_header("Reduction script - reduce.py") + lines

        # Figure out space/tabs
        indent = "    "  # Defaults to PEP 8 standard!
        # pylint:disable=deprecated-lambda
        if filter(lambda line: line.startswith("\t"), lines):
            indent = "\t"

        if import_vars:
            # Assume import is of the form 'import reduce_vars as {name}' or 'import reduce_vars'
            classname = import_vars[0].rstrip().split(" ")[-1]
            # Print the variables and a header for them
            lines = format_header("Reduction variables") + \
                    format_class(script_variables, classname, indent) + lines

        return "\n".join(lines)

    new_script_text = replace_variables(script_text)

    response = HttpResponse(content_type='application/x-python')
    response['Content-Disposition'] = 'attachment; filename=reduce.py'
    response.write(new_script_text)
    return response
