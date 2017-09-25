from django.shortcuts import redirect
from django.core.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseForbidden
from autoreduce_webapp.view_utils import login_and_uows_valid, render_with, has_valid_login, handle_redirect, check_permissions
from reduction_variables.models import InstrumentVariable, RunVariable
from reduction_variables.utils import VariableUtils, InstrumentVariablesUtils, MessagingUtils
from reduction_viewer.models import Instrument, ReductionRun
from reduction_viewer.utils import InstrumentUtils, StatusUtils, ReductionRunUtils

import logging, json
logger = logging.getLogger("app")

'''
    Imported into another view, thus no middleware
'''
def instrument_summary(request, instrument):
    instrument = Instrument.objects.get(name=instrument)
    
    current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables(instrument.name)

    # Create a nested dictionary for by-run
    upcoming_variables_by_run_dict = {}
    for variable in upcoming_variables_by_run:
        if variable.start_run not in upcoming_variables_by_run_dict:
            upcoming_variables_by_run_dict[variable.start_run] = {
                'run_start': variable.start_run,
                'run_end': 0, # We'll fill this in after
                'tracks_script': variable.tracks_script,
                'variables': [],
                'instrument': instrument,
            }
        upcoming_variables_by_run_dict[variable.start_run]['variables'].append(variable)

    # Fill in the run end numbers
    run_end = 0
    for run_number in sorted(upcoming_variables_by_run_dict.iterkeys(), reverse=True):
        upcoming_variables_by_run_dict[run_number]['run_end'] = run_end
        run_end = max(run_number-1, 0)

    current_start = current_variables[0].start_run
    next_run_starts = filter( lambda start: start > current_start
                            , sorted(upcoming_variables_by_run_dict.keys()) )
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

    context_dictionary.update(csrf(request))

    return render_to_response('snippets/instrument_summary_variables.html', context_dictionary, RequestContext(request))

@login_and_uows_valid
@check_permissions
def delete_instrument_variables(request, instrument=None, start=0, end=0, experiment_reference=None):
    instrument_name = instrument
    start, end = int(start), int(end)
    
    # We "save" an empty list to delete the previous variables.
    if experiment_reference is not None:
        InstrumentVariablesUtils().set_variables_for_experiment(instrument_name, [], experiment_reference)
    else:
        InstrumentVariablesUtils().set_variables_for_runs(instrument_name, [], start, end)

    return redirect('instrument_summary', instrument=instrument_name)

@login_and_uows_valid
@check_permissions
@render_with('instrument_variables.html')
def instrument_variables(request, instrument=None, start=0, end=0, experiment_reference=0):        
    instrument_name = instrument
    start, end = int(start), int(end)
    
    if request.method == 'POST':
        # Submission to modify variables.
        varList = [t for t in request.POST.items() if t[0].startswith("var-")] # [("var-standard-"+name, value) or ("var-advanced-"+name, value)]
        newVarDict = {"".join(t[0].split("-")[2:]) : t[1] for t in varList} # Remove the first two prefixes from the names to give {name: value}
         
        tracks_script = request.POST.get("track_script_checkbox") == "on"
        
        # Which variables should we modify?
        is_run_range = request.POST.get("variable-range-toggle-value", "True") == "True"
        start = int(request.POST.get("run_start", 1))
        end = int(request.POST.get("run_end", None)) if request.POST.get("run_end", None) else None
        
        experiment_reference = request.POST.get("experiment_reference_number", 1)
        
        
        def modifyVars(oldVars, newValues):
            for var in oldVars:
                if var.name in newValues:
                    var.value = newValues[var.name]
                var.tracks_script = tracks_script
                
        if is_run_range:
            # Get the variables for the first run, modify them, and set them for the given range.
            instrVars = InstrumentVariablesUtils().show_variables_for_run(instrument_name, start)
            modifyVars(instrVars, newVarDict)
            InstrumentVariablesUtils().set_variables_for_runs(instrument_name, instrVars, start, end)
        else:
            # Get the variables for the experiment, modify them, and set them for the experiment.
            instrVars = InstrumentVariablesUtils().show_variables_for_experiment(instrument_name, experiment_reference)
            if not instrVars: instrVars = InstrumentVariablesUtils().get_default_variables(instrument_name)
            modifyVars(instrVars, newVarDict)
            InstrumentVariablesUtils().set_variables_for_experiment(instrument_name, instrVars, experiment_reference)

        return redirect('instrument_summary', instrument=instrument_name)
        
        
    else:
        instrument = InstrumentUtils().get_instrument(instrument_name)
        
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
            variables = InstrumentVariablesUtils().show_variables_for_experiment(instrument_name, experiment_reference)
        else:
            variables = InstrumentVariablesUtils().show_variables_for_run(instrument_name, start)
        
        if not editing or not variables:
            variables = InstrumentVariablesUtils().show_variables_for_run(instrument.name)
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

        current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables(instrument.name)

        upcoming_run_variables = ','.join(list(set([str(var.start_run) for var in upcoming_variables_by_run]))) # Unique, comma-joined list of all start runs belonging to the upcoming variables.

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
            'last_instrument_run' : ReductionRun.objects.filter(instrument=instrument).exclude(status=StatusUtils().get_skipped()).order_by('-run_number')[0],
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


@login_and_uows_valid
@check_permissions
@render_with('submit_runs.html')
def submit_runs(request, instrument=None):
    logger.info('Submitting runs')
    instrument = Instrument.objects.get(name=instrument)
    if request.method == 'GET':
        processing_status = StatusUtils().get_processing()
        queued_status = StatusUtils().get_queued()
        skipped_status = StatusUtils().get_skipped()

        last_run = ReductionRun.objects.filter(instrument=instrument).exclude(status=skipped_status).order_by('-run_number').first()

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

@login_and_uows_valid
@check_permissions
@render_with('snippets/edit_variables.html')
def current_default_variables(request, instrument=None):
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
    Imported into another view, thus no middleware
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

@login_and_uows_valid
@check_permissions
@render_with('run_confirmation.html')
def run_confirmation(request, instrument=None):
    if request.method != 'POST':
        return redirect('instrument_summary', instrument=instrument.name)
        
        
    # POST
    instrument = Instrument.objects.get(name=instrument)
    run_numbers = []

    if 'run_number' in request.POST:
        run_numbers.append(int(request.POST.get('run_number')))
    else:
        range_string = request.POST.get('run_range').split(',')
        # Expand list
        for item in range_string:
            if '-' in item:
                split_range = item.split('-')
                run_numbers.extend(range(int(split_range[0]), int(split_range[1])+1)) # because this is a range, the end bound is exclusive!
            else:
                run_numbers.append(int(item))
        # Make sure run numbers are distinct
        run_numbers = set(run_numbers)

    queued_status = StatusUtils().get_queued()
    queue_count = ReductionRun.objects.filter(instrument=instrument, status=queued_status).count()

    context_dictionary = {
        'runs' : [],
        'variables' : None,
        'queued' : queue_count,
    }

    # Check that RB numbers are the same
    rb_number = ReductionRun.objects.filter(instrument=instrument, run_number__in=run_numbers).values_list('experiment__reference_number', flat=True).distinct()
    if len(rb_number) > 1:
        context_dictionary['error'] = 'Runs span multiple experiment numbers (' + ','.join(str(i) for i in rb_number) + ') please select a different range.'

    for run_number in run_numbers:
        old_reduction_run = ReductionRun.objects.filter(run_number=run_number).order_by('-run_version').first()

        # Check old run exists
        if old_reduction_run is None:
            context_dictionary['error'] = "Run number " + str(run_number) + " doesn't exist."

        use_current_script = request.POST.get('use_current_script', u"true").lower() == u"true"
        if use_current_script:
            script_text = InstrumentVariablesUtils().get_current_script_text(instrument.name)[0]
            default_variables = InstrumentVariablesUtils().get_default_variables(instrument.name)
        else:
            script_text = old_reduction_run.script
            default_variables = old_reduction_run.run_variables.all()
        
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
                    if len(value) > InstrumentVariable._meta.get_field('value').max_length:
                        context_dictionary['error'] = 'Value given in ' + str(name) + ' is too long.'
                    variable = RunVariable( name = default_var.name
                                          , value = value
                                          , is_advanced = is_advanced
                                          , type = default_var.type
                                          , help_text = default_var.help_text
                                          )
                    new_variables.append(variable)

        if len(new_variables) == 0:
            context_dictionary['error'] = 'No variables were found to be submitted.'

		# User can choose whether to overwrite with the re-run or create new data
        if request.POST.get('overwrite_checkbox') == 'on':
            overwrite_previous_data = True
        else:
            overwrite_previous_data = False

        if 'error' in context_dictionary:
            return context_dictionary
		
        run_description = request.POST.get('run_description')
        		
        new_job = ReductionRunUtils().createRetryRun(old_reduction_run, script=script_text, overwrite=overwrite_previous_data, variables=new_variables, username=request.user.username, description=run_description)

        try:
            MessagingUtils().send_pending(new_job)
            context_dictionary['runs'].append(new_job)
            context_dictionary['variables'] = new_variables
            
        except Exception as e:
            new_job.delete()
            context_dictionary['error'] = 'Failed to send new job. (%s)' % str(e)
            
    return context_dictionary


def preview_script(request, instrument=None, run_number=0, experiment_reference=0):
    # Can't use login decorator as this is requested via AJAX; need to return an error message on failure.
    if not has_valid_login(request):
        redirect_response = handle_redirect(request)
        if request.method == 'GET':
            return redirect_response
        else:
            error = {'redirect_url': redirect_response.url}
            return HttpResponseForbidden(json.dumps(error))
            
    # Make our own little function to use the permissions decorator on; if we catch a PermissionDenied, we should give a 403 error.
    # We also don't want to check the instrument in this case, since run-specific scripts ought to be viewable without owning the instrument.
    @check_permissions
    def permission_test(request, run_number=0, experiment_reference=0): pass
    try: permission_test(request, run_number, experiment_reference)
    except PermissionDenied:
        return HttpResponseForbidden()
        

    # Find the reduction run to get the script for.
    if request.method == 'GET':
        reduction_run = ReductionRun.objects.filter(run_number=run_number)
        use_current_script = False

    elif request.method == 'POST':
        lookup_run_number = request.POST.get('run_number', None)
        lookup_run_version = request.POST.get('run_version', None)
        use_current_script = request.POST.get('use_current_script', default=u"false").lower() == u"true"    
        reduction_run = ReductionRun.objects.filter(run_number=lookup_run_number, run_version=lookup_run_version)

    # Get the script text and variables from the given run; note the differing types of the variables in the two cases, which don't matter (we only access the parent Variable attributes).
    if reduction_run and not use_current_script:
        script_text = reduction_run[0].script
        script_variables = reduction_run[0].run_variables.all() # [InstrumentVariable]
    else:
        script_text = InstrumentVariablesUtils().get_current_script_text(instrument)[0]
        script_variables = InstrumentVariablesUtils().show_variables_for_run(instrument) # [RunVariable]
    
    
    def format_header(string):
        # Gives a #-enclosed string that looks header-y
        lines = ["#"*(len(string)+8)]*4
        lines[2:2] = ["##" + " "*(len(string)+4) + "##"]*3
        lines[3] = lines[3][:4] + string + lines[3][-4:]
        lines += [""]*1
        return lines
        
    def format_class(variables, name, indent):
        # Gives a Python class declaration with variable dicts as required.
        lines = ["class " + name + ":"]
        standard_vars, advanced_vars = filter(lambda var: not var.is_advanced, variables), filter(lambda var: var.is_advanced, variables)
        
        def make_dict(variables, name): 
            var_dict = {v.name: VariableUtils().convert_variable_to_type(v.value, v.type) for v in variables}
            return indent + name + " = " + str(var_dict)
        
        lines.append(make_dict(standard_vars, "standard_vars"))
        lines.append(make_dict(advanced_vars, "advanced_vars"))
        lines += [""]*3
        
        return lines
    
    def replace_variables(text):
        # Find the import/s for the reduction variables and remove them.
        lines = text.split("\n")
        imports = filter(lambda line: line.lstrip().startswith("import") or line.lstrip().startswith("from"), lines)
        import_vars = filter(lambda line: "reduce_vars" in line, imports)
        lines = [line for line in lines if line not in import_vars]
        
        # Print the header for the reduce.py script
        lines = format_header("Reduction script - reduce.py") + lines
        
        # Figure out space/tabs
        indent = "    " # Defaults to PEP 8 standard!
        if filter(lambda line: line.startswith("\t"), lines):
            indent = "\t"
        
        if import_vars:
            # Assume the import is of the form 'import reduce_vars as {name}' or 'import reduce_vars'
            classname = import_vars[0].rstrip().split(" ")[-1]
            # Print the variables and a header for them
            lines = format_header("Reduction variables") + format_class(script_variables, classname, indent) + lines
            
        return "\n".join(lines)
    
    
    new_script_text = replace_variables(script_text)
    
    response = HttpResponse(content_type='application/x-python')
    response['Content-Disposition'] = 'attachment; filename=reduce.py'
    response.write(new_script_text)
    return response
