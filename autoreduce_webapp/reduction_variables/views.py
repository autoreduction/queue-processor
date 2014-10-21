from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.generic.base import View
from autoreduce_webapp.view_utils import login_and_uows_valid, render_with, require_staff
from reduction_variables.models import InstrumentVariable, RunVariable
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

    current_vars = {
        'run_start' : current_variables_run_start,
        'run_end' : next_variable_run_start,
        'variables' : current_variables,
        'instrument' : instrument,
    }

    context_dictionary = {
        'current_variables' : current_vars,
        'upcoming_variables' : upcoming_variables_dict,
    }

    try:
        #TODO: comment out when ICAT and uows are pointing at same session
        #with ICATCommunication(AUTH='uows', SESSION={'sessionid':request.session['sessionid']}) as icat:
        with ICATCommunication() as icat:
            owned_instruments = icat.get_owned_instruments(int(request.user.username))
            if not request.user.is_superuser and instrument not in owned_instruments:
                return HttpResponseForbidden('Access Forbidden')
    except Exception as icat_e:
        logging.error(icat_e.message)
        return HttpResponseForbidden('Could not verify access permission')

    return render_to_response('snippets/instrument_summary_variables.html', context_dictionary, RequestContext(request))

def instrument_variables(request, instrument, start=0, end=0):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))

def run_variables(request, run_number, run_version=0):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))
