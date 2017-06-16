# ActiveMQ
ACTIVEMQ = {
    "brokers": "localhost:61613",
    "amq_queues": ["/queue/ReductionPending"],
    "amq_user": "autoreduce",
    "amq_pwd": "activedev",
    "postprocess_error": "/queue/ReductionError",
    "reduction_started": "/queue/ReductionStarted",
    "reduction_complete": "/queue/ReductionComplete",
    "reduction_error": "/queue/ReductionError"
}

# MISC
MISC = {
    "scripts_directory": "/isis/NDX%s/user/scripts/autoreduction",
    "post_process_directory": "/home/tip22963/AutoreductionProcessor/post_process_admin.py",
    "archive_directory": "/isis/NDX%s/Instrument/data/cycle_%s/autoreduced/%s/%s",
    "ceph_directory": "/instrument/%s/RBNumber/RB%s/autoreduced/%s",
    "temp_root_directory": "/autoreducetmp",
    "ceph_instruments": [],
    "excitation_instruments": ["LET", "MARI", "MAPS", "MERLIN", "WISH", "GEM"]
}