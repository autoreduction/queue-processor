from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import logout as django_logout, authenticate, login
from django.contrib.auth.decorators import login_required
from autoreduce_webapp.uows_client import UOWSClient
from autoreduce_webapp.icat_communication import ICATCommunication
from autoreduce_webapp.settings import UOWS_LOGIN_URL
from reduction_viewer.models import Experiment, ReductionRun
from reduction_viewer.utils import StatusUtils
from autoreduce_webapp.view_utils import login_and_uows_valid, render_with
from django.http import HttpResponse

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
    with ICATCommunication() as icat:
        instrument_names = icat.get_valid_instruments(int(request.user.username))
        experiments = icat.get_valid_experiments_for_instruments(int(request.user.username), instrument_names)
    for instrument in instrument_names:
        instrument_obj = {
            'name' : instrument,
            'experiments' : []
        }
        instrument_experiments = experiments[instrument]
        reference_numbers = []
        for experiment in instrument_experiments:
            if experiment.isdigit():
                reference_numbers.append(experiment)
        instrument_obj['experiments'] = Experiment.objects.filter(reference_number__in=reference_numbers)
        instruments.append(instrument_obj)
    
    context_dictionary['instrument_list'] = instruments

    return context_dictionary

@login_and_uows_valid
@render_with('base.html')
def run_summary(request, run_number, run_version=0):
    context_dictionary = {}
    return context_dictionary

@login_and_uows_valid
@render_with('base.html')
def instrument_summary(request, instrument):
    context_dictionary = {}
    return context_dictionary

@login_and_uows_valid
@render_with('base.html')
def experiment_summary(request, reference_number):
    context_dictionary = {}
    return context_dictionary
