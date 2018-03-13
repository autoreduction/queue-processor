# ActiveMQ
ACTIVEMQ = {
    "host": "reducequeue",
    "queues": ["ReductionPending", "ReductionError"],
    "username": "YOUR-ACTIVEMQ-USERNAME",
    "password": "YOUR-ACTIVEMQ-PASSWORD",
    "api-path": ":8161/api/jolokia/read/org.apache.activemq:type=Broker,brokerName=localhost,destinationType=Queue"
}

MYSQL = {
    "host" : "reducequeue",
    "username" : "YOUR-MYSQL-USERNAME",
    "password" : "YOUR-MYSQL-USERNAME",
    "db" : "autoreduction"
}

ISIS_MOUNT  = 'Z:\\'
