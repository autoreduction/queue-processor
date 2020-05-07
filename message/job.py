# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Represents the messages passed between AMQ queues
"""
import json
import logging

import attr

from utils.project.static_content import LOG_FORMAT
from utils.project.structure import get_log_file

logging.basicConfig(filename=get_log_file('job.log'), level=logging.INFO,
                    format=LOG_FORMAT)

# pylint:disable=too-many-instance-attributes
@attr.s
class Message:
    """
    A class that represents an AMQ Message.
    Messages can be serialized and deserialized for sending messages to and from AMQ
    """
    description = attr.ib(default=None)
    facility = attr.ib(default=None)
    run_number = attr.ib(default=None)
    instrument = attr.ib(default=None)
    rb_number = attr.ib(default=None)
    started_by = attr.ib(default=None)
    file_path = attr.ib(default=None)
    overwrite = attr.ib(default=None)
    run_version = attr.ib(default=None)
    job_id = attr.ib(default=None)
    reduction_script = attr.ib(default=None)
    reduction_arguments = attr.ib(default=None)
    reduction_log = attr.ib(default=None)
    admin_log = attr.ib(default=None)
    return_message = attr.ib(default=None)
    retry_in = attr.ib(default=None)

    # Note: added indent to allow pretty-printing
    #   Although I can work around needing this if not appropriate to have as argument
    def serialize(self, indent=None):
        """
        Serialized member variables as a json dump
        :return: JSON dump of a dictionary representing the member variables
        """
        return json.dumps(attr.asdict(self), indent=indent)

    @staticmethod
    def deserialize(serialized_object):
        """
        Deserialize an object and return a dictionary of that object
        :param serialized_object: The object to deserialize
        :return: Dictionary of deserialized object
        """
        return json.loads(serialized_object)

    def populate(self, source, overwrite=True):
        """
        Populate the class from either a serialised object or a dictionary optionally retaining
        or overwriting existing values of attributes
        :param source: Object to populate class from
        :param overwrite: If True, overwrite existing values of attributes
        """
        if isinstance(source, str):
            try:
                source = self.deserialize(source)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Unable to recognise serialized object {source}")

        self_dict = attr.asdict(self)
        for key, value in source.items():
            if key in self_dict.keys():
                self_value = self_dict[key]
                if overwrite or self_value is None:
                    # Set the value of the variable on this object accessing it by name
                    setattr(self, key, value)
            else:
                warning_message = (f"Unexpected key encountered during Message population: '{key}'."
                                   f"Skipping this key...")
                logging.warning(warning_message)
                print(warning_message)  # Note: for debug purposes
