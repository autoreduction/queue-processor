# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
A class responsible for creating a light weight django instance to
access the Django ORM that defines the autoreduction database
"""
import os
import sys
import logging

import django
from django.conf import settings
from django.db import close_old_connections, connection

from queue_processor.settings import PROJECT_ROOT

# pylint:disable=no-member


class DjangoORM:
    """
    Encapsulate Django setup and ORM access in a class
    This should normally be used like the following:
    orm = DjangoORM
    orm.connect()
    records = orm.data_model.<TableName>.objects.<Filter/OrderBy/..>
    """

    data_model = None
    variable_model = None

    @staticmethod
    def add_webapp_path():
        """
        Get path to the autoreduce_webapp and add this path to the system path
        This will enable importing of the autoreduce_webapp (and it's models)
        """
        path = os.path.join(PROJECT_ROOT, 'WebApp', 'autoreduce_webapp')
        if path not in sys.path:
            sys.path.append(path)

    @staticmethod
    def remove_old_db_connections():
        """
        Remove expired database connections. The connections can expire on both ends:
        - on the QP after the value of CONN_MAX_AGE
        - on the DB server (MySQL specifically) after the value of `wait_timeout` (which by default is 8 hours)

        `connection.connection` is None means there hasn't been a connection to the DB before.
        """
        if connection.connection and not connection.is_usable():
            # destroy the default mysql connection
            # after this line, when you use ORM methods
            # django will reconnect to the default mysql
            close_old_connections()

    @staticmethod
    def setup_django():
        """
        Use the WebApp settings to initialise a django instance that can be used for model access
        This should always be called before any other function
        """
        try:
            # import here to avoid failure without calling add_webapp_path first
            # pylint:disable=import-outside-toplevel
            from autoreduce_db.autoreduce_db.settings import DATABASES
            if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
                DATABASES["default"]["NAME"] = f'{PROJECT_ROOT}/sqlite3.db'

            if not settings.configured:
                settings.configure(
                    DATABASES=DATABASES,
                    INSTALLED_APPS=[
                        "autoreduce_db.reduction_viewer",
                        "autoreduce_db.instrument",
                    ],
                )
                django.setup()

            if DATABASES["default"]["ENGINE"] == "django.db.backends.mysql":
                DjangoORM.remove_old_db_connections()
        except RuntimeError as excep:
            logging.warning("Exception raised when attempting to setup: %s", excep)

    def _get_data_model(self):
        """
        Importing the ORM objects for reduction data
        """
        if not self.data_model:
            # pylint:disable=import-outside-toplevel,import-error
            import autoreduce_db.reduction_viewer.models as data_model
            self.data_model = data_model
        return self.data_model

    def _get_variable_model(self):
        """
        Import the ORM objects for reduction variables
        """
        if not self.variable_model:
            # pylint:disable=import-outside-toplevel,import-error
            import autoreduce_db.instrument.models as variable_model
            self.variable_model = variable_model
        return self.variable_model

    def connect(self):
        """
        Control function to actually perform the setup of the django ORM connection
        :return: (bool) was the setup successful?
        """
        self.add_webapp_path()
        self.setup_django()
        try:
            if not self.data_model:
                self._get_data_model()
            self.data_model.Instrument.objects.first()
            if not self.variable_model:
                self._get_variable_model()
            self.variable_model.Variable.objects.first()
        # Bare accept here as we want to catch any form of exception
        # (and there could be multiple different ones from the above code)
        # pylint:disable=bare-except
        except:
            return False
        return True
