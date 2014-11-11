from django.shortcuts import render,redirect
from django.core.context_processors import csrf
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.generic.base import View
from django.http import HttpResponse
from autoreduce_webapp.view_utils import login_and_uows_valid, render_with, require_staff
from reduction_variables.models import InstrumentVariable, RunVariable, ScriptFile
from reduction_variables.utils import InstrumentVariablesUtils, VariableUtils, MessagingUtils
from reduction_viewer.models import Instrument, ReductionRun, DataLocation
from reduction_viewer.utils import StatusUtils
from autoreduce_webapp.icat_communication import ICATCommunication
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL
import logging, re
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)

'''
    Imported into another view, thus no middlewear
'''
def instrument_summary(request, instrument):
    # Check the user has permission
    if not request.user.is_superuser and instrument not in request.session['owned_instruments']:
        raise PermissionDenied()

    instrument = Instrument.objects.get(name=instrument)
    completed_status = StatusUtils().get_completed()
    
    current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables(instrument.name)

    # Create a nested dictionary for by-run
    upcoming_variables_by_run_dict = {}
    for variables in upcoming_variables_by_run:
        if variables.start_run not in upcoming_variables_by_run_dict:
            upcoming_variables_by_run_dict[variables.start_run] = {
                'run_start' : variables.start_run,
                'run_end' : 0, # We'll fill this in after
                'variables' : [],
                'instrument' : instrument,
            }
        upcoming_variables_by_run_dict[variables.start_run]['variables'].append(variables)

    # Move the upcoming vars into an ordered list
    upcoming_variables_by_run_ordered = []
    for key in sorted(upcoming_variables_by_run_dict):
        upcoming_variables_by_run_ordered.append(upcoming_variables_by_run_dict[key])
    sorted(upcoming_variables_by_run_ordered, key=lambda r: r['run_start'])
    
    # Fill in the run end nunmbers
    run_end = 0;
    for run_number in sorted(upcoming_variables_by_run_dict.iterkeys(), reverse=True):
        upcoming_variables_by_run_dict[run_number]['run_end'] = run_end
        run_end = run_number-1

    try:
        next_variable_run_start = min(upcoming_variables_by_run_dict, key=upcoming_variables_by_run_dict.get)
    except ValueError:
        next_variable_run_start = 1
    
    current_vars = {
        'run_start' : current_variables[0].start_run,
        'run_end' : next_variable_run_start-1,
        'variables' : current_variables,
        'instrument' : instrument,
    }

    # Create a nested dictionary for by-experiment
    upcoming_variables_by_experiment_dict = {}
    for variables in upcoming_variables_by_experiment:
        if variables.experiment_reference not in upcoming_variables_by_experiment_dict:
            upcoming_variables_by_experiment_dict[variables.experiment_reference] = {
                'experiment' : variables.experiment_reference,
                'variables' : [],
                'instrument' : instrument,
            }
        upcoming_variables_by_experiment_dict[variables.experiment_reference]['variables'].append(variables)

    # Move the upcoming vars into an ordered list
    upcoming_variables_by_experiment_ordered = []
    for key in sorted(upcoming_variables_by_experiment_dict):
        upcoming_variables_by_experiment_ordered.append(upcoming_variables_by_experiment_dict[key])
    sorted(upcoming_variables_by_experiment_ordered, key=lambda r: r['experiment'])
    

    context_dictionary = {
        'instrument' : instrument,
        'current_variables' : current_vars,
        'upcoming_variables_by_run' : upcoming_variables_by_run_ordered,
        'upcoming_variables_by_experiment' : upcoming_variables_by_experiment_ordered,
    }

    return render_to_response('snippets/instrument_summary_variables.html', context_dictionary, RequestContext(request))

@require_staff
@render_with('instrument_variables.html')
def instrument_variables(request, instrument, start=0, end=0, experiment_reference=0):
    # Check the user has permission
    if not request.user.is_superuser and instrument not in request.session['owned_instruments']:
        raise PermissionDenied()
    
    instrument = Instrument.objects.get(name=instrument)

    if request.method == 'POST':
        # Truthy value comes back as text so we'll compare it to a string of "True"
        is_run_range = request.POST.get("variable-range-toggle-value", "True") == "True"

        if is_run_range:
            start = request.POST.get("run_start", 1)
            end = request.POST.get("run_end", None)

            if request.POST.get("is_editing", '') == 'True':
                old_variables = InstrumentVariable.objects.filter(instrument=instrument, start_run=start)
                script = old_variables[0].scripts.all()[0]
                default_variables = list(old_variables)
            else:
                script_binary = InstrumentVariablesUtils().get_current_script_text(instrument.name)
                script = ScriptFile(script=script_binary, file_name='reduce.py')
                script.save()
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
                script = old_variables[0].scripts.all()[0]
                default_variables = list(old_variables)
            else:

                script_binary = InstrumentVariablesUtils().get_current_script_text(instrument.name)
                script = ScriptFile(script=script_binary, file_name='reduce.py')
                script.save()
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
            variable.save()

        return redirect('instrument_summary', instrument=instrument.name)
    else:
        editing = (start>0 or experiment_reference>0)
        completed_status = StatusUtils().get_completed()
        processing_status = StatusUtils().get_processing()
        queued_status = StatusUtils().get_queued()

        try:
            latest_completed_run = ReductionRun.objects.filter(instrument=instrument, run_version=0, status=completed_status).order_by('-run_number').first().run_number
        except AttributeError :
            latest_completed_run = 0
        try:
            latest_processing_run = ReductionRun.objects.filter(instrument=instrument, run_version=0, status=processing_status).order_by('-run_number').first().run_number
        except AttributeError :
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
            # If no variables are saved, use the dfault ones from the reduce script
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

    default_variables = InstrumentVariablesUtils().get_variables_for_run(reduction_run)
    default_standard_variables = {}
    default_advanced_variables = {}
    for variable in default_variables:
        if variable.is_advanced:
            default_advanced_variables[variable.name] = variable
        else:
            default_standard_variables[variable.name] = variable

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
        'default_standard_variables' : default_standard_variables,
        'default_advanced_variables' : default_advanced_variables,
        'current_standard_variables' : current_standard_variables,
        'current_advanced_variables' : current_advanced_variables,
        'instrument' : reduction_run.instrument,
    }
    context_dictionary.update(csrf(request))
    return render_to_response('snippets/run_variables.html', context_dictionary, RequestContext(request))

@require_staff
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

        script_binary = InstrumentVariablesUtils().get_current_script_text(instrument.name)
        script = ScriptFile(script=script_binary, file_name='reduce.py')
        script.save()

        run_variables = reduction_run.run_variables.all()
        default_variables = InstrumentVariablesUtils().get_variables_for_run(reduction_run)
        new_variables = []

        for key,value in request.POST.iteritems():
            if 'var-' in key:
                if 'var-advanced-' in key:
                    name = key.replace('var-advanced-', '').replace('-',' ')
                    default_var = next((x for x in run_variables if x.name == name), next((x for x in default_variables if x.name == name), None))
                    if not default_var: continue
                    variable = RunVariable(
                        reduction_run=new_job,
                        name=default_var.name, 
                        value=value, 
                        is_advanced=True, 
                        type=default_var.type
                    )
                    variable.save()
                    variable.scripts.add(script)
                    variable.save()
                    new_variables.append(variable)
                if 'var-standard-' in key:
                    name = key.replace('var-standard-', '').replace('-',' ')
                    default_var = next((x for x in run_variables if x.name == name), next((x for x in default_variables if x.name == name), None))
                    if not default_var: continue
                    variable = RunVariable(
                        reduction_run=new_job,
                        name=default_var.name, 
                        value=value, 
                        is_advanced=False, 
                        type=default_var.type
                    )
                    variable.save()
                    variable.scripts.add(script)
                    variable.save()
                    new_variables.append(variable)
        
        if len(new_variables) == 0:
            new_job.delete()
            script.delete()
            context_dictionary = {
                'run' : None,
                'variables' : None,
                'queued' : ReductionRun.objects.filter(instrument=reduction_run.instrument, status=queued_status).count(),
                'error' : 'No variables were found to be submitted.'
            }
        else:
            try:
                MessagingUtils().send_pending(new_job)
                context_dictionary = {
                    'run' : new_job,
                    'variables' : new_variables,
                    'queued' : ReductionRun.objects.filter(instrument=reduction_run.instrument, status=queued_status).count(),
                }
            except Exception, e:
                new_job.delete()
                script.delete()
                context_dictionary = {
                    'run' : None,
                    'variables' : None,
                    'queued' : ReductionRun.objects.filter(instrument=reduction_run.instrument, status=queued_status).count(),
                    'error' : 'Failed to send new job. (%s)' % str(e),
                }
        
        return context_dictionary
    else:
        return redirect('instrument_summary', instrument=instrument.name)

@login_and_uows_valid
def preview_script(request, instrument, run_number=0, experiment_reference=0):
    reduce_script = ''

    '''
        Regular expressions to find the values of the exposed variables
        Each is seperated into two named groups, before & value.
        \s* is used to allow for unlimited spaces
        %s is later replaced with the variable name
        A live example can be found at: http://regex101.com/r/oJ7iY5/1
    '''
    standard_pattern = "(?P<before>(\s)standard_vars\s*=\s*\{(([\s\S])+)['|\"]%s['|\"]\s*:\s*)(?P<value>((?!,\n)[\S\s])+)"
    advanced_pattern = "(?P<before>(\s)advanced_vars\s*=\s*\{(([\s\S])+)['|\"]%s['|\"]\s*:\s*)(?P<value>((?!,\n)[\S\s])+)"

    if request.method == 'GET':
        instrument = Instrument.objects.get(name=instrument)
        if experiment_reference > 0:
            run_variables = InstrumentVariable.objects.filter(experiment_reference=experiment_reference, instrument=instrument)
        else:
            run_variables = InstrumentVariable.objects.filter(start_run=run_number, instrument=instrument)
        script_file = run_variables[0].scripts.all()[0].script.decode("utf-8")
        for variable in run_variables:
            if variable.is_advanced:
                pattern = advanced_pattern % variable.name
            else:
                pattern = standard_pattern % variable.name
            # Wrap the value in the correct syntax to indicate the type
            value = VariableUtils().wrap_in_type_syntax(variable.value, variable.type)
            value = '\g<before>%s' % value
            script_file = re.sub(pattern, value, script_file)

    elif request.method == 'POST':
        experiment_reference = request.POST.get('experiment_reference', None)
        run_number = request.POST.get('start_run', None)
        default_variables = None
        if experiment_reference > 0:
            default_variables = InstrumentVariable.objects.filter(experiment_reference=experiment_reference, instrument=instrument)
        elif run_number > 0:
            default_variables = InstrumentVariable.objects.filter(start_run=run_number, instrument=instrument)
        if default_variables:
            script_file = run_variables[0].scripts.all()[0].script.decode("utf-8")
        else:
            script_file = InstrumentVariablesUtils().get_current_script_text(instrument).decode("utf-8")
            default_variables = InstrumentVariablesUtils().get_default_variables(instrument)
        for key,value in request.POST.iteritems():
            if 'var-' in key:
                if 'var-advanced-' in key:
                    name = key.replace('var-advanced-', '').replace('-',' ')
                    default_var = next((x for x in default_variables if x.name == name), None)
                    if not default_var: continue
                    pattern = advanced_pattern % name

                if 'var-standard-' in key:
                    name = key.replace('var-standard-', '').replace('-',' ')
                    default_var = next((x for x in default_variables if x.name == name), None)
                    if not default_var: continue
                    pattern = standard_pattern % name
                # Wrap the value in the correct syntax to indicate the type
                value = VariableUtils().wrap_in_type_syntax(value, default_var.type)
                value = '\g<before>%s' % value
                script_file = re.sub(pattern, value, script_file)

    reduce_script = script_file

    response = HttpResponse(content_type='application/x-python')
    response['Content-Disposition'] = 'attachment; filename=reduce.py'
    response.write(reduce_script)
    return response