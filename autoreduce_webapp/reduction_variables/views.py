from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response

def run_confirmation(request, run_number, run_version=0):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))

def instrument(request):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))

def instrument_summary(request, instrument):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))

def instrument_variables(request, instrument):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))

def run_variables(request, run_number, run_version=0):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))
