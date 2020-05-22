# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
The view for the django database model

This file contains a large amount of pylint disables as there are no
working unit tests for this code at the point of correcting the pylint errors
as such we shoud remove the pylint disables and fix the code when we
can be more confident we are not affecting the execution
"""
import json
import logging
import operator

from django.contrib.auth import logout as django_logout, authenticate, login
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.db.models import Q
from django.http import JsonResponse, HttpResponseNotFound
from django.shortcuts import redirect

from autoreduce_webapp.icat_cache import ICATCache
from autoreduce_webapp.settings import (UOWS_LOGIN_URL, PRELOAD_RUNS_UNDER,
                                        USER_ACCESS_CHECKS, DEVELOPMENT_MODE)
from autoreduce_webapp.uows_client import UOWSClient
from autoreduce_webapp.view_utils import (login_and_uows_valid, render_with,
                                          require_admin, check_permissions)
from reduction_variables.utils import MessagingUtils
from reduction_viewer.models import Experiment, ReductionRun, Instrument, Status
from reduction_viewer.utils import StatusUtils, ReductionRunUtils
from reduction_viewer.view_utils import deactivate_invalid_instruments

from plotting.plot_handler import PlotHandler

from utilities.pagination import CustomPaginator

LOGGER = logging.getLogger('app')


@deactivate_invalid_instruments
def index(request):
    """
    Render the index page
    """
    return_url = UOWS_LOGIN_URL + request.build_absolute_uri()
    if request.GET.get('next'):
        return_url = UOWS_LOGIN_URL + request.build_absolute_uri(request.GET.get('next'))

    use_query_next = request.build_absolute_uri(request.GET.get('next'))
    default_next = 'overview'

    authenticated = False

    if DEVELOPMENT_MODE:
        user = authenticate(username="super", password="super")
        login(request, user)
        authenticated = True
    else:
        authenticated = request.user.is_authenticated() and 'sessionid' in request.session \
                        and UOWSClient().check_session(request.session['sessionid'])

    if authenticated:
        if request.GET.get('next'):
            return_url = use_query_next
        else:
            return_url = default_next
    elif request.GET.get('sessionid'):
        request.session['sessionid'] = request.GET.get('sessionid')
        user = authenticate(token=request.GET.get('sessionid'))
        if user is not None:
            if user.is_active:
                login(request, user)
                if request.GET.get('next'):
                    return_url = use_query_next
                else:
                    return_url = default_next

    return redirect(return_url)


@login_and_uows_valid
def logout(request):
    """
    Render the logout page
    """
    session_id = request.session.get('sessionid')
    if session_id:
        UOWSClient().logout(session_id)
    django_logout(request)
    request.session.flush()
    return redirect('index')


@login_and_uows_valid
@render_with('overview.html')
# pylint:disable=no-member,unused-argument
def overview(request):
    """
    Render the overview landing page (redirect from /index)
    """
    instruments = Instrument.objects.order_by('name')
    context_dictionary = {}
    if instruments:
        context_dictionary = {'instrument_list': instruments}
    return context_dictionary


@login_and_uows_valid
@render_with('run_queue.html')
# pylint:disable=no-member
def run_queue(request):
    """
    Render status of queue
    """
    # Get all runs that should be shown
    queued_status = StatusUtils().get_queued()
    processing_status = StatusUtils().get_processing()
    pending_jobs = ReductionRun.objects.filter(Q(status=queued_status) |
                                               Q(status=processing_status)).order_by('created')
    # Filter those which the user shouldn't be able to see
    if USER_ACCESS_CHECKS and not request.user.is_superuser:
        with ICATCache(AUTH='uows', SESSION={'sessionid': request.session['sessionid']}) as icat:
            # pylint:disable=deprecated-lambda
            pending_jobs = filter(lambda job: job.experiment.reference_number in
                                  icat.get_associated_experiments(int(request.user.username)),
                                  pending_jobs)  # check RB numbers
            pending_jobs = filter(lambda job: job.instrument.name in
                                  icat.get_owned_instruments(int(request.user.username)),
                                  pending_jobs)  # check instrument
    # Initialise list to contain the names of user/team that started runs
    started_by = []
    # cycle through all the filtered runs and retrieve the name of the user/team that started the run
    for run in pending_jobs:
        started_by.append(started_by_id_to_name(run.started_by))
    # zip the run information with the user/team name to enable simultaneous iteration with django
    context_dictionary = {'queue': zip(pending_jobs, started_by)}
    return context_dictionary


@require_admin
@login_and_uows_valid
@render_with('fail_queue.html')
# pylint:disable=no-member,too-many-locals
def fail_queue(request):
    """
    Render status of failed queue
    """
    # render the page
    error_status = StatusUtils().get_error()
    failed_jobs = ReductionRun.objects.filter(Q(status=error_status) &
                                              Q(hidden_in_failviewer=False)).order_by('-created')
    context_dictionary = {'queue': failed_jobs,
                          'status_success': StatusUtils().get_completed(),
                          'status_failed': StatusUtils().get_error()
                         }

    if request.method == 'POST':
        # perform the specified action
        action = request.POST.get("action", "default")
        selected_run_string = request.POST.get("selectedRuns", [])
        selected_runs = json.loads(selected_run_string)
        try:
            for run in selected_runs:
                run_number = int(run[0])
                run_version = int(run[1])
                rb_number = int(run[2])

                experiment = Experiment.objects.filter(reference_number=rb_number).first()
                reduction_run = ReductionRun.objects.get(experiment=experiment,
                                                         run_number=run_number,
                                                         run_version=run_version)

                if action == "hide":
                    reduction_run.hidden_in_failviewer = True
                    reduction_run.save()

                elif action == "rerun":
                    highest_version = max([int(runL[1]) for runL in
                                           selected_runs if int(runL[0]) == run_number])
                    if run_version != highest_version:
                        continue  # do not run multiples of the same run

                    ReductionRunUtils().cancelRun(reduction_run)
                    reduction_run.cancel = False
                    new_job = ReductionRunUtils().createRetryRun(user_id=request.user.id,
                                                                 reduction_run=reduction_run)

                    try:
                        MessagingUtils().send_pending(new_job)
                    # pylint:disable=broad-except
                    except Exception as exception:
                        new_job.delete()
                        raise exception

                elif action == "cancel":
                    ReductionRunUtils().cancelRun(reduction_run)

                elif action == "default":
                    pass

        # pylint:disable=broad-except
        except Exception as exception:
            fail_str = "Selected action failed: %s %s" % (type(exception).__name__,
                                                          exception)
            LOGGER.info("Failed to carry out fail_queue action - %s", fail_str)
            context_dictionary["message"] = fail_str

    return context_dictionary


@login_and_uows_valid
@render_with('run_list.html')
# pylint:disable=no-member,too-many-locals,too-many-branches,too-many-statements
def run_list(request):
    """
    Render list of runs
    """
    context_dictionary = {}
    instruments = []
    owned_instruments = []
    experiments = {}

    # Superuser sees everything
    if request.user.is_superuser or not USER_ACCESS_CHECKS:
        instrument_names = Instrument.objects.order_by('name', 'name')
        is_instrument_scientist = True
        if instrument_names:
            for instrument_name in instrument_names:
                experiments[instrument_name] = []
                instrument = Instrument.objects.get(name=instrument_name)
                instrument_experiments = Experiment.objects.\
                    filter(reduction_runs__instrument=instrument).\
                    values_list('reference_number', flat=True)
                for experiment in instrument_experiments:
                    experiments[instrument_name].append(str(experiment))
    else:
        with ICATCache(AUTH='uows',
                       SESSION={'sessionid': request.session.get('sessionid')}) as icat:
            instrument_names = icat.get_valid_instruments(int(request.user.username))
            if instrument_names:
                experiments = icat.\
                    get_valid_experiments_for_instruments(int(request.user.username),
                                                          instrument_names)
            owned_instruments = icat.get_owned_instruments(int(request.user.username))
            is_instrument_scientist = owned_instruments if owned_instruments else True

    # get database status labels up front to reduce queries to database
    status_error = StatusUtils().get_error()
    status_queued = StatusUtils().get_queued()
    status_processing = StatusUtils().get_processing()

    # Keep count of the total number of runs, to preload if there aren't too many.
    total_runs = 0

    for instrument_name in instrument_names:
        try:
            instrument = Instrument.objects.get(name=instrument_name)
        # pylint:disable=bare-except
        except:
            continue
        instrument_queued_runs = 0
        instrument_processing_runs = 0
        instrument_error_runs = 0

        instrument_obj = {
            'name': instrument_name,
            'experiments': [],
            'is_instrument_scientist': is_instrument_scientist,
            'is_active': instrument.is_active,
            'is_paused': instrument.is_paused
        }

        if instrument_name in owned_instruments:
            matching_experiments = list(set(Experiment.objects.
                                            filter(reduction_runs__instrument=instrument)))
        else:
            exp_refs = experiments[instrument_name] if instrument_name in experiments else []
            matching_experiments = Experiment.objects.filter(reference_number__in=exp_refs)

        for experiment in matching_experiments:
            runs = ReductionRun.objects.filter(experiment=experiment,
                                               instrument=instrument).order_by('-created')
            total_runs += runs.count()

            # count how many runs are in status error, queued and processing
            experiment_error_runs = runs.filter(status__exact=status_error).count()
            experiment_queued_runs = runs.filter(status__exact=status_queued).count()
            experiment_processing_runs = runs.filter(status__exact=status_processing).count()

            # Add experiment stats to instrument
            instrument_queued_runs += experiment_queued_runs
            instrument_processing_runs += experiment_processing_runs
            instrument_error_runs += experiment_error_runs

            experiment_obj = {
                'reference_number': experiment.reference_number,
                'progress_summary': {
                    'processing': experiment_processing_runs,
                    'queued': experiment_queued_runs,
                    'error': experiment_error_runs,
                }
            }
            instrument_obj['experiments'].append(experiment_obj)

        instrument_obj['progress_summary'] = {
            'processing': instrument_processing_runs,
            'queued': instrument_queued_runs,
            'error': instrument_error_runs,
        }

        # Sort lists before appending
        instrument_obj['experiments'] = sorted(instrument_obj['experiments'],
                                               key=lambda k: k['reference_number'],
                                               reverse=True)
        instruments.append(instrument_obj)

    context_dictionary['instrument_list'] = instruments
    context_dictionary['preload_runs'] = (total_runs < PRELOAD_RUNS_UNDER)
    if is_instrument_scientist:
        context_dictionary['default_tab'] = 'run_number'
    else:
        context_dictionary['default_tab'] = 'experiment'

    return context_dictionary


@login_and_uows_valid
@check_permissions
@render_with('load_runs.html')
# pylint:disable=no-member,unused-argument
def load_runs(request, reference_number=None, instrument_name=None):
    """
    Render load runs
    """
    runs = []

    if reference_number:
        experiments = Experiment.objects.filter(reference_number=reference_number)
        if experiments:
            experiment = experiments[0]
            runs = ReductionRun.objects.filter(experiment=experiment).order_by('-created')

    elif instrument_name:
        instrument = Instrument.objects.filter(name=instrument_name)

        if instrument.exists():
            runs = (ReductionRun.objects.
                    # Get the foreign key 'status' now.
                    # Otherwise many queries made from load_runs which is very slow.
                    select_related('status')
                    # Only get these attributes, to speed it up.
                    .only('status', 'last_updated', 'run_number', 'run_name', 'run_version')
                    .filter(instrument=instrument.first())
                    .order_by('-created'))

    context_dictionary = {"runs": runs}
    return context_dictionary


@login_and_uows_valid
@check_permissions
@render_with('run_summary.html')
# pylint:disable=no-member,unused-argument
def run_summary(request, instrument_name=None, run_number=None, run_version=0):
    """
    Render run summary
    """
    # pylint:disable=broad-except
    try:
        instrument = Instrument.objects.get(name=instrument_name)
        run = ReductionRun.objects.get(instrument=instrument,
                                       run_number=run_number,
                                       run_version=run_version)
        history = ReductionRun.objects.filter(run_number=run_number).order_by('-run_version')
        started_by = started_by_id_to_name(run.started_by)

        location_list = run.reduction_location.all()
        reduction_location = None
        if location_list:
            reduction_location = location_list[0].file_path
        if reduction_location and '\\' in reduction_location:
            reduction_location = reduction_location.replace('\\', '/')

        rb_number=Experiment.objects.get(id=run.experiment_id).reference_number
        #plot_location=PlotHandler.get_plot_file(instrument_name=run.instrument,rb_number=rb_number, run_number=run.run_number)

        context_dictionary = {'run': run,
                              'history': history,
                              'reduction_location': reduction_location,
                              'started_by': started_by}
                              #'plot_location':plot_location}
    except PermissionDenied:
        raise
    except Exception as exception:
        LOGGER.error(exception)
        context_dictionary = {}

    return context_dictionary


def started_by_id_to_name(started_by_id=None):
    """
    Returns name of the user or team that submitted an autoreduction run given an ID number
    :param started_by_id: The ID of the user who started the run, or a control code if not started by a user
    :return:
        If started by a valid user, returns the name either of the user in the format '[forename] [surname]'.
        If started automatically, returns "Autoreduciton service".
        If started manually, returns "Development team".
        Otherwise, returns None.
    """
    name = None
    if started_by_id is not None:
        if started_by_id == -1:
            name = "Development team"
        elif started_by_id == 0:
            name = "Autoreduction service"
        elif started_by_id > 0:
            try:
                user_record = User.objects.get(id=started_by_id)
                name = f"{user_record.first_name} {user_record.last_name}"
            except ObjectDoesNotExist as exception:
                LOGGER.error(exception)
                name = None
        elif started_by_id < -1:
            name = None
    return name


@login_and_uows_valid
@check_permissions
@render_with('instrument_summary.html')
# pylint:disable=no-member,unused-argument
def instrument_summary(request, instrument=None):
    """
    Render instrument summary
    """
    try:
        filter_by = request.GET.get('filter', 'run')
        instrument_obj = Instrument.objects.get(name=instrument)
        sort_by = request.GET.get('sort', 'run')
        if sort_by == 'run':
            runs = (ReductionRun.objects
                    .only('status', 'last_updated', 'run_number', 'run_version')
                    .select_related('status')
                    .filter(instrument=instrument_obj)
                    .order_by('-run_number', 'run_version'))
        else:
            runs = (ReductionRun.objects
                    .only('status', 'last_updated', 'run_number', 'run_version')
                    .select_related('status')
                    .filter(instrument=instrument_obj)
                    .order_by('-last_updated'))
        context_dictionary = {
            'instrument': instrument_obj,
            'instrument_name': instrument_obj.name,
            'runs': runs,
            'last_instrument_run': runs[0],
            'processing': runs.filter(status=StatusUtils().get_processing()),
            'queued': runs.filter(status=StatusUtils().get_queued()),
            'filtering': filter_by,
            'sort': sort_by
        }

        if filter_by == 'experiment':
            experiments_and_runs = {}
            experiments = Experiment.objects.filter(reduction_runs__instrument=instrument_obj). \
                order_by('-reference_number').distinct()
            for experiment in experiments:
                associated_runs = runs.filter(experiment=experiment). \
                    order_by('-created')
                experiments_and_runs[experiment] = associated_runs
            context_dictionary['experiments'] = experiments_and_runs
        else:
            max_items_per_page = request.GET.get('pagination', 10)
            custom_paginator = CustomPaginator(page_type=sort_by,
                                               query_set=runs,
                                               items_per_page=max_items_per_page,
                                               page_tolerance=3,
                                               current_page=request.GET.get('page', 1))
            context_dictionary['paginator'] = custom_paginator
            context_dictionary['last_page_index'] = len(custom_paginator.page_list)
            context_dictionary['max_items'] = max_items_per_page

    # pylint:disable=broad-except
    except Exception as exception:
        LOGGER.error(exception)
        context_dictionary = {}

    return context_dictionary


@login_and_uows_valid
@check_permissions
@render_with('experiment_summary.html')
# pylint:disable=no-member
def experiment_summary(request, reference_number=None):
    """
    Render experiment summary
    """
    try:
        experiment = Experiment.objects.get(reference_number=reference_number)
        runs = ReductionRun.objects.filter(experiment=experiment).order_by('-run_version')
        data = []
        reduced_data = []
        started_by = []
        for run in runs:
            for location in run.data_location.all():
                if location not in data:
                    data.append(location)
            for location in run.reduction_location.all():
                if location not in reduced_data:
                    reduced_data.append(location)
            started_by.append(started_by_id_to_name(run.started_by))
        sorted_runs = sorted(runs, key=operator.attrgetter('last_updated'), reverse=True)
        runs_with_started_by = zip(sorted_runs, started_by)

        try:
            if DEVELOPMENT_MODE:
                # If we are in development mode use user/password for ICAT from django settings
                # e.g. do not attempt to use same authentication as the user office
                with ICATCache() as icat:
                    experiment_details = icat.get_experiment_details(int(reference_number))
            else:
                with ICATCache(AUTH='uows',
                               SESSION={'sessionid': request.session['sessionid']}) as icat:
                    experiment_details = icat.get_experiment_details(int(reference_number))
        # pylint:disable=broad-except
        except Exception as icat_e:
            LOGGER.error(icat_e)
            experiment_details = {
                'reference_number': '',
                'start_date': '',
                'end_date': '',
                'title': '',
                'summary': '',
                'instrument': '',
                'pi': '',
            }
        context_dictionary = {
            'experiment': experiment,
            'runs_with_started_by': runs_with_started_by,
            'run_count': len(runs),
            'experiment_details': experiment_details,
            'data': data,
            'reduced_data': reduced_data,
        }
    # pylint:disable=broad-except
    except Exception as exception:
        LOGGER.error(exception)
        context_dictionary = {}

    return context_dictionary


@render_with('help.html')
# pylint:disable=redefined-builtin,unused-argument
def help(request):
    """
    Render help page
    """
    return {}


@login_and_uows_valid
@check_permissions
# pylint:disable=no-member
def instrument_pause(request, instrument=None):
    """
    Renders pausing of instrument returning a JSON response
    """
    # ToDo: Check ICAT credentials
    instrument_obj = Instrument.objects.get(name=instrument)
    currently_paused = (request.POST.get("currently_paused").lower() == u"false")
    instrument_obj.is_paused = currently_paused
    instrument_obj.save()
    return JsonResponse({'currently_paused': str(currently_paused)})  # Blank response


@render_with('admin/graph_home.html')
# pylint:disable=no-member,unused-argument
def graph_home(request):
    """
    Render graph page
    """
    instruments = Instrument.objects.all()

    context_dictionary = {
        'instruments': instruments
    }

    return context_dictionary


@require_admin
@render_with('admin/graph_instrument.html')
# pylint:disable=no-member
def graph_instrument(request, instrument_name):
    """
    Render instrument speciifc graphing page
    """
    instrument = Instrument.objects.filter(name=instrument_name)
    if not instrument:
        return HttpResponseNotFound('<h1>Instrument not found</h1>')
    runs = (ReductionRun.objects.
            # Get the foreign key 'status' now. Otherwise many queries
            # made from load_runs which is very slow.
            select_related('status')
            # Only get these attributes, to speed it up.
            .only('status', 'started', 'finished', 'last_updated',
                  'created', 'run_number', 'run_name', 'run_version')
            .filter(instrument=instrument.first())
            .order_by('-created'))

    try:
        if 'last' in request.GET:
            runs = runs[:int(request.GET.get('last'))]
    except ValueError:
        # Non integer value entered as 'last' parameter.
        # Just show all runs.
        pass

    # Reverse list so graph displayed in correct order
    runs = runs[::-1]

    for run in runs:
        if run.started and run.finished:
            run.run_time = (run.finished - run.started).total_seconds()
        else:
            run.run_time = 0
    context_dictionary = {
        'runs': runs,
        'instrument': instrument.first().name
    }
    return context_dictionary


@require_admin
@render_with('admin/stats.html')
# pylint:disable=no-member,unused-argument
def stats(request):
    """
    Render run statistics page
    """
    statuses = []
    for status in Status.objects.all():
        status_count = (ReductionRun.objects.
                        # Get the foreign key 'status' now.
                        # Otherwise many queries made from load_runs which is very slow.
                        select_related('status')
                        # Only get these attributes, to speed it up.
                        .only('status')
                        .filter(status__value=status.value).count())
        statuses.append({'name': status, 'count': status_count})

    context_dictionary = {
        'statuses': statuses,
    }

    return context_dictionary
