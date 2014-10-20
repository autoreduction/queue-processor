from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.generic.base import View
from autoreduce_webapp.view_utils import login_and_uows_valid, render_with, require_staff
from reduction_variables.models import InstrumentVariable, RunVariable
from django.http import HttpResponseForbidden
from autoreduce_webapp.icat_communication import ICATCommunication
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL
import logging
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)

def run_confirmation(request, run_number, run_version=0):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))

class InstrumentSummary(View):
    @login_and_uows_valid
    @render_with('snippets/instrument_summary_variables.html')
    @require_staff
    def get(request, instrument):
        context_dictionary = {}


        try:
            #TODO: comment out when ICAT and uows are pointing at same session
            #with ICATCommunication(AUTH='uows', SESSION={'sessionid':request.session['sessionid']}) as icat:
            with ICATCommunication() as icat:
                owned_instruments = icat.get_owned_instruments(int(request.user.username))
                if not request.user.is_superuser and instrument not in owned_instruments:
                    return HttpResponseForbidden('Access Forbidden')
        except Exception as icat_e:
            logging.error(icat_e.message)
            return HttpResponseForbidden('Could not verify access permission')

        return context_dictionary

def instrument_variables(request, instrument):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))

def run_variables(request, run_number, run_version=0):
    context_dictionary = {}
    return render_to_response('base.html', context_dictionary, RequestContext(request))
