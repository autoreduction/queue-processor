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

from paths.path_manipulation import add_to_path

from utils.project.structure import get_project_root

# ActiveMQ
ACTIVEMQ = {
    "brokers": "127.0.1.1:61613",
    "amq_queues": ["/queue/ReductionPending"],
    "amq_user": "admin",
    "amq_pwd": "admin",
    "postprocess_error": "/queue/ReductionError",
    "reduction_started": "/queue/ReductionStarted",
    "reduction_complete": "/queue/ReductionComplete",
    "reduction_error": "/queue/ReductionError",
    "reduction_skipped": "/queue/ReductionSkipped"
}

# MISC
# "scripts_directory": "/isis/NDX%s/user/scripts/autoreduction",
# "ceph_directory": "/instrument/%s/RBNumber/RB%s/autoreduced/%s",
MISC = {
    "script_timeout": 3600,  # The max time to wait for a user script to finish running (seconds)
    "mantid_path": "/opt/Mantid/bin",
    "scripts_directory": add_to_path(get_project_root(), ['data-archive', 'NDX%s', 'user', 'scripts', 'autoreduction']),
    "post_process_directory": add_to_path(os.path.dirname(os.path.realpath(__file__)), "post_process_admin.py"),
    "ceph_directory": add_to_path(get_project_root(), ['reduced-data', '%s', 'RB%s', 'autoreduced', '%s']),
    "temp_root_directory": "/autoreducetmp",
    "excitation_instruments": ["LET", "MARI", "MAPS", "MERLIN", "WISH", "GEM"]
}
