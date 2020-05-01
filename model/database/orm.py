import os
import sys
import logging

import django
from django.conf import settings

from utils.project.structure import get_project_root


class DjangoORM:

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
        """
        try:
            from WebApp.autoreduce_webapp.autoreduce_webapp.settings import DATABASES, ORM_INSTALL
            settings.configure(
                DATABASES=DATABASES,
                INSTALLED_APPS=ORM_INSTALL,
            )
            django.setup()
        except RuntimeError as excep:
            logging.warning("Exception raised when attempting to setup: %s", excep)

    def _get_data_model(self):
        """
        Encapsulate the importing of the ORM objects that relate to the
        data passing through the system from django models
        """
        if not self.data_model:
            import reduction_viewer.models as data_model
            self.data_model = data_model
        return self.data_model

    def _get_variable_model(self):
        """
        Encapsulate the importing of the ORM objects that relate to the
        data passing through the system from django models
        """
        if not self.variable_model:
            import reduction_variables.models as variable_model
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
        except:
            return False
        return True
