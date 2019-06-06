# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint: skip-file
"""
Settings for connecting to the test services that run locally
"""
import configparser
from utils.clients.settings.client_settings_factory import ClientSettingsFactory


VALID_INSTRUMENTS = ['GEM', 'POLARIS', 'WISH', 'OSIRIS', 'MUSR', 'POLREF']


CONFIG = configparser.ConfigParser()
SETTINGS_FACTORY = ClientSettingsFactory()

ICAT_SETTINGS = SETTINGS_FACTORY.create('icat',
                                        username=CONFIG.get('ICAT', 'user'),
                                        password=CONFIG.get('ICAT', 'password'),
                                        host=CONFIG.get('ICAT', 'host'),
                                        port='',
                                        authentication_type=CONFIG.get('ICAT', 'auth'))

MYSQL_SETTINGS = SETTINGS_FACTORY.create('database',
                                         username=CONFIG.get('DATABASE', 'user'),
                                         password=CONFIG.get('DATABASE', 'password'),
                                         host=CONFIG.get('DATABASE', 'host'),
                                         port=CONFIG.get('DATABASE', 'port'),
                                         database_name=CONFIG.get('DATABASE', 'name'))

ACTIVEMQ_SETTINGS = SETTINGS_FACTORY.create('queue',
                                            username=CONFIG.get('QUEUE', 'user'),
                                            password=CONFIG.get('QUEUE', 'password'),
                                            host=CONFIG.get('QUEUE', 'host'),
                                            port=CONFIG.get('QUEUE', 'port'))
