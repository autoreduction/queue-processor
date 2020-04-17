# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
""" Represents the messages passed between AMQ queues"""
import json


class Message:

    def __init__(self, serialised_object=None, overwrite=True):
        """
        If a serialised object is supplied then the class will be populated
        :param serialised_object: a serialised json object (json.dumps)
        :param overwrite: Should we overwrite existing variables?
        """
        self.description = None
        self.facility = None
        self.run_number = None
        self.instrument = None
        self.rb_number = None
        self.started_by = None
        self.file_path = None
        self.overwrite = None
        self.run_version = None
        self.job_id = None
        self.reduction_script = None
        self.reduction_arguments = None
        self.reduction_log = None
        self.admin_log = None
        self.return_message = None
        self.retry_in = None
        if serialised_object:
            self.un_serialise(serialised_object, overwrite)

    def to_dict(self):
        """
        Create a dictionary of all the class member variables
        :return: member variables dictionary
        """
        return {key: value for key, value in self.__dict__.items()
                if not key.startswith('__') and not callable(key)}

    def serialise(self):
        """
        serialised member variables as a json dump
        :return: json dump of a dictionary representing the member variables
        """
        return json.dumps(self.to_dict())

    def un_serialise(self, serialised_object, overwrite=True):
        """
        un serialise an object and use its values to populate member variables in this class
        :param serialised_object: The object to un-serialise
        :param overwrite: Should we overwrite any existing variables?
        """
        un_serialised_dict = json.loads(serialised_object)
        self_dict = self.to_dict()
        for key, value in un_serialised_dict.items():
            if key in self_dict.keys():
                current_value = self_dict[key]
                if overwrite or current_value is None:
                    # Set the value of the variable on this object accessing it by name
                    setattr(self, key, value)
