from autoreduce_utils.message.message import Message
from autoreduce_utils.settings import CYCLE_DIRECTORY


def add_data_and_message():
    """
    Makes and returns some test data and message
    """
    data = {
        'data': '\\\\isis\\inst$\\NDXTESTINSTRUMENT\\Instrument\\data\\cycle_21_1\\data.nxs',
        'facility': 'ISIS',
        'instrument': 'TESTINSTRUMENT',
        'rb_number': '1234',
        'run_number': '4321',
        'run_version': 1,
        'reduction_script': 'print("hello")',  # not actually used for the reduction
        'reduction_arguments': {
            "standard_vars": {
                "arg1": "differentvalue",
                "arg2": 321
            },
            "advanced_vars": {
                "adv_arg1": "advancedvalue2",
                "adv_arg2": ""
            }
        },
        'description': 'This is a test',
        'software': {
            "name": "Mantid",
            "version": "6.2.0",
        },
    }

    message = Message()
    message.populate(data)
    return data, message


def expected_return_data_and_message():
    """
    Makes and returns some test data and message
    """
    data = {
        'data': '\\\\isis\\inst$\\NDXTESTINSTRUMENT\\Instrument\\data\\cycle_21_1\\data.nxs',
        'facility': 'ISIS',
        'instrument': 'TESTINSTRUMENT',
        'rb_number': '1234',
        'run_number': '4321',
        'run_version': 1,
        'reduction_script': 'print("hello")',  # not actually used for the reduction
        'reduction_arguments': {
            "standard_vars": {
                "arg1": "differentvalue",
                "arg2": 321
            },
            "advanced_vars": {
                "adv_arg1": "advancedvalue2",
                "adv_arg2": ""
            }
        },
        'description': 'This is a test',
        'software': "6.2.0",
        "reduction_data": "/instrument/TESTINSTRUMENT/RBNumber/RB1234/autoreduced/Test run name/run-version-1",
        "reduction_log":
        "Running reduction script: /isis/NDXTESTINSTRUMENT/user/scripts/autoreduction/reduce.py\nHello\n"
    }

    message = Message()
    message.populate(data)
    return data, message


def add_bad_data_and_message():
    """
    Makes and returns some test data and message
    """
    data = {
        'data': CYCLE_DIRECTORY % ("TESTINSTRUMENT", "21_1") + '/data.nxs',
        'facility': 'ISIS',
        'instrument': 'TESTINSTRUMENT',
        'rb_number': '1234',
        'run_number': '4321',
        'run_version': 1,
        'reduction_script': 'print("hello")',  # not actually used for the reduction
        'reduction_arguments': "None",
        'description': 'This is a test',
        'software': "6.2.0",
        "reduction_data": "/instrument/TESTINSTRUMENT/RBNumber/RB1234/autoreduced/Test run name/run-version-1",
        "reduction_log": "Running reduction script: /isis/NDXTESTINSTRUMENT/user/scripts/autoreduction/reduce.py"
    }

    message = Message()
    message.populate(data)
    return data, message
