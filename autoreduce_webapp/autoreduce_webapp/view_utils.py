from django.shortcuts import redirect
from autoreduce_webapp.uows_client import UOWSClient

def login_and_uows_valid(fn):
    """
        Function decorator to check whether a user's session is still valid
    """
    def request_processor(request, *args, **kws):
        if request.user.is_authenticated() and request.session['sessionid'] and UOWSClient().check_session(request.session['sessionid']):
            return fn(request, *args, **kws)

        return redirect(UOWS_LOGIN_URL + request.build_absolute_uri('login'))
    return request_processor