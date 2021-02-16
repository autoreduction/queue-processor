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

from utils.project.structure import get_project_root


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
        path = os.path.join(get_project_root(), 'WebApp', 'autoreduce_webapp')
        if path not in sys.path:
            sys.path.append(path)

    @staticmethod
    def setup_django():
        """
        Use the WebApp settings to initialise a django instance that can be used for model access
        This should always be called before any other function
        """
        try:
            # import here to avoid failure without calling add_webapp_path first
            # pylint:disable=import-outside-toplevel
            from WebApp.autoreduce_webapp.autoreduce_webapp.settings import DATABASES, ORM_INSTALL
            if not settings.configured:
                settings.configure(
                    DATABASES=DATABASES,
                    INSTALLED_APPS=ORM_INSTALL,
                )
                django.setup()
        except RuntimeError as excep:
            logging.warning("Exception raised when attempting to setup: %s", excep)

    def _get_data_model(self):
        """
        Importing the ORM objects for reduction data
        """
        if not self.data_model:
            # pylint:disable=import-outside-toplevel,import-error
            import reduction_viewer.models as data_model
            self.data_model = data_model
        return self.data_model

    def _get_variable_model(self):
        """
        Import the ORM objects for reduction variables
        """
        if not self.variable_model:
            # pylint:disable=import-outside-toplevel,import-error
            import instrument.models as variable_model
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
