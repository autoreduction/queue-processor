from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from autoreduce_webapp.uows_client import UOWSClient
from autoreduce_webapp.settings import UOWS_LOGIN_URL, LOGIN_URL, INSTALLED_APPS, USER_ACCESS_CHECKS, OUTDATED_BROWSERS
from autoreduce_webapp.icat_cache import ICATCache
from reduction_viewer.models import ReductionRun, Experiment
from django.template import RequestContext
from django.shortcuts import render
from reduction_viewer.models import Notification, Setting
from settings import DEVELOPMENT_MODE
import logging
logger = logging.getLogger(__name__)

def has_valid_login(request):
    """
    Check that the user is correctly logged in and their session is still considered valid
    """
    logger.debug("Checking if user is authenticated")
    if DEVELOPMENT_MODE:
        logger.debug("DEVELOPMENT_MODE True so allowing access")
        return True
    if request.user.is_authenticated() and 'sessionid' in request.session:
        logger.debug("User is authenticated and has a sessionid from the UOWS")
        return True
    return False

def handle_redirect(request):
    """
    Redirect the user to either capture the session id or to go and log in
    """
    if request.GET.get('sessionid'):
        return redirect(request.build_absolute_uri(LOGIN_URL) + "?next=" + request.build_absolute_uri().replace('?sessionid=', '&sessionid=')) 
    return redirect(UOWS_LOGIN_URL + request.build_absolute_uri())

def login_and_uows_valid(fn):
    """
    Function decorator to check whether the user's session is still valid
    """
    def request_processor(request, *args, **kws):
        if has_valid_login(request):
            return fn(request, *args, **kws)
        return handle_redirect(request)
    return request_processor

def require_staff(fn):
    """
    Function decorator to check whether the user is a staff memeber
    """
    def request_processor(request, *args, **kws):
        if has_valid_login(request):
            if request.user.is_staff:
                return fn(request, *args, **kws)
            else:
                raise PermissionDenied()
        else:
            return handle_redirect(request)
    return request_processor

def require_admin(fn):
    """
    Function decorator to check whether the user is a superuser
    """
    def request_processor(request, *args, **kws):
        if has_valid_login(request):
            if request.user.is_superuser:
                return fn(request, *args, **kws)
            else:
                raise PermissionDenied()
        else:
            return handle_redirect(request)
    return request_processor

def render_with(template):
    """
    Decorator for Django views that sends returned dict to render function
    with given template and RequestContext as context instance.
    """
    def renderer(fn):
        def populate_template_dict(request, output):
            if 'request' not in output:
                output['request'] = request
            
            notifications = Notification.objects.filter(is_active=True, is_staff_only=(request.user.is_authenticated() and request.user.is_staff))
            if 'notifications' not in output:
                output['notifications'] = notifications
            else:
                output['notifications'].extend(notifications)

            if 'bad_browsers' not in output:
                # Load in the list of not accepted browsers from the settings
                bad_browsers = []
                for browser in OUTDATED_BROWSERS:
                    bad_browsers.append((browser, OUTDATED_BROWSERS[browser]))

                # Get the family and version from the user_agent
                family = request.user_agent.browser.family
                version = request.user_agent.browser.version_string

                # Make sure we are only comparing against a single integer
                if '.' in version:
                    version = int(version[0:(version.index('.'))])
                else:
                    version = int(version)

                # Check whether the browser is outdated
                outdated = False
                for browser in bad_browsers:
                    if browser[0] == family and version <= browser[1]:
                        outdated = True

                # Change to more user-friendly language
                if family == "IE":
                    family = "Microsoft Internet Explorer"

                output['bad_browsers'] = bad_browsers
                output['current_browser'] = family
                output['version'] = version
                output['outdated'] = outdated

            if 'reduction_variables_on' not in output:
                output['reduction_variables_on'] = ('reduction_variables' in INSTALLED_APPS)
            
            if 'support_email' not in output:
                support_email = Setting.objects.filter(name='support_email').first()
                if support_email:
                    output['support_email'] = support_email.value

            return output

        def wrapper(request, *args, **kw):  
            output = fn(request, *args, **kw)
            if isinstance(output, dict):
                output = populate_template_dict(request, output)
                return render(request, template, output)
            return output
        return wrapper
    return renderer
    
def check_permissions(fn):
    """
    Checks that the user has permission to access the given experiment and/or instrument.
    Queries ICATCache to check owned instruments and experiments.
    """
    def request_processor(request, *args, **kwargs):
        if USER_ACCESS_CHECKS and not request.user.is_superuser:
            # Get the things to check by from the arguments supplied.
            experiment_reference, owned_instrument_name, viewed_instrument_name, optional_instrument_names = None, None, None, []
            if "run_number" in kwargs:
                # Get the experiment and instrument from the given run number.
                run = ReductionRun.objects.filter(run_number=int(kwargs["run_number"])).first()
                experiment_reference, viewed_instrument_name = run.experiment.reference_number, run.instrument.name
            else:
                # Get the experiment reference if it's supplied.
                if "reference_number" in kwargs:
                    experiment_reference = int(kwargs["reference_number"])
                    # Find the associated instrument.
                    experiment_obj = Experiment.objects.filter(reference_number=experiment_reference).first()
                    if experiment_obj:
                        optional_instrument_names = list(set([run.instrument.name for run in experiment_obj.reduction_runs.all()]))
                else:
                    # Look for an instrument name under 'instrument_name', or, failing that, 'instrument'.
                    owned_instrument_name = kwargs.get("instrument_name", kwargs.get("instrument"))
            
            with ICATCache(AUTH='uows', SESSION={'sessionid':request.session['sessionid']}) as icat:
                owned_instrument_list, valid_instrument_list = icat.get_owned_instruments(int(request.user.username)), icat.get_valid_instruments(int(request.user.username))
                
                # Check for access to the instrument
                if owned_instrument_name or viewed_instrument_name:
                    optional_instrument_names.append(owned_instrument_name if owned_instrument_name is not None else viewed_instrument_name)
                    
                    # Check access to an owned instrument.
                    if owned_instrument_name is not None and owned_instrument_name not in owned_instrument_list:
                        raise PermissionDenied() # No access allowed
                    
                    # Check access to a valid instrument (able to view some runs, etc.).
                    if viewed_instrument_name is not None and viewed_instrument_name not in owned_instrument_list + valid_instrument_list:
                        raise PermissionDenied() # No access allowed
                
                # Check for access to the experiment; if the user owns one of the associated instruments, we don't need to check this.
                if optional_instrument_names and list(set(optional_instrument_names).intersection(owned_instrument_list)):
                    pass
                elif experiment_reference is not None and experiment_reference not in icat.get_associated_experiments(int(request.user.username)):
                    raise PermissionDenied()
        
        # If we're here, the access checks have passed.
        return fn(request, *args, **kwargs)
    
    return request_processor