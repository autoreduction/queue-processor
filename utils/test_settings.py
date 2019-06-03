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

from utils.clients.settings.client_settings_factory import ClientSettingsFactory


VALID_INSTRUMENTS = ['GEM', 'POLARIS', 'WISH', 'OSIRIS', 'MUSR', 'POLREF']

SETTINGS_FACTORY = ClientSettingsFactory()

ICAT_SETTINGS = SETTINGS_FACTORY.create('icat',
                                        username='YOUR-ICAT-USERNAME',
                                        password='YOUR-PASSWORD',
                                        host='YOUR-ICAT-WSDL-URL',
                                        port='',
                                        authentication_type='simple')

MYSQL_SETTINGS = SETTINGS_FACTORY.create('database',
                                         username='test-user',
                                         password='pass',
                                         host='localhost',
                                         port='3306',
                                         database_name='autoreduction')

ACTIVEMQ_SETTINGS = SETTINGS_FACTORY.create('queue',
                                            username='admin',
                                            password='admin',
                                            host='127.0.1.1',
                                            port='61613')
