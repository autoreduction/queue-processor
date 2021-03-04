# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint: skip-file
import os
from utils.project.structure import PROJECT_ROOT

FACILITY = 'ISIS'

MYSQL = {'HOST': 'localhost:3306', 'USER': 'test-user', 'PASSWD': 'pass', 'DB': 'autoreduction'}

# Logging
LOG_FILE = os.path.join(PROJECT_ROOT, 'logs', 'queue_processor.log')
DEBUG = False

if DEBUG:
    LOG_LEVEL = 'DEBUG'
else:
    LOG_LEVEL = 'INFO'

# The reduction outputs are saved there. If you want to avoid writing to the real CEPH then
# change this to a local directory - the reductions should process fine regardless.
# %(instrument, experiment_number, run_number)
# CEPH_DIRECTORY = "/instrument/%s/RBNumber/RB%s/autoreduced/%s"
CEPH_DIRECTORY = f"{PROJECT_ROOT}/reduced-data/%s/RB%s/autoreduced/%s/"

# for development/prod or when connecting to the real archive, mounted locally
# ARCHIVE_ROOT = "/isis"
# for testing which uses a local folder to simulate an archive
if "RUNNING_VIA_PYTEST" in os.environ:
    ARCHIVE_ROOT = os.path.join(PROJECT_ROOT, 'test-archive')
else:
    ARCHIVE_ROOT = os.path.join(PROJECT_ROOT, 'data-archive')

# Variables that get changes less
# %(instrument, cycle, experiment_number, run_number)
CYCLE_DIRECTORY = os.path.join(ARCHIVE_ROOT, 'NDX%s', 'Instrument', 'data', 'cycle_%s')
SCRIPTS_DIRECTORY = f"{ARCHIVE_ROOT}/NDX%s/user/scripts/autoreduction/"

SCRIPT_TIMEOUT = 3600  # The max time to wait for a user script to finish running (seconds)
MANTID_PATH = "/opt/Mantid/lib"
TEMP_ROOT_DIRECTORY = "/autoreducetmp"
FLAT_OUTPUT_INSTRUMENTS = ["LET", "MARI", "MAPS", "MERLIN", "WISH", "GEM"]
