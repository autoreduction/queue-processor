from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from autoreduce_webapp.uows_client import UOWSClient
from autoreduce_webapp.settings import UOWS_LOGIN_URL, LOGIN_URL, INSTALLED_APPS, USER_ACCESS_CHECKS
from autoreduce_webapp.icat_cache import ICATCache
from reduction_viewer.models import ReductionRun
from django.template import RequestContext
from django.shortcuts import render_to_response
from reduction_viewer.models import Notification, Setting

def has_valid_login(request):
    """
    Check that the user is correctly logged in and their session is still considered valid
    """
    if request.user.is_authenticated() and request.session['sessionid'] and UOWSClient().check_session(request.session['sessionid']):
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
    Decorator for Django views that sends returned dict to render_to_response function
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
                return render_to_response(template, output, RequestContext(request))      
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
            experiment_reference, instrument_name = None, None
            if "run_number" in kwargs:
                # Get the experiment and instrument from the given run number.
                run = ReductionRun.objects.filter(run_number=kwargs["run_number"]).first()
                experiment_reference, instrument_name = run.experiment.reference_number, run.instrument.name
            else:
                # Get the experiment reference if it's supplied.
                if "reference_number" in kwargs: experiment_reference = int(kwargs["reference_number"])
                # Look for an instrument name under 'instrument_name', or, failing that, 'instrument'.
                instrument_name = kwargs.get("instrument_name", kwargs.get("instrument"))
            
            with ICATCache(AUTH='uows', SESSION={'sessionid':request.session['sessionid']}) as icat:
                # Check for access to the experiment.
                if experiment_reference is not None and experiment_reference not in icat.get_associated_experiments(int(request.user.username)):
                    raise PermissionDenied()
                
                # Check for access to the instrument.
                if instrument_name is not None and instrument_name not in icat.get_owned_instruments(int(request.user.username)):
                    raise PermissionDenied()
        
        # If we're here, the access checks have passed.
        return fn(request, *args, **kwargs)
    
    return request_processor