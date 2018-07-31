# pylint: skip-file
"""
Settings for ActiveMQ and reduction variables
"""
import os

# ActiveMQ
ACTIVEMQ = {
    "brokers": "127.0.1.1:61613",
    "amq_queues": ["/queue/ReductionPending"],
    "amq_user": "admin",
    "amq_pwd": "admin",
    "postprocess_error": "/queue/ReductionError",
    "reduction_started": "/queue/ReductionStarted",
    "reduction_complete": "/queue/ReductionComplete",
    "reduction_error": "/queue/ReductionError"
}

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
TEST_ARCHIVE_DIR = os.path.join(PROJECT_DIR, 'systemtests', 'data-archive')
# MISC
MISC = {
    "script_timeout": 3600,  # The maximum time that we should wait for a user script to finish running (in seconds)
    "mantid_path": "/opt/Mantid/bin",
    "scripts_directory": os.path.join(TEST_ARCHIVE_DIR, 'NDX%s', 'user',
                                      'scripts', 'autoreduction'),
    "post_process_directory": os.path.join(os.path.dirname(os.path.realpath(__file__)), "post_process_admin.py"),
    "archive_directory": os.path.join(TEST_ARCHIVE_DIR, 'NDX%s', 'Instrument', 'data',
                                      'cycle_%s', 'autoreduced', '%s', '%s'),
    "ceph_directory": os.path.join(PROJECT_DIR, 'systemtests', 'ceph', 'instrument',
                                   '%s', 'RBNumber', 'RB%s', 'autoreduced', '%s'),
    "temp_root_directory": os.path.join(PROJECT_DIR, 'systemtests', 'autoreducetmp'),
    "ceph_instruments": [],
    "excitation_instruments": ["LET", "MARI", "MAPS", "MERLIN", "WISH", "GEM"]
}

LOG = {
    "log_location": os.path.join(os.path.dirname(os.path.abspath(__file__)), "autoreductionProcessor.log")
}
