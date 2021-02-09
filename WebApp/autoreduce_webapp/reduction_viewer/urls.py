# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from django.urls import path
from reduction_viewer import views

app_name = "runs"

urlpatterns = [
    path('queue/', views.run_queue, name='queue'),
    path('failed/', views.fail_queue, name='failed'),
    path('<str:instrument>/', views.runs_list, name='list'),
    path('<str:instrument_name>/<int:run_number>/', views.run_summary, name='summary'),
    path('<str:instrument_name>/<int:run_number>/<int:run_version>/', views.run_summary, name='summary'),
]
