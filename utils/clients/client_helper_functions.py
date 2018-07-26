"""
Same helper functions for the client classes
"""


def use_default_if_none(input_var, default):
    """
    :param input_var: Input to the class (could be None)
    :param default: The default value to use if input_var is None
    """
    if input_var is None:
        return default
    return input_var
