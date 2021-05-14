# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Handle page responses for WebApp
"""
from django.http import HttpRequest
from django.shortcuts import render
from django.template import RequestContext

from autoreduce_db.reduction_viewer.models import Setting

# pylint: disable=unused-argument


def get_admin_email():
    """Check the settings for a valid admin email"""
    try:
        admin_email = Setting.objects.get(name='admin_email')
        return admin_email.value
    # pylint: disable=bare-except
    except:
        return ''


def handler400(request, exception):
    """Error 400 handler"""
    response = render(None, '400.html', {'admin_email': get_admin_email()}, RequestContext(request))
    response.status_code = 400
    return response


def handler404(request, exception):
    """Error 404 handler"""
    response = render('404.html', {'admin_email': get_admin_email()}, RequestContext(request))
    response.status_code = 404
    return response


def handler403(request, exception):
    """Error 403 handler"""
    response = render('403.html', {'admin_email': get_admin_email()}, RequestContext(request))
    response.status_code = 403
    return response


def handler500(request):
    """Error 500 handler"""
    response = render(RequestContext(request), '500.html', {'admin_email': get_admin_email()})
    response.status_code = 500
    return response


def render_error(request: HttpRequest, message: str):
    """
    Return the error page with a message displayed.
    :param request: (HttpRequest) The original sent request
    :param message: (str) The message that will be displayed
    :return: (HttpResponse) The error page
    """
    return render(request, 'error.html', {'message': message, 'admin_email': get_admin_email()}, status=500)
