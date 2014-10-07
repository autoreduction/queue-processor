from settings import LOG_FILE, LOG_LEVEL, UOWS_URL
import logging
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)
from suds.client import Client
import suds

class UOWSClient(object):
    def __init__(self, **kwargs):
        url = UOWS_URL
        if 'URL' in kwargs:
            url = kwargs['URL']
        self.client = Client(url)

    # Add the ability to use 'with'
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        pass

    def check_session(self, session_id):
        try:
            return self.client.service.checkSession(session_id)
        except suds.WebFault:
            logging.warn("Session ID is not valid: %s" % session_id)
            return False

    def get_person(self, session_id):
        try:
            person = self.client.service.getPersonDetailsFromSessionId(session_id)
            if person:
                first_name = person.givenName
                if not first_name:
                    first_name = person.firstNameKnownAs
                trimmed_person = {
                    'first_name' : first_name,
                    'last_name' : person.familyName,
                    'email' : person.email,
                    'usernumber' : person.userNumber
                }
                return trimmed_person
        except suds.WebFault:
            logging.warn("Session ID is not valid: %s" % session_id)
        return None

    def logout(self, session_id):
        try:
            self.client.service.logout(session_id)
        except suds.WebFault:
            logging.warn("Failed to logout Session ID %s" % session_id)