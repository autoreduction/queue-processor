"""
Queue Configuration 
"""
import logging
import json
import os


class StreamToLogger(object):
    # Fake file-like stream object that redirects writes to a logger instance.
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''
 
    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())
        
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(process)d/%(threadName)s: %(message)s",
    filename='/var/log/mantid_autoreduce_worker.log',
    filemode='a'
)


class Configuration(object):
    """
        Read and process configuration file and provide an easy way to create a configured Client object
    """
    def __init__(self, config_file):
                    
        if not os.access(config_file, os.R_OK):
            logging.error("Configuration file doesn't exist or is not readable.")
            raise ValueError
        
        try:
            logging.info("Found configuration file at: %s" % config_file)
            cfg = open(config_file, 'r')
            json_encoded = cfg.read()           
            config = json.loads(json_encoded)
            self.amq_user = config['amq_user']
            self.amq_pwd = config['amq_pwd']
            self.brokers = config['brokers']
            self.queues = config['amq_queues']
            self.postprocess_error = config['postprocess_error']
            self.catalog_started = config['catalog_started']
            self.catalog_complete = config['catalog_complete']
            self.catalog_error = config['catalog_error']
            self.reduction_started = config['reduction_started']
            self.reduction_complete = config['reduction_complete']
            self.reduction_error = config['reduction_error']
            self.reduction_disabled = config['reduction_disabled']
            self.reduction_catalog_started = config['reduction_catalog_started']
            self.reduction_catalog_complete = config['reduction_catalog_complete']
            self.reduction_catalog_error = config['reduction_catalog_error']
            self.heart_beat = config['heart_beat']
            
        except Exception:
            logging.info('Failed to read configuration file', exc_info=True)
            raise ValueError
