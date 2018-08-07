"""
Common helper functions for templatetags
"""
from django.template import VariableDoesNotExist


def get_var(variable, context):
    """
    Obtain a variable from the context
    """
    try:
        return variable.resolve(context)
    except VariableDoesNotExist:
        return variable.var
