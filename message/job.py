# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
""" Represents the messages passed between AMQ queues"""
import json
import attr


# pylint:disable=too-many-instance-attributes
@attr.s
class Message:
    """
    A class that represents an AMQ Message, these can be both serialised and un-serialised
    for sending messages to and from AMQ
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

    def serialise(self):
        """
        serialised member variables as a json dump
        :return: json dump of a dictionary representing the member variables
        """
        return json.dumps(attr.asdict(self))

    def un_serialise(self, serialised_object, overwrite=True):
        """
        un serialise an object and use its values to populate member variables in this class
        :param serialised_object: The object to un-serialise
        :param overwrite: Should we overwrite any existing variables?
        """
        un_serialised_dict = json.loads(serialised_object)
        self_dict = attr.asdict(self)
        for key, value in un_serialised_dict.items():
            if key in self_dict.keys():
                current_value = self_dict[key]
                if overwrite or current_value is None:
                    # Set the value of the variable on this object accessing it by name
                    setattr(self, key, value)
