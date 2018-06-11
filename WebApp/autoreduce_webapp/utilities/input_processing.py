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
        split_range = value.split('-')
        run_numbers.extend(range(int(split_range[0]), int(split_range[1]) + 1))

    # Range is inclusive
    return run_numbers


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
    # We also allow dashes or commas for delimiting
    _check_input_is_numeric(str_input, '-,')

    # First split out all single values
    single_values = str_input.split(',')

    run_numbers = []

    for value in single_values:
        if '-' not in value:
            # Single value
            _check_input_is_numeric(value)
            run_numbers.append(int(value))
            continue

        # Otherwise range separated values
        split_range = value.split('-')
        _check_input_is_numeric(split_range[0])
        _check_input_is_numeric(split_range[1])

        run_numbers.extend(range(int(split_range[0]), int(split_range[1])))

    return True
