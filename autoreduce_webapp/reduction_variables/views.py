from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.generic.base import View
from autoreduce_webapp.view_utils import login_and_uows_valid, render_with, require_staff
from reduction_variables.models import InstrumentVariable, RunVariable
from reduction_variables.utils import InstrumentVariablesUtils
from reduction_viewer.models import Instrument, ReductionRun
from reduction_viewer.utils import StatusUtils
from django.http import HttpResponseForbidden
from autoreduce_webapp.icat_communication import ICATCommunication
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL
import logging
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)

def run_confirmation(request, run_number, run_version=0):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))

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
        next_variable_run_start = 0

    # If no variables are saved, use the dfault ones from the reduce script
    if not current_variables:
        InstrumentVariablesUtils().set_default_instrument_variables(instrument, current_variables_run_start)
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

def instrument_variables(request, instrument, start=0, end=0):
    # Check the user has permission
    if not request.user.is_superuser and instrument not in request.session['owned_instruments']:
        return HttpResponseForbidden('Access Forbidden')
    
    instrument = Instrument.objects.get(name=instrument)

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

    if start == 0 and end == 0:
        try:
            start = InstrumentVariable.objects.filter(instrument=instrument,start_run__lte=latest_completed_run ).order_by('-start_run').first().start_run
        except AttributeError :
            start = 1
        
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

    return render_to_response('instrument_variables.html', context_dictionary, RequestContext(request))

def run_variables(request, run_number, run_version=0):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))
