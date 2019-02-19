# pylint: skip-file
import os
import logging.handlers

from utils.project.structure import get_project_root


LOGGING_LEVEL = logging.INFO
LOGGING_LOC = os.path.join(get_project_root(), 'logs', 'autoreductionProcessor.log')

logger = logging.getLogger('AutoreductionProcessor')
logger.setLevel(LOGGING_LEVEL)
handler = logging.handlers.RotatingFileHandler(LOGGING_LOC, maxBytes=104857600, backupCount=20)
handler.setLevel(LOGGING_LEVEL)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
# Quiet the Stomp logs as they are quite chatty
logging.getLogger('stomp').setLevel(logging.INFO)
