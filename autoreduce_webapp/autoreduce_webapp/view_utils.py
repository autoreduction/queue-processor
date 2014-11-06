from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from autoreduce_webapp.uows_client import UOWSClient
from autoreduce_webapp.settings import UOWS_LOGIN_URL, LOGIN_URL, INSTALLED_APPS
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
        if has_valid_login(request) and request.user.is_staff:
            return fn(request, *args, **kws)
        if request.user.is_authenticated():
            raise PermissionDenied()
        return handle_redirect(request)
    return request_processor

def require_admin(fn):
    """
    Function decorator to check whether the user is a superuser
    """
    def request_processor(request, *args, **kws):
        if has_valid_login(request) and request.user.is_superuser:
            return fn(request, *args, **kws)
        if request.user.is_authenticated():
            raise PermissionDenied()
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