# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Functions for comparing database objects
"""
import copy


# pylint:disable=protected-access
def compare_db_objects(first, second):
    """
    Compare to database objects defined by SQLAlchemy ORM mapping
    :param first: first object to compare
    :param second: second object to compare
    :return: True if objects match, else False
    """
    # Assert classes match
    classes_match = isinstance(first, second.__class__)
    first_dict = copy.deepcopy(first._sa_instance_state.dict)
    first_dict.pop('_sa_instance_state', None)
    second_dict = copy.deepcopy(second._sa_instance_state.dict)
    second_dict.pop('_sa_instance_state', None)
    # Assert dict values match
    attrs_match = first_dict == second_dict
    return attrs_match and classes_match
