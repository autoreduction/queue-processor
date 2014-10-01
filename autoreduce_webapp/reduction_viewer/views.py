from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import logout as django_logout
from autoreduce_webapp.uows_client import UOWSClient
from autoreduce_webapp.settings import UOWS_LOGIN_URL

def index(request):
    if request.user.is_authenticated():
        return redirect('run_list')
    else:
        return redirect(UOWS_LOGIN_URL + request.build_absolute_uri('run_queue'))

def logout(request):
    django_logout(request)
    session_id = request.session.get('session_id')
    if session_id:
        UOWSClient().logout(session_id)
    return redirect('index')

def run_queue(request):
    return render_to_response('base.html')

def run_list(request):
    return render_to_response('base.html')