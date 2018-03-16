import logging.config
from settings import LOGGING
from orm_mapping import *
from base import session

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")


class InstrumentUtils(object):
    @staticmethod
    def get_instrument(instrument_name):
        """
        Helper method that will try to get an instrument matching the given name or create one if it doesn't yet exist
        """
        instrument = session.query(Instrument).filter_by(name=instrument_name).first()
        if instrument is None:
            instrument = Instrument(name=instrument_name, is_active=1, is_paused=0)
            session.add(instrument)
            session.commit()
            logger.warn("%s instrument was not found, created it." % instrument_name)
        return instrument
