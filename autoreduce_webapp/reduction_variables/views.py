from django.shortcuts import redirect
from django.core.context_processors import csrf
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from autoreduce_webapp.view_utils import login_and_uows_valid, render_with, require_staff
from reduction_variables.models import InstrumentVariable, RunVariable, ScriptFile
from reduction_variables.utils import InstrumentVariablesUtils, VariableUtils, MessagingUtils, ScriptUtils
from reduction_viewer.models import Instrument, ReductionRun, DataLocation
from reduction_viewer.utils import StatusUtils

import logging, re
logger = logging.getLogger(__name__)

'''
    Imported into another view, thus no middlewear
'''
def instrument_summary(request, instrument):
    # Check the user has permission
    #if not request.user.is_superuser and instrument not in request.session['owned_instruments']:
    #    raise PermissionDenied()

    instrument = Instrument.objects.get(name=instrument)
    
    current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables(instrument.name)

    # Create a nested dictionary for by-run
    upcoming_variables_by_run_dict = {}
    for variables in upcoming_variables_by_run:
        if variables.start_run not in upcoming_variables_by_run_dict:
            upcoming_variables_by_run_dict[variables.start_run] = {
                'run_start': variables.start_run,
                'run_end': 0, # We'll fill this in after
                'tracks_script': variables.tracks_script,
                'variables': [],
                'instrument': instrument,
            }
        upcoming_variables_by_run_dict[variables.start_run]['variables'].append(variables)

    # Move the upcoming vars into an ordered list
    upcoming_variables_by_run_ordered = []
    for key in sorted(upcoming_variables_by_run_dict):
        upcoming_variables_by_run_ordered.append(upcoming_variables_by_run_dict[key])
    sorted(upcoming_variables_by_run_ordered, key=lambda r: r['run_start'])
    
    # Fill in the run end numbers
    run_end = 0
    for run_number in sorted(upcoming_variables_by_run_dict.iterkeys(), reverse=True):
        upcoming_variables_by_run_dict[run_number]['run_end'] = run_end
        run_end = run_number-1

    try:
        next_variable_run_start = min(upcoming_variables_by_run_dict, key=upcoming_variables_by_run_dict.get)
    except ValueError:
        next_variable_run_start = 1
    
    current_vars = {
        'run_start': current_variables[0].start_run,
        'run_end': next_variable_run_start-1,
        'tracks_script': current_variables[0].tracks_script,
        'variables': current_variables,
        'instrument': instrument,
    }

    # Create a nested dictionary for by-experiment
    upcoming_variables_by_experiment_dict = {}
    for variables in upcoming_variables_by_experiment:
        if variables.experiment_reference not in upcoming_variables_by_experiment_dict:
            upcoming_variables_by_experiment_dict[variables.experiment_reference] = {
                'experiment': variables.experiment_reference,
                'variables': [],
                'instrument': instrument,
            }
        upcoming_variables_by_experiment_dict[variables.experiment_reference]['variables'].append(variables)

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

    return render_to_response('snippets/instrument_summary_variables.html', context_dictionary, RequestContext(request))

#@require_staff
@login_and_uows_valid
@render_with('instrument_variables.html')
def instrument_variables(request, instrument, start=0, end=0, experiment_reference=0):
    # Check the user has permission
    #if not request.user.is_superuser and instrument not in request.session['owned_instruments']:
    #    raise PermissionDenied()
    
    instrument = Instrument.objects.get(name=instrument)
    script = None
    script_vars = None
    if request.method == 'POST':
        # Truth value comes back as text so we'll compare it to a string of "True"
        is_run_range = request.POST.get("variable-range-toggle-value", "True") == "True"

        track_scripts = request.POST.get("track_script_checkbox") == "on"

        if is_run_range:
            start = request.POST.get("run_start", 1)
            end = request.POST.get("run_end", None)

            if request.POST.get("is_editing", '') == 'True':
                old_variables = InstrumentVariable.objects.filter(instrument=instrument, start_run=start)
                if old_variables:
                    script, script_vars = ScriptUtils().get_reduce_scripts(old_variables[0].scripts.all())
                    default_variables = list(old_variables)
            if script is None or request.POST.get("is_editing", '') != 'True':
                script_binary, script_vars_binary = InstrumentVariablesUtils().get_current_script_text(instrument.name)
                script = ScriptFile(script=script_binary, file_name='reduce.py')
                script.save()
                script_vars = ScriptFile(script=script_vars_binary, file_name='reduce_vars.py')
                script_vars.save()
                default_variables = InstrumentVariablesUtils().get_default_variables(instrument.name)

            # Remove any existing variables saved within the provided range
            if end and int(end) > 0:
                existing_variables = InstrumentVariable.objects.filter(instrument=instrument, start_run__gte=start, start_run__lte=end)
                # Create default variables for after the run end if they don't already exist
                if not InstrumentVariable.objects.filter(instrument=instrument, start_run=int(end)+1):
                    InstrumentVariablesUtils().set_default_instrument_variables(instrument.name, int(end)+1)
            else:
                existing_variables = InstrumentVariable.objects.filter(instrument=instrument, start_run__gte=start)
            for existing in existing_variables:
                existing.delete()
        else:
            experiment_reference = request.POST.get("experiment_reference_number", 1)

            if request.POST.get("is_editing", '') == 'True':
                old_variables = InstrumentVariable.objects.filter(instrument=instrument, experiment_reference=experiment_reference)
                if old_variables:
                    script, script_vars = ScriptUtils().get_reduce_scripts(old_variables[0].scripts.all())
                    default_variables = list(old_variables)
            if script is None or request.POST.get("is_editing", '') != 'True':
                script_binary, script_vars_binary = InstrumentVariablesUtils().get_current_script_text(instrument.name)
                script = ScriptFile(script=script_binary, file_name='reduce.py')
                script.save()
                script_vars = ScriptFile(script=script_vars_binary, file_name='reduce_vars.py')
                script_vars.save()
                default_variables = InstrumentVariablesUtils().get_default_variables(instrument.name)

            existing_variables = InstrumentVariable.objects.filter(instrument=instrument, experiment_reference=experiment_reference)
            for existing in existing_variables:
                existing.delete()

        for default_var in default_variables:
            form_name = 'var-'
            if default_var.is_advanced:
                form_name += 'advanced-'
            else:
                form_name += 'standard-'
            form_name += default_var.sanitized_name()

            post_variable = request.POST.get(form_name, None)
            if post_variable:
                variable = InstrumentVariable(
                    instrument=instrument, 
                    name=default_var.name, 
                    value=post_variable, 
                    is_advanced=default_var.is_advanced, 
                    type=default_var.type,
                    tracks_script=track_scripts,
                    help_text=default_var.help_text,
                    )
                if is_run_range:
                    variable.start_run = start
                else:
                    variable.experiment_reference = experiment_reference
            else:
                variable = default_var
                variable.pk = None
                variable.id = None
                variable.scripts.clear()
            variable.save()
            variable.scripts.add(script)
            variable.scripts.add(script_vars)
            variable.save()

        return redirect('instrument_summary', instrument=instrument.name)
    else:
        editing = (start > 0 or experiment_reference > 0)
        completed_status = StatusUtils().get_completed()
        processing_status = StatusUtils().get_processing()
        queued_status = StatusUtils().get_queued()

        try:
            latest_completed_run = ReductionRun.objects.filter(instrument=instrument, run_version=0, status=completed_status).order_by('-run_number').first().run_number
        except AttributeError:
            latest_completed_run = 0
        try:
            latest_processing_run = ReductionRun.objects.filter(instrument=instrument, run_version=0, status=processing_status).order_by('-run_number').first().run_number
        except AttributeError:
            latest_processing_run = 0

        if experiment_reference > 0:
            variables = InstrumentVariable.objects.filter(instrument=instrument,experiment_reference=experiment_reference)
        else:
            if not start and not end:
                try:
                    start = InstrumentVariable.objects.filter(instrument=instrument,start_run__lte=latest_completed_run ).order_by('-start_run').first().start_run
                except AttributeError :
                    start = 1
            if not start:
                start = 1
            if not end:
                end = 0
            variables = InstrumentVariable.objects.filter(instrument=instrument,start_run=start)
        
        if not editing:
            variables = InstrumentVariablesUtils().get_default_variables(instrument.name)
        elif not variables:
            # If no variables are saved, use the default ones from the reduce script
            editing = False
            InstrumentVariablesUtils().set_default_instrument_variables(instrument.name, start)
            variables = InstrumentVariable.objects.filter(instrument=instrument,start_run=start )

        standard_vars = {}
        advanced_vars = {}
        for variable in variables:
            if variable.is_advanced:
                advanced_vars[variable.name] = variable
            else:
                standard_vars[variable.name] = variable

        current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables(instrument.name)

        upcoming_run_variables = ','.join([str(i) for i in upcoming_variables_by_run.values_list('start_run', flat=True).distinct()])

        default_variables = InstrumentVariablesUtils().get_default_variables(instrument.name)
        default_standard_variables = {}
        default_advanced_variables = {}
        for variable in default_variables:
            if variable.is_advanced:
                default_advanced_variables[variable.name] = variable
            else:
                default_standard_variables[variable.name] = variable

        context_dictionary = {
            'instrument' : instrument,
            'last_instrument_run' : ReductionRun.objects.filter(instrument=instrument).order_by('-run_number')[0],
            'processing' : ReductionRun.objects.filter(instrument=instrument, status=processing_status),
            'queued' : ReductionRun.objects.filter(instrument=instrument, status=queued_status),
            'standard_variables' : standard_vars,
            'advanced_variables' : advanced_vars,
            'default_standard_variables' : default_standard_variables,
            'default_advanced_variables' : default_advanced_variables,
            'run_start' : start,
            'run_end' : end,
            'experiment_reference' : experiment_reference,
            'minimum_run_start' : max(latest_completed_run, latest_processing_run),
            'upcoming_run_variables' : upcoming_run_variables,
            'editing' : editing,
            'tracks_script' : variables[0].tracks_script,
        }
        context_dictionary.update(csrf(request))

        return context_dictionary

#@require_staff
@login_and_uows_valid
@render_with('submit_runs.html')
def submit_runs(request, instrument):
    # Check the user has permission
    if not request.user.is_superuser and instrument not in request.session['owned_instruments']:
        raise PermissionDenied()

    instrument = Instrument.objects.get(name=instrument)

    if request.method == 'POST':
        # TODO: Need to check ICAT credentials
        start = int(request.POST.get("run_start", 1))
        end = int(request.POST.get("run_end", start))

        for run_number in range(start, end):
            old_reduction_run = ReductionRun.objects.filter(run_number=run_number).order_by('-run_version').first()
            if not old_reduction_run:
                continue
            queued_status = StatusUtils().get_queued()
            new_job = ReductionRun(
                instrument=instrument,
                run_number=run_number,
                run_name=request.POST.get('run_description'),
                run_version=old_reduction_run.run_version+1,
                experiment=old_reduction_run.experiment, #TODO: Get from ICAT
                started_by=request.user.username,
                status=queued_status,
                )
            new_job.save()

            for data_location in old_reduction_run.data_location.all(): #TODO: If old run get from there otherwise should be able to create (maybe by assuming same format as old data locs)
                new_data_location = DataLocation(file_path=data_location.file_path, reduction_run=new_job)
                new_data_location.save()
                new_job.data_location.add(new_data_location)

            script_binary, script_vars_binary = InstrumentVariablesUtils().get_current_script_text(instrument.name)
            default_variables = InstrumentVariablesUtils().get_variables_from_current_script(instrument.name)

            script = ScriptFile(script=script_binary, file_name='reduce.py')
            script.save()
            script_vars = ScriptFile(script=script_vars_binary, file_name='reduce_vars.py')
            script_vars.save()

            new_variables = []

            for key,value in request.POST.iteritems():
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
                        variable = RunVariable(
                            reduction_run=new_job,
                            name=default_var.name,
                            value=value,
                            is_advanced=is_advanced,
                            type=default_var.type,
                            help_text=default_var.help_text
                        )
                        variable.save()
                        variable.scripts.add(script)
                        variable.scripts.add(script_vars)
                        variable.save()
                        new_variables.append(variable)

            queue_count = ReductionRun.objects.filter(instrument=instrument, status=queued_status).count()

            context_dictionary = {
                'run' : None,
                'variables' : None,
                'queued' : queue_count,
            }

            if len(new_variables) == 0:
                new_job.delete()
                script.delete()
                script_vars.delete()
                context_dictionary['error'] = 'No variables were found to be submitted.'
            else:
                try:
                    MessagingUtils().send_pending(new_job)
                    context_dictionary['run'] = new_job
                    context_dictionary['variables'] = new_variables
                except Exception, e:
                    new_job.delete()
                    script.delete()
                    script_vars.delete()
                    context_dictionary['error'] = 'Failed to send new job. (%s)' % str(e)

        return redirect('instrument_summary', instrument=instrument.name)
    else:
        processing_status = StatusUtils().get_processing()
        queued_status = StatusUtils().get_queued()

        last_run = ReductionRun.objects.filter(instrument=instrument).order_by('-run_number')[0]

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

        context_dictionary = {
            'instrument' : instrument,
            'last_instrument_run' : last_run,
            'processing' : ReductionRun.objects.filter(instrument=instrument, status=processing_status),
            'queued' : ReductionRun.objects.filter(instrument=instrument, status=queued_status),
            'standard_variables' : standard_vars,
            'advanced_variables' : advanced_vars,
            'default_standard_variables' : default_standard_variables,
            'default_advanced_variables' : default_advanced_variables,
        }
        context_dictionary.update(csrf(request))

        return context_dictionary


#@require_staff
@login_and_uows_valid
@render_with('snippets/edit_variables.html')
def current_default_variables(request, instrument):
    variables = InstrumentVariablesUtils().get_default_variables(instrument)
    standard_vars = {}
    advanced_vars = {}
    for variable in variables:
        if variable.is_advanced:
            advanced_vars[variable.name] = variable
        else:
            standard_vars[variable.name] = variable
    context_dictionary = {
        'instrument' : instrument,
        'standard_variables' : standard_vars,
        'advanced_variables' : advanced_vars,
    }
    context_dictionary.update(csrf(request))
    return context_dictionary

'''
    Imported into another view, thus no middlewear
'''
def run_summary(request, run_number, run_version=0):
    reduction_run = ReductionRun.objects.get(run_number=run_number, run_version=run_version)
    variables = reduction_run.run_variables.all()

    standard_vars = {}
    advanced_vars = {}
    for variable in variables:
        if variable.is_advanced:
            advanced_vars[variable.name] = variable
        else:
            standard_vars[variable.name] = variable

    current_variables = InstrumentVariablesUtils().get_default_variables(reduction_run.instrument.name)
    current_standard_variables = {}
    current_advanced_variables = {}
    for variable in current_variables:
        if variable.is_advanced:
            current_advanced_variables[variable.name] = variable
        else:
            current_standard_variables[variable.name] = variable

    context_dictionary = {
        'run_number' : run_number,
        'run_version' : run_version,
        'standard_variables' : standard_vars,
        'advanced_variables' : advanced_vars,
        'default_standard_variables' : standard_vars,
        'default_advanced_variables' : advanced_vars,
        'current_standard_variables' : current_standard_variables,
        'current_advanced_variables' : current_advanced_variables,
        'instrument' : reduction_run.instrument,
    }
    context_dictionary.update(csrf(request))
    return render_to_response('snippets/run_variables.html', context_dictionary, RequestContext(request))

#@require_staff
@login_and_uows_valid
@render_with('run_confirmation.html')
def run_confirmation(request, run_number, run_version=0):
    reduction_run = ReductionRun.objects.get(run_number=run_number, run_version=run_version)
    instrument = reduction_run.instrument

    if request.method == 'POST':
        highest_version = ReductionRun.objects.filter(run_number=run_number).order_by('-run_version').first().run_version
        queued_status = StatusUtils().get_queued()
        new_job = ReductionRun(
            instrument=instrument,
            run_number=run_number,
            run_name=request.POST.get('run_description'),
            run_version=(highest_version+1),
            experiment=reduction_run.experiment,
            started_by=request.user.username,
            status=queued_status,
            )
        new_job.save()
        for data_location in reduction_run.data_location.all():
            new_data_location = DataLocation(file_path=data_location.file_path, reduction_run=new_job)
            new_data_location.save()
            new_job.data_location.add(new_data_location)

        use_current_script = request.POST.get('use_current_script', u"false").lower() == u"true"
        run_variables = reduction_run.run_variables.all()

        if use_current_script:
            script_binary, script_vars_binary = InstrumentVariablesUtils().get_current_script_text(instrument.name)
            default_variables = InstrumentVariablesUtils().get_variables_from_current_script(reduction_run.instrument.name)
        else:
            script_binary, script_vars_binary = ScriptUtils().get_reduce_scripts_binary(run_variables[0].scripts.all())
            default_variables = run_variables

        script = ScriptFile(script=script_binary, file_name='reduce.py')
        script.save()
        script_vars = ScriptFile(script=script_vars_binary, file_name='reduce_vars.py')
        script_vars.save()

        new_variables = []

        for key,value in request.POST.iteritems():
            if 'var-' in key:
                name = None
                if 'var-advanced-' in key:
                    name = key.replace('var-advanced-', '').replace('-', ' ')
                    is_advanced = True
                if 'var-standard-' in key:
                    name = key.replace('var-standard-', '').replace('-', ' ')
                    is_advanced = False
                    
                if name is not None:
                    default_var = next((x for x in run_variables if x.name == name), next((x for x in default_variables if x.name == name), None))
                    if not default_var:
                        continue
                    variable = RunVariable(
                        reduction_run=new_job,
                        name=default_var.name,
                        value=value,
                        is_advanced=is_advanced,
                        type=default_var.type,
                        help_text=default_var.help_text
                    )
                    variable.save()
                    variable.scripts.add(script)
                    variable.scripts.add(script_vars)
                    variable.save()
                    new_variables.append(variable)

        queue_count = ReductionRun.objects.filter(instrument=reduction_run.instrument, status=queued_status).count()

        context_dictionary = {
            'run' : None,
            'variables' : None,
            'queued' : queue_count,
        }

        if len(new_variables) == 0:
            new_job.delete()
            script.delete()
            script_vars.delete()
            context_dictionary['error'] = 'No variables were found to be submitted.'
        else:
            try:
                MessagingUtils().send_pending(new_job)
                context_dictionary['run'] = new_job
                context_dictionary['variables'] = new_variables
            except Exception, e:
                new_job.delete()
                script.delete()
                script_vars.delete()
                context_dictionary['error'] = 'Failed to send new job. (%s)' % str(e),

        return context_dictionary
    else:
        return redirect('instrument_summary', instrument=instrument.name)

@login_and_uows_valid
def preview_script(request, instrument, run_number=0, experiment_reference=0):
    reduce_script = '"""\nreduce_vars.py\n"""\n\n'

    '''
        Regular expressions to find the values of the exposed variables
        Each is seperated into two named groups, before & value.
        \s* is used to allow for unlimited spaces
        %s is later replaced with the variable name
        A live example can be found at: https://regex101.com/r/oJ7iY5/3
    '''
    standard_pattern = "(?P<before>(\s)standard_vars\s*=\s*\{(([\s\S])+)['|\"]%s['|\"]\s*:\s*)(?P<value>((?!,(\s+)\n|\n)[\S\s])+)"
    advanced_pattern = "(?P<before>(\s)advanced_vars\s*=\s*\{(([\s\S])+)['|\"]%s['|\"]\s*:\s*)(?P<value>((?!,(\s+)\n|\n)[\S\s])+)"

    instrument_object = Instrument.objects.get(name=instrument)

    if request.method == 'GET':
        if int(experiment_reference) > 0:
            run_variables = InstrumentVariable.objects.filter(experiment_reference=experiment_reference, instrument=instrument_object)
        else:
            run_variables = InstrumentVariable.objects.filter(start_run=run_number, instrument=instrument_object)
        if run_variables[0].tracks_script:
            script, script_vars = InstrumentVariablesUtils().get_current_script_text(instrument)
        else:
            script, script_vars = ScriptUtils().get_reduce_scripts_binary(run_variables[0].scripts.all())
        script_file = script.decode("utf-8")
        script_vars_file = script_vars.decode("utf-8")

        for variable in run_variables:
            if variable.is_advanced:
                pattern = advanced_pattern % variable.name
            else:
                pattern = standard_pattern % variable.name
            # Wrap the value in the correct syntax to indicate the type
            value = VariableUtils().wrap_in_type_syntax(variable.value, variable.type)
            value = '\g<before>%s' % value
            script_vars_file = re.sub(pattern, value, script_vars_file)

    elif request.method == 'POST':
        experiment_reference = request.POST.get('experiment_reference_number', None)
        start_run = request.POST.get('run_start', None)
        lookup_run_number = request.POST.get('run_number', None)
        lookup_run_version = request.POST.get('run_version', None)
        if 'use_current_script' in request.POST:
            use_current_script = request.POST.get('use_current_script', u"false").lower() == u"true"
        else:
            use_current_script = request.POST.get("track_script_checkbox") == "on"

        default_variables = None
        if not use_current_script:
            if lookup_run_number is not None:
                try:
                    run = ReductionRun.objects.get(run_number=lookup_run_number, run_version=lookup_run_version)
                    default_variables = RunVariable.objects.filter(reduction_run=run)
                except Exception as e:
                    logger.info("Run not found :" + str(e))
            else:
                if int(experiment_reference) > 0:
                    default_variables = InstrumentVariable.objects.filter(experiment_reference=experiment_reference, instrument=instrument_object)
                elif int(start_run) > 0:
                    default_variables = InstrumentVariable.objects.filter(start_run=start_run, instrument=instrument_object)

        if default_variables:
            script_binary, script_vars_binary = ScriptUtils().get_reduce_scripts_binary(default_variables[0].scripts.all())
        else:
            script_binary, script_vars_binary = InstrumentVariablesUtils().get_current_script_text(instrument)
            default_variables = InstrumentVariablesUtils().get_default_variables(instrument)

        script_file = script_binary.decode("utf-8")
        script_vars_file = script_vars_binary.decode("utf-8")

        for key,value in request.POST.iteritems():
            if 'var-' in key:
                pattern = None
                if 'var-advanced-' in key:
                    name = key.replace('var-advanced-', '').replace('-',' ')
                    default_var = next((x for x in default_variables if x.name == name), None)
                    if not default_var:
                        continue
                    pattern = advanced_pattern % name

                if 'var-standard-' in key:
                    name = key.replace('var-standard-', '').replace('-',' ')
                    default_var = next((x for x in default_variables if x.name == name), None)
                    if not default_var:
                        continue
                    pattern = standard_pattern % name

                if pattern is not None:
                    # Wrap the value in the correct syntax to indicate the type
                    value = VariableUtils().wrap_in_type_syntax(value, default_var.type)
                    value = '\g<before>%s' % value
                    script_vars_file = re.sub(pattern, value, script_vars_file)

    reduce_script += script_vars_file
    reduce_script += '\n\n"""\nreduce.py\n"""\n\n'
    reduce_script += script_file
    
    response = HttpResponse(content_type='application/x-python')
    response['Content-Disposition'] = 'attachment; filename=reduce & reduce_vars.py'
    response.write(reduce_script)
    return response