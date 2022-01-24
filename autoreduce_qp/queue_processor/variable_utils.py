# ############################################################################ #
# Autoreduction Repository :
# https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################ #
"""Class to deal with reduction run variables."""
import logging
import traceback

from autoreduce_qp.queue_processor.reduction.service import ReductionScript

logger = logging.getLogger(__file__)


class VariableUtils:

    @staticmethod
    def get_default_variables(instrument_name, raise_exc=False) -> dict:
        """
        Load the variables from the reduction script on disk for the instrument.

        Args:
            instrument_name: The name of the instrument to get the variables for
            raise_exc: If True, re-raise any exception encountered while getting
            the variables. Some callers may want to catch the exception and
            handle it differently, e.g. show an error message to the user.

        Returns:
            A dictionary of variables for the instrument.

        Raises (if raise_exc=True):
            FileNotFoundError: If file not found.
            ImportError: If something cannot be imported.
            SyntaxError: If a syntax error is encountered.

        Raises (if raise_exc=False):
            Exception: If any other uncaught error is raised.
        """
        arguments = {
            "standard_vars": {},
            "advanced_vars": {},
            "variable_help": {
                "standard_vars": {},
                "advanced_vars": {},
            }
        }
        reduce_vars = ReductionScript(instrument_name, script_path=None, module='reduce_vars.py')

        try:
            module = reduce_vars.load()

            for dict_name in ["standard_vars", "advanced_vars", "variable_help"]:
                if hasattr(module, dict_name):
                    arguments[dict_name] = getattr(module, dict_name)
        except (FileNotFoundError, ImportError, SyntaxError):
            if not raise_exc:
                logger.error(traceback.format_exc())
            else:
                raise
        except Exception:
            logger.error(traceback.format_exc())
            raise

        return arguments
