from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import logout as django_logout, authenticate, login
from django.contrib.auth.decorators import login_required
from autoreduce_webapp.uows_client import UOWSClient
from autoreduce_webapp.icat_communication import ICATCommunication
from autoreduce_webapp.settings import UOWS_LOGIN_URL
from reduction_viewer.models import Experiment, ReductionRun, Instrument
from reduction_viewer.utils import StatusUtils
from autoreduce_webapp.view_utils import login_and_uows_valid, render_with, require_staff
from django.http import HttpResponse
import operator 

def index(request):
    return_url = UOWS_LOGIN_URL + request.build_absolute_uri()
    if request.GET.get('next'):
        return_url = UOWS_LOGIN_URL + request.build_absolute_uri(request.GET.get('next'))

    use_query_next = request.build_absolute_uri(request.GET.get('next'))
    default_next = 'run_list'

    if request.user.is_authenticated() and 'sessionid' in request.session and UOWSClient().check_session(request.session['sessionid']):
        if request.GET.get('next'):
            return_url = use_query_next
        else:
            return_url = default_next
    elif request.GET.get('sessionid'):
        user = authenticate(token=request.GET.get('sessionid'))
        if user is not None:
            if user.is_active:
                request.session['sessionid'] = request.GET.get('sessionid')
                login(request, user)
                if request.GET.get('next'):
                    return_url = use_query_next
                else:
                    return_url = default_next

    return redirect(return_url)

@login_and_uows_valid
def logout(request):
    session_id = request.session.get('sessionid')
    if session_id:
        UOWSClient().logout(session_id)
    django_logout(request)
    request.session.flush()
    return redirect('index')

@login_and_uows_valid
@render_with('run_queue.html')
@require_staff
def run_queue(request):
    complete_status = StatusUtils().get_completed()
    error_status = StatusUtils().get_error()
    pending_jobs = ReductionRun.objects.all().exclude(status=complete_status).exclude(status=error_status)
    context_dictionary = {
        'queue' : pending_jobs
    }
    return context_dictionary

@login_and_uows_valid
@render_with('run_list.html')
def run_list(request):
    context_dictionary = {}
    instruments = []
    # TODO: Uncomment on release: with ICATCommunication(AUTH='uows',SESSION={'sessionid':request.session.get('sessionid')}) as icat:
    with ICATCommunication() as icat:
        instrument_names = icat.get_valid_instruments(int(request.user.username))
        experiments = icat.get_valid_experiments_for_instruments(int(request.user.username), instrument_names)
        owned_instruments = icat.get_owned_instruments(int(request.user.username))
    for instrument in instrument_names:
        instrument_queued_runs = 0
        instrument_processing_runs = 0
        instrument_error_runs = 0

        instrument_obj = {
            'name' : instrument,
            'experiments' : [],
            'is_instrument_scientist' : (instrument in owned_instruments),
            'runs' : []
        }
        
        instrument_experiments = experiments[instrument]
        reference_numbers = []
        for experiment in instrument_experiments:
            # Filter out calibration runs
            if experiment.isdigit():
                reference_numbers.append(experiment)

        matching_experiments = Experiment.objects.filter(reference_number__in=reference_numbers)
        for experiment in matching_experiments:
            experiment_queued_runs = 0
            experiment_processing_runs = 0
            experiment_error_runs = 0

            runs = ReductionRun.objects.filter(experiment=experiment).order_by('-created')
            for run in runs:
                if run.status == StatusUtils().get_error():
                    experiment_error_runs += 1
                if run.status == StatusUtils().get_queued():
                    experiment_queued_runs += 1
                if run.status == StatusUtils().get_processing():
                    experiment_processing_runs += 1

            # Add exepriment stats to instrument
            instrument_queued_runs += experiment_queued_runs
            instrument_processing_runs += experiment_processing_runs
            instrument_error_runs += experiment_error_runs

            experiment_obj = {
                'reference_number' : experiment.reference_number,
                'runs' : runs,
                'progress_summary' : {
                    'processing' : experiment_processing_runs,
                    'queued' : experiment_queued_runs,
                    'error' : experiment_error_runs,
                }
            }
            # Add all runs to instrument object as well to be used by the "view by run number" layout
            instrument_obj['runs'].extend(runs)
            instrument_obj['experiments'].append(experiment_obj)

        instrument_obj['progress_summary']= {
            'processing' : instrument_processing_runs,
            'queued' : instrument_queued_runs,
            'error' : instrument_error_runs,
        }

        # Sort lists before appending
        instrument_obj['runs'] = sorted(instrument_obj['runs'], key=operator.attrgetter('created'), reverse=True)
        instrument_obj['experiments'] = sorted(instrument_obj['experiments'], key=lambda k: k['reference_number'], reverse=True)
        instruments.append(instrument_obj)
    
    # TODO: generate notification if there are any error runs
    context_dictionary['instrument_list'] = instruments
    # TODO: generate object to tell the template what to display by default (such as which tab and instruments to expand)

    return context_dictionary

@login_and_uows_valid
@render_with('run_summary.html')
def run_summary(request, run_number, run_version=0):
    try:
        run = ReductionRun.objects.get(run_number=run_number, run_version=run_version)
        history = ReductionRun.objects.filter(run_number=run_number).order_by('-run_version')
        context_dictionary = {
            'run' : run,
            'history' : history,
        }
    except:
        context_dictionary = {}
    return context_dictionary

@login_and_uows_valid
@render_with('instrument_summary.html')
@require_staff
def instrument_summary(request, instrument):
    processing_status = StatusUtils().get_processing()
    queued_status = StatusUtils().get_queued()
    try:
        instrument_obj = Instrument.objects.get(name=instrument)
        context_dictionary = {
            'instrument' : instrument_obj,
            'processing' : ReductionRun.objects.filter(instrument=instrument_obj, status=processing_status),
            'queued' : ReductionRun.objects.filter(instrument=instrument_obj, status=queued_status),
        }
    except:
        context_dictionary = {}
    return context_dictionary

@login_and_uows_valid
@render_with('experiment_summary.html')
def experiment_summary(request, reference_number):
    try:
        experiment = Experiment.objects.get(reference_number=reference_number)
        runs = ReductionRun.objects.filter(experiment=experiment).order_by('-run_version')
        with ICATCommunication(SESSION={'sessionid':request.session['sessionid']}) as icat:
            experiment_details = icat.get_experiment_details(int(reference_number))

        context_dictionary = {
            'experiment' : experiment,
            'runs' : runs,
            'experiment_details' : experiment_details,
        }
    except:
        context_dictionary = {}
    return context_dictionary
