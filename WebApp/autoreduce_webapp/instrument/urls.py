# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from django.urls import path
from instrument import views

app_name = "instrument"

urlpatterns = [
    path('<str:instrument>/submit_runs/', views.submit_runs, name='submit_runs'),
    path('<str:instrument>/variables/', views.instrument_variables, name='variables'),
    path('<str:instrument>/variables/<int:start>/<int:end>/', views.instrument_variables, name='variables'),
    path('<str:instrument>/variables_summary/', views.instrument_variables_summary, name='variables_summary'),
    path('<str:instrument>/variables/<int:start>/<int:end>/delete',
         views.delete_instrument_variables,
         name='delete_variables'),
    path('<str:instrument>/variables/experiment/<int:experiment_reference>/',
         views.instrument_variables,
         name='variables_by_experiment'),
    path('<str:instrument>/variables/experiment/<int:experiment_reference>/delete/',
         views.delete_instrument_variables,
         name='delete_variables_by_experiment'),
    path('<str:instrument>/default_variables/', views.current_default_variables, name='current_default_variables'),
    path('<str:instrument>/pause', views.instrument_pause, name='instrument_pause'),
]
