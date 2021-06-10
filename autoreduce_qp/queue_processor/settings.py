# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint: skip-file
import os

AUTOREDUCE_HOME_ROOT = os.path.expanduser("~/.autoreduce")
PROJECT_ROOT = os.path.join(AUTOREDUCE_HOME_ROOT, "dev")
FACILITY = 'ISIS'

# The reduction outputs are saved there. If you want to avoid writing to the real CEPH then
# change this to a local directory - the reductions should process fine regardless.
# %(instrument, experiment_number, run_number)
if "AUTOREDUCTION_PRODUCTION" in os.environ:
    CEPH_DIRECTORY = "/instrument/%s/RBNumber/RB%s/autoreduced/%s"
    MANTID_PATH = "/opt/Mantid/lib"
else:
    CEPH_DIRECTORY = f"{PROJECT_ROOT}/reduced-data/%s/RB%s/autoreduced/%s/"
    MANTID_PATH = "/tmp/Mantid/lib"

if "AUTOREDUCTION_PRODUCTION" in os.environ:
    # for when deploying on production - this is the real path where the mounts are
    ARCHIVE_ROOT = "\\\\isis\\inst$\\" if os.name == "nt" else "/isis"
elif "RUNNING_VIA_PYTEST" in os.environ:
    # for testing which uses a local folder to simulate an archive
    ARCHIVE_ROOT = os.path.join(PROJECT_ROOT, 'test-archive')
else:
    # the default development path
    ARCHIVE_ROOT = os.path.join(PROJECT_ROOT, 'data-archive')

# Variables that get changes less
# %(instrument, cycle, experiment_number, run_number)
CYCLE_DIRECTORY = os.path.join(ARCHIVE_ROOT, 'NDX%s', 'Instrument', 'data', 'cycle_%s')
SCRIPTS_DIRECTORY = os.path.join(ARCHIVE_ROOT, "NDX%s", "user", "scripts", "autoreduction")

SCRIPT_TIMEOUT = 3600  # The max time to wait for a user script to finish running (seconds)
TEMP_ROOT_DIRECTORY = "/autoreducetmp"
