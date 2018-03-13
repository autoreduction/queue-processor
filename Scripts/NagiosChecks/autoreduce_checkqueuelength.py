#! /usr/bin/env python
from autoreduce_settings import ACTIVEMQ
import requests
from requests.auth import HTTPBasicAuth
import sys

'''
Check the length of the queues
'''

activemq_url = "http://"+ ACTIVEMQ['host'] + ACTIVEMQ['api-path'] 
activemq_auth = HTTPBasicAuth(ACTIVEMQ['username'], ACTIVEMQ['password'])

def checkQueueLength(warning, critical):
    for queue in ACTIVEMQ['queues']:
        r = requests.get(activemq_url + ",destinationName=" + queue + "/QueueSize", auth=activemq_auth)
        
        queue_length = r.json()['value']
        #print(queue + " length = " + str(queue_length))
        
        if(queue_length > warning):
            print(queue + " queue getting big " + str(queue_length))
            return 1
        if(queue_length > warning):
            print(queue + " queue length is critical " + str(queue_length))
            return 2
    return 0
    
    
if "__name__":
    sys.exit(checkQueueLength(3, 10))