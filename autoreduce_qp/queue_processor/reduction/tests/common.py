from autoreduce_utils.message.message import Message
from autoreduce_utils.settings import CYCLE_DIRECTORY


def add_data_and_message():
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
        'reduction_arguments': 'None',
        'description': 'This is a test',
    }

    message = Message()
    message.populate(data)
    return data, message
