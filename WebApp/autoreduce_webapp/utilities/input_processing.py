# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Custom parsing of user input
"""


def parse_user_run_numbers(user_input):
    """
    Returns an inclusive range of values based on the unsanitised user input as a string.
    If the input is malformed a syntax error is thrown, otherwise a single integer or list
    of integers are returned depending on the original input.
    :param user_input : The string representation of the user's input
    :return List or single value(s) based on user input
    :raises Syntax error if the users input contains malformed chars
    """
    allowed_non_numeric = ['-', ',']
    is_list = True if any(x in user_input for x in allowed_non_numeric) else False

    # Single value handling
    if not is_list:
        _check_input_is_numeric(user_input)
        return [int(user_input)]

    # List handling below
    _check_ranged_numeric_input(user_input)

    single_values = user_input.split(',')
    run_numbers = []
    for value in single_values:
        if '-' not in value:
            # Single value
            run_numbers.append(int(value))
            continue

        # Otherwise range separated values
        saturated_vals = _parse_range_input(value)
        if len(saturated_vals) == 2:
            run_numbers.extend(range(int(saturated_vals[0]), int(saturated_vals[1]) + 1))
        else:
            # Single negative value
            run_numbers.append(int(saturated_vals[0]))

    # Range is inclusive
    return run_numbers


def _check_input_is_numeric(str_input, extra_whitelisted_char_set=None):
    # Allow 0-9 to delimit the list plus any passed extra ones
    if not str_input:
        raise SyntaxError("No numeric digits were entered at all, or after a ',' or '-' character.")

    allowed_characters = set("1234567890-")
    if extra_whitelisted_char_set:
        allowed_characters |= set(extra_whitelisted_char_set)

    disallowed_char = next((char for char in str_input if char not in allowed_characters), None)
    if disallowed_char:
        raise SyntaxError("The character '{0}' was entered, " "which is not permitted".format(disallowed_char))

    return True


def _check_ranged_numeric_input(str_input):
    # We also allow dashes or commas for delimiting
    _check_input_is_numeric(str_input, '-,')

    # First split out all single values
    single_values = str_input.split(',')

    for value in single_values:
        if '-' not in value:
            # Single value
            _check_input_is_numeric(value)
            continue

        # Otherwise range separated values
        returned_ranges = _parse_range_input(value)

        if len(returned_ranges) > 2:
            # A range greater than 2 has been added (i.e. 3 - 5 - 7)
            raise SyntaxError("More than 2 values have been detected in {0}".format(str_input))

        for split_ranges in returned_ranges:
            _check_input_is_numeric(split_ranges)

    return True


def _parse_range_input(ranged_input):
    split_range = ranged_input.split('-')

    found_val = []

    next_val_represents_negative = False
    for value in split_range:
        if not value and not next_val_represents_negative:
            # The next value is probably negative
            next_val_represents_negative = True
            continue

        if not value and next_val_represents_negative:
            # We probably have an input like -3 - (-5) as: -3--5
            # consume this range separator
            continue

        # Check if the current value is negative
        found_val.append('-' + value if next_val_represents_negative else value)
        next_val_represents_negative = False

    return found_val
