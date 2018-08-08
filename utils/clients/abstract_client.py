"""
Generic client class used as an interface for other classes
"""
from abc import ABCMeta, abstractmethod

from utils.clients.settings.client_settings import ClientSettings


class AbstractClient:
    __metaclass__ = ABCMeta

    credentials = None

    def __init__(self, credentials):
        if not isinstance(credentials, ClientSettings):
            raise TypeError("Expected instance of ClientSettings not {}".
                            format(type(credentials)))
        self.credentials = credentials

    @abstractmethod
    def connect(self): raise NotImplementedError

    @abstractmethod
    def disconnect(self): raise NotImplementedError

    @abstractmethod
    def _test_connection(self): raise NotImplementedError
