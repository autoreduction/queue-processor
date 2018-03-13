#! /usr/bin/env python
from autoreduce_settings import ACTIVEMQ
import requests
from requests.auth import HTTPBasicAuth
import sys

'''
Check the number of consumer for the list is atleast 1
'''

activemq_url = "http://"+ ACTIVEMQ['host'] + ACTIVEMQ['api-path'] 
activemq_auth = HTTPBasicAuth(ACTIVEMQ['username'], ACTIVEMQ['password'])

def checkConsumer():
    for queue in ACTIVEMQ['queues']:
        r = requests.get(activemq_url + ",destinationName=" + queue + "/ConsumerCount", auth=activemq_auth)
        
        consumer_count = r.json()['value']
        #print(queue + " consumerCount = " + str(r.json()['value']))
        
        if(consumer_count < 1):
            print("No consumers for  " + str(queue))
            return 2
    return 0
    
if "__name__":
    sys.exit(checkConsumer())