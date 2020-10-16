# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint: skip-file
"""
Settings for ActiveMQ and reduction variables
"""
import os

from paths.path_manipulation import append_path

from utils.project.structure import get_project_root

# MISC
# "scripts_directory": "/isis/NDX%s/user/scripts/autoreduction",
# "ceph_directory": "/instrument/%s/RBNumber/RB%s/autoreduced/%s",
MISC = {
    "script_timeout": 3600,  # The max time to wait for a user script to finish running (seconds)
    "mantid_path": "/opt/Mantid/lib",
    "scripts_directory": append_path(get_project_root(), ['data-archive', 'NDX%s', 'user', 'scripts', 'autoreduction']),
    "post_process_directory": append_path(os.path.dirname(os.path.realpath(__file__)), ["post_process_admin.py"]),
    "ceph_directory": append_path(get_project_root(), ['reduced-data', '%s', 'RB%s', 'autoreduced', '%s']),
    "temp_root_directory": "/autoreducetmp",
    "flat_output_instruments": ["LET", "MARI", "MAPS", "MERLIN", "WISH", "GEM"]
}
