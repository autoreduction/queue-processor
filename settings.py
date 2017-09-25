# ICAT
ICAT_SETTINGS = {
    'AUTH': 'simple',
    'URL': 'https://icatisis.esc.rl.ac.uk/ICATService/ICAT?wsdl',
    'USER': 'autoreduce',
    'PASSWORD': 'YOUR-PASSWORD'
}
# ActiveMQ
ACTIVEMQ = {
    "brokers": "reducequeue:61613",
    "amq_queues": ["/queue/ReductionPending"],
    "amq_user": "autoreduce",
    "amq_pwd": "YOUR-PASSWORD",
    "postprocess_error": "/queue/ReductionError",
    "reduction_started": "/queue/ReductionStarted",
    "reduction_complete": "/queue/ReductionComplete",
    "reduction_error": "/queue/ReductionError"
}
