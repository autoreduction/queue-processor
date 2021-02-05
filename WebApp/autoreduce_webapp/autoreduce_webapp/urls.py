# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Routing for URI to page contents
"""
import sys
import os

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from utils.project.structure import get_project_root
sys.path.append(os.path.join(get_project_root(), 'WebApp', 'autoreduce_webapp'))

from reduction_viewer import views as reduction_viewer_views
from reduction_variables import views as reduction_variables_views

# pylint: disable=invalid-name
handler400 = 'autoreduce_webapp.views.handler400'
handler403 = 'autoreduce_webapp.views.handler403'
handler404 = 'autoreduce_webapp.views.handler404'
handler500 = 'autoreduce_webapp.views.handler500'

urlpatterns = [
    # ===========================MISC================================= #
    url(r'^admin/', admin.site.urls),
    url(r'^$', reduction_viewer_views.index, name='index'),
    url(r'^logout/$', reduction_viewer_views.logout, name='logout'),
    url(r'^help/$', reduction_viewer_views.help, name='help'),

    # ===========================RUNS================================= #
    url(r'^overview/', reduction_viewer_views.overview, name='overview'),
    url(r'^runs/queue/$', reduction_viewer_views.run_queue, name='run_queue'),
    url(r'^runs/failed/$', reduction_viewer_views.fail_queue, name='fail_queue'),
    url(r'^runs/(?P<instrument_name>\w+)/(?P<run_number>[0-9]+)/$',
        reduction_viewer_views.run_summary,
        name='run_summary'),
    url(r'^runs/(?P<instrument_name>\w+)/(?P<run_number>[0-9]+)/(?P<run_version>[0-9]+)/$',
        reduction_viewer_views.run_summary,
        name='run_summary'),
    url(r'^runs/(?P<instrument>\w+)/confirmation/$',
        reduction_variables_views.run_confirmation,
        name='run_confirmation'),

    # ===========================INSTRUMENT========================== #
    url(r'^instrument/(?P<instrument>\w+)/$', reduction_viewer_views.instrument_summary, name='instrument_summary'),
    url(r'^instrument/(?P<instrument>\w+)/pause$', reduction_viewer_views.instrument_pause, name='instrument_pause'),
    url(r'^instrument/(?P<instrument>\w+)/submit_runs/$',
        reduction_variables_views.submit_runs,
        name='instrument_submit_runs'),
    url(r'^instrument/(?P<instrument>\w+)/variables/$',
        reduction_variables_views.instrument_variables,
        name='instrument_variables'),
    url(r'^instrument/(?P<instrument>\w+)/variables(?:/(?P<start>[0-9]+))?(?:/(?P<end>[0-9]+))?/$',
        reduction_variables_views.instrument_variables,
        name='instrument_variables'),
    # pylint: disable=line-too-long
    url(r'^instrument/(?P<instrument>\w+)/variables_summary/$',
        reduction_variables_views.instrument_variables_summary,
        name='instrument_variables_summary'),
    # pylint: disable=line-too-long
    url(r'^instrument/(?P<instrument>\w+)/variables(?:/(?P<start>[0-9]+))?(?:/(?P<end>[0-9]+))?/delete$',
        reduction_variables_views.delete_instrument_variables,
        name='delete_instrument_variables'),
    url(r'^instrument/(?P<instrument>\w+)/variables/experiment/(?P<experiment_reference>[0-9]+)/$',
        reduction_variables_views.instrument_variables,
        name='instrument_variables_by_experiment'),
    url(r'^instrument/(?P<instrument>\w+)/variables/experiment/(?P<experiment_reference>[0-9]+)/delete$',
        reduction_variables_views.delete_instrument_variables,
        name='delete_instrument_variables_by_experiment'),
    url(r'^instrument/(?P<instrument>\w+)/default_variables/$',
        reduction_variables_views.current_default_variables,
        name='current_default_variables'),

    # ===========================EXPERIMENT========================== #
    url(r'^experiment/(?P<reference_number>-?[0-9]+)/$',
        reduction_viewer_views.experiment_summary,
        name='experiment_summary'),

    # ===========================SCRIPTS============================= #
    url(r'^graph/$', reduction_viewer_views.graph_home, name="graph"),
    url(r'^graph/(?P<instrument_name>\w+)', reduction_viewer_views.graph_instrument, name="graph_instrument"),
    url(r'^stats', reduction_viewer_views.stats, name="stats"),

    # ===========================VISUALISATION============================= #
    url('django_plotly_dash/', include('django_plotly_dash.urls'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
