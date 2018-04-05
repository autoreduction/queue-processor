"""
Common helper functions for templatetags
"""
from django.template import VariableDoesNotExist


def get_var(v, context):
    """
    Obtain a variable from the context
    """
    try:
        return v.resolve(context)
    except VariableDoesNotExist:
        return v.var
