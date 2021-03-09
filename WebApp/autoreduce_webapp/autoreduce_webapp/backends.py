# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
UOWS authentication backend
"""
import logging

from django.contrib.auth.models import User

from .icat_cache import ICATCache
from .uows_client import UOWSClient

LOGGER = logging.getLogger('app')


class UOWSAuthenticationBackend:
    """
    Custom authentication for use with the User Office Web Service
    """
    @staticmethod
    def authenticate(request, token=None):
        """
        Checks that the given session ID (token) is still valid and
        returns an appropriate user object.
        If this is the first time a user has logged in a new user object is created.
        A users permissions (staff/superuser) is also set based on calls to ICAT.
        """
        with UOWSClient() as client:
            if client.check_session(token):
                person = client.get_person(token)
                try:
                    user = User.objects.get(username=person['usernumber'])
                # pylint: disable=no-member
                except User.DoesNotExist:
                    user = User(username=person['usernumber'],
                                password='get from uows',
                                first_name=person['first_name'],
                                last_name=person['last_name'],
                                email=person['email'])

                with ICATCache() as icat:
                    # Make sure user has correct permissions set.
                    # This will be checked upon each login
                    # pylint: disable=no-member
                    user.is_superuser = icat.is_admin(int(person['usernumber']))
                    user.is_staff = (icat.is_instrument_scientist(int(person['usernumber'])) or user.is_superuser)
                user.save()
                return user
        return None

    @staticmethod
    def get_user(user_id):
        """
        Static function to return the user from user_id
        """
        try:
            # pylint: disable=no-member
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
