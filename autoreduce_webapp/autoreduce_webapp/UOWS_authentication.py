from autoreduce_webapp.uows_client import UOWSClient
from django.conf import settings
from django.contrib.auth.models import User

class UOWSAuthenticationBackened(object):
    def authenticate(self, token=None):
        with UOWSClient() as client:
            if client.check_session(token):
                person = client.get_person(token)
                try:
                    user = User.objects.get(username=person['usernumber'])
                except User.DoesNotExist:
                    user = User(username=person['usernumber'], password='get from uows', first_name=person['first_name'], last_name=person['last_name'], email=person['email'])
                    user.save()
                return user

        return None