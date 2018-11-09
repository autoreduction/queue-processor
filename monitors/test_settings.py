# pylint: skip-file
"""
Settings for End of run monitor
"""
import os

from utils.project.structure import get_project_root

# Config settings for cycle number, and instrument file arrangement
ARCHIVE_BASE = get_project_root()
DATA_ARCHIVE = os.path.join(ARCHIVE_BASE, 'data-archive')
INST_FOLDER = os.path.join(DATA_ARCHIVE, 'NDX%s', 'Instrument')
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
