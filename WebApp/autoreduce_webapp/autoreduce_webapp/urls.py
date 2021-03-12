# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from instrument.views import runs
from reduction_viewer import views as reduction_viewer_views

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
    path('runs/', include('reduction_viewer.urls')),
    path('runs/<str:instrument>/confirmation/', runs.run_confirmation, name='run_confirmation'),

    # ===========================INSTRUMENT========================== #
    path('instrument/', include('instrument.urls')),

    # ===========================EXPERIMENT========================== #
    path('experiment/<int:reference_number>/', reduction_viewer_views.experiment_summary, name='experiment_summary'),

    # ===========================SCRIPTS============================= #
    path('graph/', reduction_viewer_views.graph_home, name="graph"),
    path('graph/<str:instrument_name>', reduction_viewer_views.graph_instrument, name="graph_instrument"),
    path('stats/', reduction_viewer_views.stats, name="stats"),

    # ===========================VISUALISATION============================= #
    path('django_plotly_dash/', include('django_plotly_dash.urls'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
