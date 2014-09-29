from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response

def index(request):
    context = RequestContext(request)
    context_dict = {}
    return render_to_response('base.html', context_dict, context)

def logout(request):
    pass

def run_queue(request):
    pass