# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint: skip-file
"""
Settings for End of run monitor
"""
import os

from utils.project.structure import get_project_root

from sentry_sdk import init
init('http://4b7c7658e2204228ad1cfd640f478857@172.16.114.151:9000/1')

# Config settings for cycle number, and instrument file arrangement
INST_FOLDER = os.path.join(get_project_root(), 'data-archive', 'NDX%s', 'Instrument')
DATA_LOC = os.path.join('data', 'cycle_%s')
SUMMARY_LOC = os.path.join('logs', 'journal', 'summary.txt')
LAST_RUN_LOC = os.path.join('logs', 'lastrun.txt')
EORM_LOG_FILE = os.path.join(get_project_root(), 'logs', 'end_of_run_monitor.log')
EORM_LAST_RUN_FILE = os.path.join(get_project_root(), 'logs', 'eorm_last_runs.csv')
INSTRUMENTS = [{'name': 'WISH', 'use_nexus': True},
               {'name': 'GEM', 'use_nexus': True},
               {'name': 'OSIRIS', 'use_nexus': True},
               {'name': 'POLARIS', 'use_nexus': True},
               {'name': 'MUSR', 'use_nexus': True},
               {'name': 'POLREF', 'use_nexus': True}]

# New EoRM
CYCLE_FOLDER = "cycle_18_4"
LAST_RUNS_CSV = "lastruns.csv"
