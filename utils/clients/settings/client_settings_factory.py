# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Factory for creating settings objects that can be used in the client classes
"""
# pylint: disable=fixme
from utils.clients.settings.client_settings import ClientSettings


# pylint:disable=too-few-public-methods
class ClientSettingsFactory:
    """
    Class for the settings factory
    """

    ignore_kwargs = ['username', 'password', 'host', 'port']
    valid_types = ['database', 'icat', 'queue', 'sftp', 'cycle']

    # pylint:disable=too-many-arguments
    def create(self, settings_type, username, password, host, port, **kwargs):
        """
        Create a settings object to use with a client
        :param settings_type: The type of client you require this can be: database, icat or queue
        :param username: username for logon
        :param password: password for logon
        :param host: host address for service
        :param port: port on the host machine where the service is running
        :param kwargs: key word arguments used for specific classes
                       Database specific args : database_name
                       ICAT specific args     : authentication_type
                       Queue specific args    : reduction_pending, data_ready, reduction_started
                                                reduction_complete, reduction_error
        :return: A ClientSettings object
        """
        if settings_type.lower() not in self.valid_types:
            raise ValueError(f"Factories creation settings type must be one of:" f"{','.join(self.valid_types)}")
        kwargs['username'] = username
        kwargs['password'] = password
        kwargs['host'] = host
        kwargs['port'] = port

        settings = None
        if settings_type.lower() == 'database':
            settings = self._create_database(**kwargs)
        elif settings_type.lower() == 'icat':
            settings = self._create_icat(**kwargs)
        elif settings_type.lower() == 'queue':
            settings = self._create_queue(**kwargs)
        elif settings_type.lower() == 'sftp':
            settings = self._create_sftp(**kwargs)
        elif settings_type.lower() == 'cycle':
            settings = self._create_cycle(**kwargs)
        return settings

    def _create_database(self, **kwargs):
        """
        :return: Database compatible settings object
        """
        database_kwargs = ['database_name']
        self._test_kwargs(database_kwargs, kwargs)
        return MySQLSettings(**kwargs)

    def _create_queue(self, **kwargs):
        """
        :return: Queue compatible settings object
        """
        queue_kwargs = ['data_ready']
        self._test_kwargs(queue_kwargs, kwargs)
        return ActiveMQSettings(**kwargs)

    def _create_icat(self, **kwargs):
        """
        :return: Icat compatible settings object
        """
        icat_kwargs = ['authentication_type']
        self._test_kwargs(icat_kwargs, kwargs)
        return ICATSettings(**kwargs)

    def _create_sftp(self, **kwargs):
        """
        :return: SFTP compatible settings object
        """
        sftp_kwargs = []  # No additional kwargs needed for sftp
        self._test_kwargs(sftp_kwargs, kwargs)
        return SFTPSettings(**kwargs)

    def _create_cycle(self, **kwargs):
        """
        :return: cycle-ingestion compatible settings object
        """
        cycle_kwargs = ['uows_url', 'scheduler_url']
        self._test_kwargs(cycle_kwargs, kwargs)
        return CycleIngestionSettings(**kwargs)

    def _test_kwargs(self, expected, actual):
        """
        Ensure that the kwargs given as input contain the expected keys
        """
        for key, _ in actual.items():
            if key not in expected and key not in self.ignore_kwargs:
                raise ValueError("{0} is not a recognised key word argument."
                                 " Valid kwargs: {1}".format(key, expected))


# pylint:disable=too-few-public-methods
class ICATSettings(ClientSettings):
    """
    ICAT settings object
    """
    auth = None

    def __init__(self, authentication_type='Simple', **kwargs):
        super(ICATSettings, self).__init__(**kwargs)  # pylint:disable=super-with-arguments
        self.auth = authentication_type


# pylint:disable=too-few-public-methods
class MySQLSettings(ClientSettings):
    """
    MySQL settings to be used as a Database settings object
    """
    database = None

    def __init__(self, database_name='autoreduction', **kwargs):
        super(MySQLSettings, self).__init__(**kwargs)  # pylint:disable=super-with-arguments
        self.database = database_name

    def get_full_connection_string(self):
        """ :return: string for connecting directly to mysql service with user + pass """
        return 'mysql+mysqldb://{0}:{1}@{2}/{3}'.format(self.username, self.password, self.host, self.database)


# pylint:disable=too-few-public-methods
class ActiveMQSettings(ClientSettings):
    """
    ActiveMq settings to be used as a Queue settings object
    """
    data_ready = None
    all_subscriptions = None

    # pylint:disable=too-many-arguments
    def __init__(self, data_ready='/queue/DataReady', **kwargs):
        # TODO explicitly state args
        super(ActiveMQSettings, self).__init__(**kwargs)  # pylint:disable=super-with-arguments

        self.data_ready = data_ready
        self.all_subscriptions = [data_ready]


class SFTPSettings(ClientSettings):
    """
    SFTP settings object
    """
    def __init__(self, **kwargs):  # pylint:disable=useless-super-delegation
        super(SFTPSettings, self).__init__(**kwargs)  # pylint:disable=super-with-arguments


class CycleIngestionSettings(ClientSettings):
    """
    Cycle-ingestion settings object
    """
    uows_url = None
    scheduler_url = None

    # pylint:disable=super-with-arguments
    def __init__(self, uows_url, scheduler_url, **kwargs):
        super(CycleIngestionSettings, self).__init__(**kwargs)
        self.uows_url = uows_url
        self.scheduler_url = scheduler_url
