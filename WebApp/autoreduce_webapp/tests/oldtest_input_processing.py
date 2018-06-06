import string, unittest

from utilities import input_processing

# This test needs reworking, so was prefixed with the word old
# so it would not be picked up by nosetests

class RunParsingTestCase(unittest.TestCase):
    def test_single_value_case(self):
        input_value = "101"
        expected_value = int(input_value)

        result = input_processing.parse_user_run_numbers(input_value)
        self.assertEqual(expected_value, result)

    def test_list_case(self):
        input_value = "10-20"
        # Returns inclusive values
        expected_value = range(10, 21)

        result = input_processing.parse_user_run_numbers(input_value)
        self.assertEqual(expected_value, result)

    def test_alpha_char_is_rejected(self):
        # Check the single case first
        with self.assertRaises(SyntaxError):
            input_processing.parse_user_run_numbers('a')

        # Check all individual characters
        for char in string.ascii_letters:
            with self.assertRaises(SyntaxError):
                input_processing.parse_user_run_numbers(char)