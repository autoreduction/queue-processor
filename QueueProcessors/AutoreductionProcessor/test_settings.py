# pylint: skip-file
"""
Settings for ActiveMQ and reduction variables
"""
import os

from utils.project.structure import get_project_root, get_log_folder

# ActiveMQ
ACTIVEMQ = {
    "brokers": "YOUR-ACTIVEMQ-SERVER",
    "amq_queues": ["/queue/ReductionPending"],
    "amq_user": "YOUR-ACTIVEMQ-USERNAME",
    "amq_pwd": "YOUR-PASSWORD",
    "postprocess_error": "/queue/ReductionError",
    "reduction_started": "/queue/ReductionStarted",
    "reduction_complete": "/queue/ReductionComplete",
    "reduction_error": "/queue/ReductionError"
}

# MISC
MISC = {
    # The maximum time that we should wait for a user script to finish running (in seconds)
    "script_timeout": 3600,
    "mantid_path": "/opt/Mantid/bin",
    # /isis/NDX<instrument>/user/scripts/autoreduction
    "scripts_directory": os.path.join(get_project_root(), 'data-archive',
                                      'NDX%s', 'user', 'scripts', 'autoreduction'),
    "post_process_directory": os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                           "post_process_admin.py"),
    "ceph_directory": "/instrument/%s/RBNumber/RB%s/autoreduced/%s",
    "temp_root_directory": "/autoreducetmp",
    "excitation_instruments": ["LET", "MARI", "MAPS", "MERLIN", "WISH", "GEM"]
}

LOGGING_PATH = os.path.join(get_log_folder(), 'queue_processor.log')
