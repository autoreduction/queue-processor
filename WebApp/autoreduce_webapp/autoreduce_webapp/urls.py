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
from django.urls import path

from utils.project.structure import get_project_root
sys.path.append(os.path.join(get_project_root(), 'WebApp', 'autoreduce_webapp'))

from reduction_viewer import views as reduction_viewer_views
from instrument import views as reduction_variables_views

# pylint: disable=invalid-name
handler400 = 'autoreduce_webapp.views.handler400'
handler403 = 'autoreduce_webapp.views.handler403'
handler404 = 'autoreduce_webapp.views.handler404'
handler500 = 'autoreduce_webapp.views.handler500'

urlpatterns = [
    # ===========================MISC================================= #
    path('', reduction_viewer_views.index, name='index'),
    path('admin/', admin.site.urls),
    path('logout/', reduction_viewer_views.logout, name='logout'),
    path('help/', reduction_viewer_views.help, name='help'),

    # ===========================RUNS================================= #
    path('overview/', reduction_viewer_views.overview, name='overview'),
    path('runs/queue/', reduction_viewer_views.run_queue, name='run_queue'),
    path('runs/failed/', reduction_viewer_views.fail_queue, name='fail_queue'),
    path('runs/<str:instrument_name>/<int:run_number>/', reduction_viewer_views.run_summary, name='run_summary'),
    path('runs/<str:instrument_name>/<int:run_number>/<int:run_version>/',
         reduction_viewer_views.run_summary,
         name='run_summary'),
    path('runs/<str:instrument>/confirmation/', reduction_variables_views.run_confirmation, name='run_confirmation'),

    # ===========================INSTRUMENT========================== #
    path('instrument/<str:instrument>/', reduction_viewer_views.instrument_summary, name='instrument_summary'),
    path('instrument/<str:instrument>/pause', reduction_viewer_views.instrument_pause, name='instrument_pause'),
    path('instrument/', include('instrument.urls')),

    # ===========================EXPERIMENT========================== #
    path('experiment/<int:reference_number>/', reduction_viewer_views.experiment_summary, name='experiment_summary'),

    # ===========================SCRIPTS============================= #
    path('graph/', reduction_viewer_views.graph_home, name="graph"),
    path('graph/<str:instrument_name>', reduction_viewer_views.graph_instrument, name="graph_instrument"),
    path('stats', reduction_viewer_views.stats, name="stats"),

    # ===========================VISUALISATION============================= #
    path('django_plotly_dash/', include('django_plotly_dash.urls'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
