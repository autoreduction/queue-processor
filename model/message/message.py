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

import attr

from model.message.validation import stages


# pylint:disable=too-many-instance-attributes
@attr.s
class Message:
    """
    A class that represents an AMQ Message.
    Messages can be serialized and deserialized for sending messages to and from AMQ
    """
    description = attr.ib(default=None)
    facility = attr.ib(default="ISIS")
    run_number = attr.ib(default=None)
    instrument = attr.ib(default=None)
    rb_number = attr.ib(default=None)
    started_by = attr.ib(default=None)
    data = attr.ib(default=None)
    overwrite = attr.ib(default=None)
    run_version = attr.ib(default=None)
    job_id = attr.ib(default=None)
    reduction_script = attr.ib(default=None)
    reduction_arguments = attr.ib(default=None)
    reduction_log = attr.ib(default="")  # Cannot be null in database
    admin_log = attr.ib(default="")  # Cannot be null in database
    message = attr.ib(default=None)
    retry_in = attr.ib(default=None)
    reduction_data = attr.ib(default=None)  # Required by reduction runner
    software = attr.ib(default=None)

    def serialize(self, indent=None, limit_reduction_script=False):
        """
        Serialized member variables as a json dump
        :param indent: The indent level passed to json.dumps
        :param limit_reduction_script: if True, limits reduction_script to 50 chars in return
        :return: JSON dump of a dictionary representing the member variables
        """
        data_dict = attr.asdict(self)
        if limit_reduction_script:
            data_dict["reduction_script"] = data_dict["reduction_script"][:50]

        return json.dumps(data_dict, indent=indent)

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
            except json.decoder.JSONDecodeError as exp:
                raise ValueError(f"Unable to recognise serialized object {source}") from exp

        self_dict = attr.asdict(self)
        for key, value in source.items():
            if key in self_dict.keys():
                self_value = self_dict[key]
                if overwrite or self_value is None:
                    # Set the value of the variable on this object accessing it by name
                    setattr(self, key, value)
            else:
                raise ValueError("Unexpected key encountered during Message population: '{key}'.")

    def validate(self, destination):
        """
        Ensure that the message is valid to be sent to a given destination queue
        :param destination: (str) The name of the queue to send the data to
        """
        if destination == '/queue/DataReady':
            try:
                stages.validate_data_ready(self)
            except RuntimeError as err:
                raise RuntimeError(f"Message was not valid for queue {destination}.") from err
