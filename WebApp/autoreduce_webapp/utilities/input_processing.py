"""
Returns an inclusive range of values based on
the unsanitised user input as a string.
If the input is malformed a syntax error is
thrown, otherwise a single integer or list of integers
are returned depending on the original input

:param user_input : The string representation of the user's input
:return List or single value(s) based on user input
:raises Syntax error if the users input contains malformed chars
"""
def parse_user_run_numbers(user_input):
    is_list = True if '-' in user_input else False

    # Single value handling
    if not is_list:
        _check_input_is_numeric(user_input)
        return int(user_input)

    # List handling
    _check_ranged_numeric_input(user_input)
    run_range = user_input.split('-')
    # Range is inclusive
    return range(int(run_range[0]), int(run_range[1]) + 1)


def _check_input_is_numeric(str_input, extra_whitelisted_char_set=None):
    # Allow 0-9 to delimit the list plus any passed extra ones
    allowed_characters = set("1234567890")
    if extra_whitelisted_char_set:
        allowed_characters |= set(extra_whitelisted_char_set)

    disallowed_char = next((char for char in str_input if char not in allowed_characters), None)
    if disallowed_char:
        raise SyntaxError("The character '{0}' was entered, which is not permitted".format(disallowed_char))

    return True


def _check_ranged_numeric_input(str_input):
    # We also allow dashes for delimiting
    _check_input_is_numeric(str_input, '-')

    run_range = str_input.split('-')
    if len(run_range) != 2:
        raise SyntaxError("Incorrect number of range delimiters was entered")

    return True