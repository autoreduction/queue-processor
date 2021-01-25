# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
import os
from unittest.mock import Mock, patch
from queue_processors.queue_processor.queueproc_utils.script_utils import import_module
from queue_processors.queue_processor.queueproc_utils.tests.module_to_import import TEST_DICTIONARY


def assert_raises(exc, func, args):
    """
    Custom assert raises function
    """
    try:
        func(args)
    except Exception as actual_exc:  # pylint:disable=broad-except
        assert isinstance(actual_exc, exc), f"Expected exception {exc}, got {actual_exc}"


def test_import_module():
    """
    Test importing a module that is all OK
    """
    module_path = os.path.join(os.path.dirname(__file__), "module_to_import.py")
    module = import_module(module_path)

    assert getattr(module, "TEST_DICTIONARY") == TEST_DICTIONARY


@patch("queue_processors.queue_processor.queueproc_utils.script_utils.log_error_and_notify")
def test_import_module_invalid_module(log_error_and_notify: Mock):
    """
    Test importing a module that does not exist
    """
    assert_raises(ImportError, import_module, "some.module.that.does.not.exist")
    log_error_and_notify.assert_called_once()


@patch("queue_processors.queue_processor.queueproc_utils.script_utils.log_error_and_notify")
def test_import_module_syntax_error(log_error_and_notify: Mock):
    """
    Test importing a module that has a syntax error in it
    """
    module_path = os.path.join(os.path.dirname(__file__), "module_with_syntax_error.py")

    assert_raises(SyntaxError, import_module, module_path)

    log_error_and_notify.assert_called_once()
