# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from django.urls import path
from instrument.views import runs, variables, pause

app_name = "instrument"

urlpatterns = [
    path('<str:instrument>/submit_runs/', runs.submit_runs, name='submit_runs'),
    path('<str:instrument>/configure_new_runs/', runs.configure_new_runs, name='variables'),
    path('<str:instrument>/configure_new_runs/<int:start>/', runs.configure_new_runs, name='variables'),
    path('<str:instrument>/configure_new_runs/<int:start>/<int:end>/', runs.configure_new_runs, name='variables'),
    path('<str:instrument>/variables_summary/', variables.instrument_variables_summary, name='variables_summary'),
    path('<str:instrument>/variables/<int:start>/<int:end>/delete',
         variables.delete_instrument_variables,
         name='delete_variables'),
    path('<str:instrument>/variables/experiment/<int:experiment_reference>/',
         runs.configure_new_runs,
         name='variables_by_experiment'),
    path('<str:instrument>/variables/experiment/<int:experiment_reference>/delete/',
         variables.delete_instrument_variables,
         name='delete_variables_by_experiment'),
    path('<str:instrument>/default_variables/', variables.current_default_variables, name='current_default_variables'),
    path('<str:instrument>/pause/', pause.instrument_pause, name='pause'),
]
