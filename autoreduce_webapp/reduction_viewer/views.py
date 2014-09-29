from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect

def index(request):
    context = RequestContext(request)
    context_dict = {}
    return render_to_response('base.html', context_dict, context)

def run_queue(request):
    pass