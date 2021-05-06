# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
The view for the django database model

This file contains a large amount of pylint disables as there are no
working unit tests for this code at the point of correcting the pylint errors
as such we should remove the pylint disables and fix the code when we
can be more confident we are not affecting the execution
"""
# pylint:disable=imported-auth-user
import json
import logging
import operator
import traceback

from autoreduce_webapp.icat_cache import ICATCache
from autoreduce_webapp.settings import (ALLOWED_HOSTS, DEVELOPMENT_MODE, UOWS_LOGIN_URL, USER_ACCESS_CHECKS)
from autoreduce_webapp.uows_client import UOWSClient
from autoreduce_webapp.view_utils import (check_permissions, login_and_uows_valid, render_with, require_admin)
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from reduction_viewer.models import (Experiment, Instrument, ReductionRun, Status)
from reduction_viewer.utils import ReductionRunUtils
from reduction_viewer.view_utils import deactivate_invalid_instruments, get_interactive_plot_data
from utilities.pagination import CustomPaginator

from plotting.plot_handler import PlotHandler
from queue_processors.queue_processor.status_utils import STATUS
from queue_processors.queue_processor.variable_utils import VariableUtils

LOGGER = logging.getLogger('app')


@deactivate_invalid_instruments
def index(request):
    """
    Render the index page
    """
    return_url = _make_return_url(request, request.GET.get('next'))

    use_query_next = request.build_absolute_uri(request.GET.get('next'))
    default_next = 'overview'

    authenticated = False

    if DEVELOPMENT_MODE:
        user = authenticate(username="super", password="super", backend="django.contrib.auth.backends.ModelBackend")
        login(request, user)
        authenticated = True
    else:
        if 'sessionid' in request.session.keys():
            authenticated = request.user.is_authenticated \
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


def _make_return_url(request, next_url):
    """
    Make the return URL based on whether a next_url is present in the url.

    If there is a next_url, verify that the url is safe and allowed before using it. If not, default to the host.
    """
    if next_url:
        if url_has_allowed_host_and_scheme(next_url, ALLOWED_HOSTS, require_https=True):
            return UOWS_LOGIN_URL + request.build_absolute_uri(next_url)
        else:
            # the next_url was not safe so don't use it - build from request.path to ignore GET parameters
            return UOWS_LOGIN_URL + request.build_absolute_uri(request.path)
    else:
        return UOWS_LOGIN_URL + request.build_absolute_uri()


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
    return redirect('overview')


@login_and_uows_valid
@render_with('overview.html')
# pylint:disable=no-member
def overview(_):
    """
    Render the overview landing page (redirect from /index)
    Note: _ is replacing the passed in request parameter
    """
    context_dictionary = {}
    instruments = Instrument.objects.values_list("name", flat=True)
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
    queued_status = STATUS.get_queued()
    processing_status = STATUS.get_processing()
    pending_jobs = ReductionRun.objects.filter(Q(status=queued_status)
                                               | Q(status=processing_status)).order_by('created')
    # Filter those which the user shouldn't be able to see
    if USER_ACCESS_CHECKS and not request.user.is_superuser:
        with ICATCache(AUTH='uows', SESSION={'sessionid': request.session['sessionid']}) as icat:
            pending_jobs = filter(lambda job: job.experiment.reference_number in icat.get_associated_experiments(
                int(request.user.username)), pending_jobs)  # check RB numbers
            pending_jobs = filter(
                lambda job: job.instrument.name in icat.get_owned_instruments(int(request.user.username)),
                pending_jobs)  # check instrument
    # Initialise list to contain the names of user/team that started runs
    started_by = []
    # cycle through all filtered runs and retrieve the name of the user/team that started the run
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
    error_status = STATUS.get_error()
    failed_jobs = ReductionRun.objects.filter(Q(status=error_status)
                                              & Q(hidden_in_failviewer=False)).order_by('-created')
    context_dictionary = {
        'queue': failed_jobs,
        'status_success': STATUS.get_completed(),
        'status_failed': STATUS.get_error()
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

                reduction_run = failed_jobs.get(run_number=run_number, run_version=run_version)

                if action == "hide":
                    reduction_run.hidden_in_failviewer = True
                    reduction_run.save()

                elif action == "rerun":
                    highest_version = max([int(runL[1]) for runL in selected_runs if int(runL[0]) == run_number])
                    if run_version != highest_version:
                        continue  # do not run multiples of the same run

                    ReductionRunUtils.send_retry_message_same_args(request.user.id, reduction_run)

                elif action == "default":
                    pass

        # pylint:disable=broad-except
        except Exception as exception:
            fail_str = "Selected action failed: %s %s" % (type(exception).__name__, exception)
            LOGGER.info("Failed to carry out fail_queue action - %s", fail_str)
            context_dictionary["message"] = fail_str

    return context_dictionary


@login_and_uows_valid
@check_permissions
@render_with('run_summary.html')
# pylint:disable=no-member,too-many-locals
def run_summary(_, instrument_name=None, run_number=None, run_version=0):
    """
    Render run summary
    """
    # pylint:disable=broad-except
    try:
        history = ReductionRun.objects.filter(instrument__name=instrument_name, run_number=run_number).order_by(
            '-run_version').select_related('status').select_related('experiment').select_related('instrument')
        if len(history) == 0:
            raise ValueError(f"Could not find any matching runs for instrument {instrument_name} run {run_number}")

        run = next(run for run in history if run.run_version == int(run_version))
        started_by = started_by_id_to_name(run.started_by)
        # run status value of "s" means the run is skipped
        is_skipped = run.status.value == "s"
        is_rerun = len(history) > 1

        location_list = run.reduction_location.all()
        reduction_location = None
        if location_list:
            reduction_location = location_list[0].file_path
        if reduction_location and '\\' in reduction_location:
            reduction_location = reduction_location.replace('\\', '/')

        rb_number = run.experiment.reference_number
        try:
            current_variables = VariableUtils.get_default_variables(run.instrument.name)
        except (FileNotFoundError, ImportError, SyntaxError):
            current_variables = {}

        has_reduce_vars = bool(current_variables)
        has_run_variables = bool(run.run_variables.count())
        context_dictionary = {
            'run': run,
            'run_number': run_number,
            'instrument': instrument_name,
            'run_version': run_version,
            'is_skipped': is_skipped,
            'is_rerun': is_rerun,
            'history': history,
            'reduction_location': reduction_location,
            'started_by': started_by,
            'has_reduce_vars': has_reduce_vars,
            'has_run_variables': has_run_variables
        }

    except PermissionDenied:
        raise
    except Exception as exception:
        # Error that we cannot recover from - something wrong with instrument, run, or experiment
        LOGGER.error(exception)
        return {"message": str(exception)}

    if reduction_location:
        try:
            plot_handler = PlotHandler(data_filepath=run.data_location.first().file_path,
                                       server_dir=reduction_location,
                                       rb_number=rb_number)
            local_plot_locs, server_plot_locs = plot_handler.get_plot_file()
            if local_plot_locs:
                context_dictionary['static_plots'] = [
                    location for location in local_plot_locs if not location.endswith(".json")
                ]

                context_dictionary['interactive_plots'] = get_interactive_plot_data(server_plot_locs)
        except Exception as exception:
            # Lack of plot images is recoverable - we shouldn't stop the whole page rendering
            # if something is wrong with the plot images - but display an error message
            err_msg = "Encountered error while retrieving plots for this run"
            LOGGER.error("%s. Instrument: %s, run %s. RB Number %s Error: %s", err_msg, run.instrument.name, run,
                         rb_number, exception)
            context_dictionary["plot_error_message"] = f"{err_msg}."

    return context_dictionary


@login_and_uows_valid
@check_permissions
@render_with('runs_list.html')
# pylint:disable=no-member,unused-argument,too-many-locals
def runs_list(request, instrument=None):
    """
    Render instrument summary
    """
    try:
        filter_by = request.GET.get('filter', 'run')
        instrument_obj = Instrument.objects.get(name=instrument)
    except Instrument.DoesNotExist:
        return {'message': "Instrument not found."}

    try:
        sort_by = request.GET.get('sort', 'run')
        if sort_by == 'run':
            runs = (ReductionRun.objects.only('status', 'last_updated', 'run_number', 'run_version',
                                              'run_description').select_related('status').filter(
                                                  instrument=instrument_obj).order_by('-run_number', 'run_version'))
        else:
            runs = (ReductionRun.objects.only(
                'status', 'last_updated', 'run_number', 'run_version',
                'run_description').select_related('status').filter(instrument=instrument_obj).order_by('-last_updated'))

        if len(runs) == 0:
            return {'message': "No runs found for instrument."}

        try:
            current_variables = VariableUtils.get_default_variables(instrument_obj.name)
            error_reason = ""
        except FileNotFoundError:
            current_variables = {}
            error_reason = "reduce_vars.py is missing for this instrument"
        except (ImportError, SyntaxError):
            current_variables = {}
            error_reason = "reduce_vars.py has an import or syntax error"

        has_variables = bool(current_variables)

        context_dictionary = {
            'instrument': instrument_obj,
            'instrument_name': instrument_obj.name,
            'runs': runs,
            'last_instrument_run': runs[0],
            'processing': runs.filter(status=STATUS.get_processing()),
            'queued': runs.filter(status=STATUS.get_queued()),
            'filtering': filter_by,
            'sort': sort_by,
            'has_variables': has_variables,
            'error_reason': error_reason
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
    except Exception:
        LOGGER.error(traceback.format_exc())
        return {'message': "An unexpected error has occurred when loading the instrument."}

    return context_dictionary


@login_and_uows_valid
@check_permissions
@render_with('experiment_summary.html')
# pylint:disable=no-member,too-many-locals
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
                with ICATCache(AUTH='uows', SESSION={'sessionid': request.session['sessionid']}) as icat:
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
# pylint:disable=redefined-builtin
def help(_):
    """
    Render help page
    Note: _ is replacing the passed in request parameter
    """
    return {}


@render_with('accessibility_statement.html')
# pylint:disable=redefined-builtin
def accessibility_statement(_):
    """
    Render accessibility statement page
    Note: _ is replacing the passed in request parameter
    """
    return {}


@render_with('admin/graph_home.html')
# pylint:disable=no-member
def graph_home(_):
    """
    Render graph page
    Note: _ is replacing the passed in request parameter
    """
    instruments = Instrument.objects.all()

    context_dictionary = {'instruments': instruments}

    return context_dictionary


@require_admin
@render_with('admin/graph_instrument.html')
# pylint:disable=no-member
def graph_instrument(request, instrument_name):
    """
    Render instrument specific graphing page
    """
    instrument = Instrument.objects.filter(name=instrument_name)
    if not instrument:
        return HttpResponseNotFound('<h1>Instrument not found</h1>')

    runs = (
        ReductionRun.objects.
        # Get the foreign key 'status' now. Otherwise many queries
        # made from load_runs which is very slow.
        select_related('status')
        # Only get these attributes, to speed it up.
        .only('status', 'started', 'finished', 'last_updated', 'created', 'run_number', 'run_description',
              'run_version').filter(instrument=instrument.first()).order_by('-created'))

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

    context_dictionary = {'runs': runs, 'instrument': instrument.first().name}

    return context_dictionary


@require_admin
@render_with('admin/stats.html')
# pylint:disable=no-member
def stats(_):
    """
    Render run statistics page
    Note: _ is replacing the passed in request parameter
    """
    statuses = []
    for status in Status.objects.all():
        status_count = (
            ReductionRun.objects.
            # Get the foreign key 'status' now.
            # Otherwise many queries made from load_runs which is very slow.
            select_related('status')
            # Only get these attributes, to speed it up.
            .only('status').filter(status__value=status.value).count())
        statuses.append({'name': status, 'count': status_count})

    context_dictionary = {
        'statuses': statuses,
    }

    return context_dictionary


def started_by_id_to_name(started_by_id=None):
    """
    Returns name of the user or team that submitted an autoreduction run given an ID number
    :param started_by_id: (int) The ID of the user who started the run, or a control code if not
     started by a user
    :return:
        If started by a valid user, returns the name either of the user in the format
         '[forename] [surname]'.
        If started automatically, returns "Autoreducton service".
        If started manually, returns "Development team".
        Otherwise, returns None.
    """
    if started_by_id is None or started_by_id < -1:
        return None

    if started_by_id == -1:
        return "Development team"

    if started_by_id == 0:
        return "Autoreduction service"

    try:
        user_record = User.objects.get(id=started_by_id)
        return f"{user_record.first_name} {user_record.last_name}"
    except ObjectDoesNotExist as exception:
        LOGGER.error(exception)
        return None
