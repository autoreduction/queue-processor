from django.shortcuts import redirect
from autoreduce_webapp.uows_client import UOWSClient
from autoreduce_webapp.settings import UOWS_LOGIN_URL, LOGIN_URL
from django.template import RequestContext
from django.shortcuts import render_to_response
from reduction_viewer.models import Notification

def login_and_uows_valid(fn):
    """
        Function decorator to check whether a user's session is still valid
    """
    def request_processor(request, *args, **kws):
        if request.user.is_authenticated() and request.session['sessionid'] and UOWSClient().check_session(request.session['sessionid']):
            return fn(request, *args, **kws)
        if request.GET.get('sessionid'):
            return redirect(request.build_absolute_uri(LOGIN_URL) + "?next=" + request.build_absolute_uri().replace('?sessionid=', '&sessionid=')) 
        return redirect(UOWS_LOGIN_URL + request.build_absolute_uri())
    return request_processor

def with_template(template):
    def wrapper(view):
        def call(request, *args, **kwargs):
            context = {}
            ret = view(request, context, *args, **kwargs)
            if ret: return(ret)
            return(render_to_response(template, RequestContext(request, context)))
        return(call)
    return(wrapper)

def render_with(template):
    """
        Decorator for Django views that sends returned dict to render_to_response function
        with given template and RequestContext as context instance.
    """
    def renderer(fn):
        def populate_template_dict(request, output):
            if 'notifications' not in output:
                if request.user.is_authenticated() and request.user.is_staff:
                    output['notifications'] = Notification.objects.filter(is_active=True, is_staff_only=True)
                else:
                    output['notifications'] = Notification.objects.filter(is_active=True)
            return output

        def wrapper(request, *args, **kw):  
            output = fn(request, *args, **kw)
            if isinstance(output, dict):
                output = populate_template_dict(request, output)    
                return render_to_response(template, output, RequestContext(request))      
            return output
        return wrapper
    return renderer