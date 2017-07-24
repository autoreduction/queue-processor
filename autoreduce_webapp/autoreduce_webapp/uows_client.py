import suds
import ssl
import logging
from settings import CERTIFICATE_LOCATION
from suds.client import Client
from suds.transport.https import HttpAuthenticated
from urllib2 import HTTPSHandler
from settings import UOWS_URL
logger = logging.getLogger(__name__)


class CustomTransport(HttpAuthenticated):
    def u2handlers(self):
        # use handlers from superclass
        handlers = HttpAuthenticated.u2handlers(self)
        # create custom ssl context, e.g.
        ctx = ssl.create_default_context(cafile=CERTIFICATE_LOCATION)
        # configure context as needed...
        ctx.check_hostname = False

        # add a https handler using the custom context
        handlers.append(HTTPSHandler(context=ctx))
        return handlers


class UOWSClient(object):
    """
    A client for interacting with the User Office Web Service
    """
    def __init__(self, **kwargs):
        url = UOWS_URL
        if 'URL' in kwargs:
            url = kwargs['URL']
        self.client = Client(url, transport=CustomTransport())

    # Add the ability to use 'with'
    def __enter__(self):
        return self

    def __exit__(self, exit_type, value, traceback):
        pass

    def check_session(self, session_id):
        """
        Checks if a session ID is still active and valid
        """
        try:
            return self.client.service.checkSession(session_id)
        except suds.WebFault:
            logger.warn("Session ID is not valid: %s" % session_id)
            return False

    def get_person(self, session_id):
        """
        Returns a dictionary containing basic person details for the user associated with the session id.
        Values include, first name, last name, email and unique usernumber.
        If session_id isn't valid, None is returned.
        """
        try:
            person = self.client.service.getPersonDetailsFromSessionId(session_id)
            if person:
                first_name = person.givenName
                if not first_name:
                    first_name = person.firstNameKnownAs
                trimmed_person = {
                    'first_name': first_name,
                    'last_name': person.familyName,
                    'email': person.email,
                    'usernumber': person.userNumber
                }
                return trimmed_person
        except suds.WebFault:
            logger.warn("Session ID is not valid: %s" % session_id)
        return None

    def logout(self, session_id):
        """
        Ends the session within the User Office Web Service.
        Note: This doesn't kill the local session.
        """
        try:
            self.client.service.logout(session_id)
        except suds.WebFault:
            logger.warn("Failed to logout Session ID %s" % session_id)
