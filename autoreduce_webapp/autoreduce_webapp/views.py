from django.shortcuts import render_to_response
from django.template import RequestContext

def handler400(request):
    context_dictionary = {
        'admin_email' : ''
    }
    response = render_to_response('400.html', context_dictionary, RequestContext(request))
    response.status_code = 400
    return response

def handler404(request):
    context_dictionary = {
        'admin_email' : ''
    }
    response = render_to_response('404.html', context_dictionary, RequestContext(request))
    response.status_code = 404
    return response

def handler403(request):
    context_dictionary = {
        'admin_email' : ''
    }
    response = render_to_response('403.html', context_dictionary, RequestContext(request))
    response.status_code = 403
    return response

def handler500(request):
    context_dictionary = {
        'admin_email' : ''
    }
    response = render_to_response('500.html', context_dictionary, RequestContext(request))
    response.status_code = 500
    return response