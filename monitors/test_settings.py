# pylint: skip-file
"""
Settings for End of run monitor
"""
import os

from utils.project.structure import get_project_root

# Config settings for cycle number, and instrument file arrangement
INST_FOLDER = os.path.join(get_project_root(), 'data-archive', 'NDX%s', 'Instrument')
DATA_LOC = os.path.join('data', 'cycle_%s')
SUMMARY_LOC = os.path.join('logs', 'journal', 'summary.txt')
LAST_RUN_LOC = os.path.join('logs', 'lastrun.txt')
EORM_LOG_FILE = os.path.join(get_project_root(), 'logs', 'end_of_run_monitor.log')
INSTRUMENTS = [{'name': 'WISH', 'file_prefix': 'WISH', 'use_nexus': True},
               {'name': 'GEM', 'file_prefix': 'GEM', 'use_nexus': True},
               {'name': 'OSIRIS', 'file_prefix': 'OSIRIS', 'use_nexus': True},
               {'name': 'POLARIS', 'file_prefix': 'POLARIS', 'use_nexus': True},
               {'name': 'MUSR', 'file_prefix': 'MUSR', 'use_nexus': True},
               {'name': 'POLREF', 'file_prefix': 'POLREF', 'use_nexus': True}]
