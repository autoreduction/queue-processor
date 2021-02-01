# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
import os
from unittest.mock import Mock, patch

import pytest
from queue_processors.queue_processor.utils.script_utils import import_module
from queue_processors.queue_processor.utils.tests.module_to_import import TEST_DICTIONARY


def test_import_module():
    """
    Test importing a module that is all OK
    """
    module_path = os.path.join(os.path.dirname(__file__), "module_to_import.py")
    module = import_module(module_path)

    assert getattr(module, "TEST_DICTIONARY") == TEST_DICTIONARY


@patch("queue_processors.queue_processor.utils.script_utils.log_error_and_notify")
def test_import_module_invalid_module(log_error_and_notify: Mock):
    """
    Test importing a module that does not exist
    """
    with pytest.raises(ImportError):
        import_module("some.module.that.does.not.exist")
    log_error_and_notify.assert_called_once()


@patch("queue_processors.queue_processor.utils.script_utils.log_error_and_notify")
def test_import_module_syntax_error(log_error_and_notify: Mock):
    """
    Test importing a module that has a syntax error in it
    """
    module_with_syntax_error_str = """TEST_DICTIONARY = {"key1": "value1"""
    module_path = os.path.join("/tmp", "module_with_syntax_error.py")

    with open(module_path, 'w') as file:
        file.write(module_with_syntax_error_str)

    with pytest.raises(SyntaxError):
        import_module(module_path)

    log_error_and_notify.assert_called_once()
    os.remove(module_path)
