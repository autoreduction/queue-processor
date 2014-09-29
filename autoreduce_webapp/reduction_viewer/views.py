from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import logout

def index(request):
    context = RequestContext(request)
    context_dict = {}
    return render_to_response('base.html', context_dict, context)

def logout(request):
    logout(request)
    return redirect('index')

def run_queue(request):
    pass