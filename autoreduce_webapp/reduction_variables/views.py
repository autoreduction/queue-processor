from django.shortcuts import render,redirect
from django.core.context_processors import csrf
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.generic.base import View
from django.http import HttpResponse
from autoreduce_webapp.view_utils import login_and_uows_valid, render_with, require_staff
from reduction_variables.models import InstrumentVariable, RunVariable, ScriptFile
from reduction_variables.utils import InstrumentVariablesUtils, VariableUtils
from reduction_viewer.models import Instrument, ReductionRun
from reduction_viewer.utils import StatusUtils
from django.http import HttpResponseForbidden
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
        return HttpResponseForbidden('Access Forbidden')

    instrument = Instrument.objects.get(name=instrument)
    completed_status = StatusUtils().get_completed()
    try:
        latest_completed_run = ReductionRun.objects.filter(instrument=instrument, run_version=0, status=completed_status).order_by('-run_number').first().run_number
    except AttributeError :
        latest_completed_run = 0
    try:
        current_variables_run_start = InstrumentVariable.objects.filter(instrument=instrument,start_run__lte=latest_completed_run ).order_by('-start_run').first().start_run
    except AttributeError :
        current_variables_run_start = 1
    current_variables = InstrumentVariable.objects.filter(instrument=instrument,start_run=current_variables_run_start )
    upcoming_variables = InstrumentVariable.objects.filter(instrument=instrument,start_run__gt=latest_completed_run ).order_by('start_run')
    upcoming_variables_dict = {}
    for variables in upcoming_variables:
        if variables.start_run not in upcoming_variables_dict:
            upcoming_variables_dict[variables.start_run] = {
                'run_start' : variables.start_run,
                'run_end' : 0, # We'll fill this in after
                'variables' : [],
                'instrument' : instrument,
            }
        upcoming_variables_dict[variables.start_run]['variables'].append(variables)

    # Fill in the run end nunmbers
    run_end = 0;
    for run_number in sorted(upcoming_variables_dict.iterkeys(), reverse=True):
        upcoming_variables_dict[run_number]['run_end'] = run_end
        run_end = run_number-1

    try:
        next_variable_run_start = min(upcoming_variables_dict, key=upcoming_variables_dict.get)
    except ValueError:
        next_variable_run_start = 1

    # If no variables are saved, use the dfault ones from the reduce script
    if not current_variables:
        InstrumentVariablesUtils().set_default_instrument_variables(instrument.name, current_variables_run_start)
        current_variables = InstrumentVariable.objects.filter(instrument=instrument,start_run=current_variables_run_start )

    current_vars = {
        'run_start' : current_variables_run_start,
        'run_end' : next_variable_run_start-1,
        'variables' : current_variables,
        'instrument' : instrument,
    }

    context_dictionary = {
        'instrument' : instrument,
        'current_variables' : current_vars,
        'upcoming_variables' : upcoming_variables_dict,
    }

    return render_to_response('snippets/instrument_summary_variables.html', context_dictionary, RequestContext(request))

@login_and_uows_valid
@render_with('instrument_variables.html')
@require_staff
def instrument_variables(request, instrument, start=0, end=0):
    # Check the user has permission
    if not request.user.is_superuser and instrument not in request.session['owned_instruments']:
        return HttpResponseForbidden('Access Forbidden')
    
    instrument = Instrument.objects.get(name=instrument)

    if request.method == 'POST':
        # TODO: validate

        start = request.POST.get("run_start", 1)
        end = request.POST.get("run_end", None)

        # Remove any existing variables saved within the provided range
        if end:
            existing_variables = InstrumentVariable.objects.filter(instrument=instrument, start_run__gte=start, start_run__lte=end)
            # TODO: Set values for following period
        else:
            existing_variables = InstrumentVariable.objects.filter(instrument=instrument, start_run__gte=start)
        for existing in existing_variables:
            existing.delete()

        script_binary = InstrumentVariablesUtils().get_current_script(instrument.name)
        script = ScriptFile(script=script_binary, file_name='reduce.py')
        script.save()

        default_variables = InstrumentVariablesUtils().get_default_variables(instrument.name)
        for default_var in default_variables:
            form_name = 'var-'
            if default_var.is_advanced:
                form_name += 'advanced-'
            else:
                form_name += 'standard-'
            form_name += default_var.sanitized_name

            post_variable = request.POST.get(form_name, None)
            if post_variable:
                variable = InstrumentVariable(
                    instrument=instrument, 
                    name=default_var.name, 
                    value=post_variable, 
                    is_advanced=default_var.is_advanced, 
                    type=default_var.type,
                    start_run =start,
                    )
            else:
                variable = default_var
                variable.scripts.clear()
            variable.save()
            variable.scripts.add(script)
            varaible.save()

        return redirect('instrument_summary', instrument=instrument.name)
    else:

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

        # If no variables are saved, use the dfault ones from the reduce script
        if not variables:
            InstrumentVariablesUtils().set_default_instrument_variables(instrument.name, start)
            variables = InstrumentVariable.objects.filter(instrument=instrument,start_run=start )

        standard_vars = {}
        advanced_vars = {}
        for variable in variables:
            if variable.is_advanced:
                advanced_vars[variable.name] = variable
            else:
                standard_vars[variable.name] = variable

        context_dictionary = {
            'instrument' : instrument,
            'processing' : ReductionRun.objects.filter(instrument=instrument, status=processing_status),
            'queued' : ReductionRun.objects.filter(instrument=instrument, status=queued_status),
            'standard_variables' : standard_vars,
            'advanced_variables' : advanced_vars,
            'run_start' : start,
            'run_end' : end,
            'minimum_run_start' : max(latest_completed_run, latest_processing_run)
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

    context_dictionary = {
        'run_number' : run_number,
        'run_version' : run_version,
        'standard_variables' : standard_vars,
        'advanced_variables' : advanced_vars,
        'instrument' : reduction_run.instrument,
    }
    context_dictionary.update(csrf(request))
    return render_to_response('snippets/run_variables.html', context_dictionary, RequestContext(request))

@login_and_uows_valid
@render_with('run_confirmation.html')
@require_staff
def run_confirmation(request, run_number, run_version=0):
    # TODO: Create new reduction run from post variables

    reduction_run = ReductionRun.objects.get(run_number=run_number, run_version=run_version)
    queued_status = StatusUtils().get_queued()

    context_dictionary = {
        'run' : reduction_run,
        'queued' : ReductionRun.objects.filter(instrument=reduction_run.instrument, status=queued_status).count(),
    }
    return context_dictionary

@login_and_uows_valid
def preview_script(request, instrument, run_number):
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
        script_file = InstrumentVariablesUtils().get_current_script(instrument).decode("utf-8")
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