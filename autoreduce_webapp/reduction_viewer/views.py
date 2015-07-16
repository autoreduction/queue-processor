from django.shortcuts import redirect
from django.contrib.auth import logout as django_logout, authenticate, login
from django.core.exceptions import PermissionDenied
from autoreduce_webapp.uows_client import UOWSClient
from autoreduce_webapp.icat_communication import ICATCommunication
from autoreduce_webapp.settings import UOWS_LOGIN_URL
from reduction_viewer.models import Experiment, ReductionRun, Instrument
from reduction_viewer.utils import StatusUtils
from reduction_viewer.view_utils import deactivate_invalid_instruments
from autoreduce_webapp.view_utils import login_and_uows_valid, render_with, require_staff
import operator
import logging
logger = logging.getLogger(__name__)

@deactivate_invalid_instruments
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
                # Cache these for the session as they are used for permission checking
                with ICATCommunication(AUTH='uows', SESSION={'sessionid':request.session['sessionid']}) as icat:
                    request.session['owned_instruments'] = icat.get_owned_instruments(int(request.user.username))
                    request.session['experiments'] = icat.get_associated_experiments(int(request.user.username))

    return redirect(return_url)

@login_and_uows_valid
def logout(request):
    session_id = request.session.get('sessionid')
    if session_id:
        UOWSClient().logout(session_id)
    django_logout(request)
    request.session.flush()
    return redirect('index')

@require_staff
@render_with('run_queue.html')
def run_queue(request):
    complete_status = StatusUtils().get_completed()
    error_status = StatusUtils().get_error()
    pending_jobs = ReductionRun.objects.all().exclude(status=complete_status).exclude(status=error_status).order_by('created')
    context_dictionary = {
        'queue' : pending_jobs
    }
    return context_dictionary

@login_and_uows_valid
@render_with('run_list.html')
def run_list(request):
    context_dictionary = {}
    instruments = []
    # Owned instruments is populated on login
    owned_instruments = request.session.get('owned_instruments', default=[])
    # Superuser sees everything
    if request.user.is_superuser:
        instrument_names = Instrument.objects.values_list('name', flat=True)
        if instrument_names:
            experiments = {}
            for instrument_name in instrument_names:
                experiments[instrument_name] = []
                instrument = Instrument.objects.get(name=instrument_name)
                instrument_experiments = Experiment.objects.filter(reduction_runs__instrument=instrument).values_list('reference_number', flat=True)
                for experiment in instrument_experiments:
                    experiments[instrument_name].append(str(experiment))
            request.session['experiments_to_show'] = experiments
    else:
        with ICATCommunication(AUTH='uows',SESSION={'sessionid':request.session.get('sessionid')}) as icat:
            instrument_names = icat.get_valid_instruments(int(request.user.username))
            if instrument_names:
                experiments = request.session.get('experiments_to_show', icat.get_valid_experiments_for_instruments(int(request.user.username), instrument_names))
                request.session['experiments_to_show'] = experiments

    # get database status labels up front to reduce queries to database
    status_error = StatusUtils().get_error()
    status_queued = StatusUtils().get_queued()
    status_processing = StatusUtils().get_processing()

    for instrument_name in instrument_names:
        try:
            instrument = Instrument.objects.get(name=instrument_name)
        except:
            continue
        instrument_queued_runs = 0
        instrument_processing_runs = 0
        instrument_error_runs = 0

        instrument_obj = {
            'name' : instrument_name,
            'experiments' : [],
            'is_instrument_scientist' : (instrument_name in owned_instruments),
            'runs' : [],
            'is_active' : instrument.is_active
        }
        
        if instrument_name not in experiments:
            experiments[instrument_name] = []
            
        instrument_experiments = experiments[instrument_name] 
        reference_numbers = []

        for experiment in instrument_experiments:
            # Filter out calibration runs
            if experiment.isdigit():
                reference_numbers.append(experiment)

        matching_experiments = Experiment.objects.filter(reference_number__in=reference_numbers)
        for experiment in matching_experiments:
            # get all runs for experiment
            runs = ReductionRun.objects.filter(experiment=experiment).order_by('-created')

            # count how many are in status error, queued and processing
            experiment_error_runs = runs.filter(status__exact=status_error).count()
            experiment_queued_runs = runs.filter(status__exact=status_queued).count()
            experiment_processing_runs = runs.filter(status__exact=status_processing).count()

            # Add experiment stats to instrument
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
        instrument_obj['runs'] = sorted(instrument_obj['runs'], key=operator.attrgetter('last_updated'), reverse=True)
        instrument_obj['experiments'] = sorted(instrument_obj['experiments'], key=lambda k: k['reference_number'], reverse=True)
        instruments.append(instrument_obj)

    context_dictionary['instrument_list'] = instruments
    if owned_instruments:
        context_dictionary['default_tab'] = 'run_number'
    else:
        context_dictionary['default_tab'] = 'experiment'

    return context_dictionary

@login_and_uows_valid
@render_with('run_summary.html')
def run_summary(request, run_number, run_version=0):
    try:
        run = ReductionRun.objects.get(run_number=run_number, run_version=run_version)
        # Check the user has permission
        if not request.user.is_superuser and run.experiment.reference_number not in request.session['experiments'] and run.instrument.name not in request.session['owned_instruments']:
            raise PermissionDenied()
        history = ReductionRun.objects.filter(run_number=run_number).order_by('-run_version')
        context_dictionary = {
            'run' : run,
            'history' : history,
        }
    except Exception as e:
        logger.error(e.message)
        context_dictionary = {}
    return context_dictionary

@require_staff
@render_with('instrument_summary.html')
def instrument_summary(request, instrument):
    # Check the user has permission
    if not request.user.is_superuser and instrument not in request.session['owned_instruments']:
        raise PermissionDenied()

    processing_status = StatusUtils().get_processing()
    queued_status = StatusUtils().get_queued()
    try:
        instrument_obj = Instrument.objects.get(name=instrument)
        context_dictionary = {
            'instrument' : instrument_obj,
            'last_instrument_run' : ReductionRun.objects.filter(instrument=instrument_obj).order_by('-run_number')[0],
            'processing' : ReductionRun.objects.filter(instrument=instrument_obj, status=processing_status),
            'queued' : ReductionRun.objects.filter(instrument=instrument_obj, status=queued_status),
        }
    except Exception as e:
        logger.error(e.message)
        context_dictionary = {}

    return context_dictionary

@login_and_uows_valid
@render_with('experiment_summary.html')
def experiment_summary(request, reference_number):
    try:
        experiment = Experiment.objects.get(reference_number=reference_number)
        runs = ReductionRun.objects.filter(experiment=experiment).order_by('-run_version')
        data = []
        reduced_data = []
        for run in runs:
            for location in run.data_location.all():
                if location not in data:
                    data.append(location)
            for location in run.reduction_location.all():
                if location not in reduced_data:
                    reduced_data.append(location)
        try:
            with ICATCommunication(AUTH='uows', SESSION={'sessionid':request.session['sessionid']}) as icat:
                experiment_details = icat.get_experiment_details(int(reference_number))
        except Exception as icat_e:
            logger.error(icat_e.message)
            experiment_details = {
                'reference_number' : '',
                'start_date' : '',
                'end_date' : '',
                'title' : '',
                'summary' : '',
                'instrument' : '',
                'pi' : '',
            }
        context_dictionary = {
            'experiment' : experiment,
            'runs' :  sorted(runs, key=operator.attrgetter('last_updated'), reverse=True),
            'experiment_details' : experiment_details,
            'data' : data,
            'reduced_data' : reduced_data,
        }
    except Exception as e:
        logger.error(e.message)
        context_dictionary = {}
    
    #Check the users permissions
    if not request.user.is_superuser and reference_number not in request.session['experiments'] and experiment_details['instrument'] not in request.session['owned_instruments']:
       raise PermissionDenied()
    return context_dictionary

@render_with('help.html')
def help(request):
    return {}
