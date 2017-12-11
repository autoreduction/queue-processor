
LOG_FILENAME = 'test_logging.out'

# ActiveMQ 

ACTIVEMQ = {
    'username' : 'autoreduce',
    'password' : 'password',
    'broker' : [("autoreduce.isis.cclrc.ac.uk", 61613)],
    'SSL' : False
}

# ICAT 

ICAT = {
    'AUTH' : 'simple',
    'URL' : 'https://icatdev.isis.cclrc.ac.uk/ICATService/ICAT?wsdl',
    'USER' : 'autoreduce',
    'PASSWORD' : 'icat'
}

# UserOffice WebService

UOWS_URL = 'https://fitbawebdev.isis.cclrc.ac.uk:8181/UserOfficeWebService/UserOfficeWebService?wsdl'
UOWS_LOGIN_URL = 'https://devusers.facilities.rl.ac.uk/auth/?service=http://datareducedev.isis.cclrc.ac.uk&redirecturl='
