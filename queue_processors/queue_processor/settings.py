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

# Directory Locations
if os.name == 'nt':
    # Adding this as we no longer have any nodes running on Windows.
    # The change will appear in https://github.com/ISISScientificComputing/autoreduce/pull/1033
    # If Windows must be used you will have to redefine the variables from below
    raise RuntimeError("Running the queue processor on Windows is no longer expected, nor actively supported.")
else:
    # %(instrument)
    # REDUCTION_DIRECTORY = '/isis/NDX%s/user/scripts/autoreduction'
    REDUCTION_DIRECTORY = os.path.join(PROJECT_ROOT, 'data-archive', 'NDX%s', 'user', 'scripts', 'autoreduction')
    # %(instrument, cycle, experiment_number, run_number)
    # ARCHIVE_DIRECTORY = '/isis/NDX%s/Instrument/data/cycle_%s/autoreduced/%s/%s'
    ARCHIVE_DIRECTORY = os.path.join(PROJECT_ROOT, 'data-archive', 'NDX%s', 'Instrument', 'data', 'cycle_%s',
                                     'autoreduced', '%s', '%s')
TEST_REDUCTION_DIRECTORY = '/reducedev/isis/output/NDX%s/user/scripts/autoreduction'
TEST_ARCHIVE_DIRECTORY = '/isis/NDX%s/Instrument/data/cycle_%s/autoreduced/%s/%s'

SCRIPT_TIMEOUT = 3600  # The max time to wait for a user script to finish running (seconds)
MANTID_PATH = "/opt/Mantid/lib"
SCRIPTS_DIRECTORY = f"{PROJECT_ROOT}/data-archive/NDX%s/user/scripts/autoreduction/"
CEPH_DIRECTORY = f"{PROJECT_ROOT}/reduced-data/%s/RB%s/autoreduced/%s/"
TEMP_ROOT_DIRECTORY = "/autoreducetmp"
FLAT_OUTPUT_INSTRUMENTS = ["LET", "MARI", "MAPS", "MERLIN", "WISH", "GEM"]
