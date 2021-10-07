from autoreduce_utils.message.message import Message


def add_data_and_message():
    """
    Makes and returns some test data and message
    """
    data = {
        'data': '\\\\isis\\inst$\\data.nxs',
        'facility': 'ISIS',
        'instrument': 'GEM',
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
