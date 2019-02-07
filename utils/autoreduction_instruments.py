"""
List of all valid instruments used in ISIS autoreduction
"""

from utils.instruments import (Instrument, EnginX)


INSTRUMENTS = [
    EnginX(True, '/instrument/%s/RBNumber/RB%s/'),
    Instrument('GEM',     True, '/instrument/%s/RBNumber/RB%s/autoreduced/%s'),
    Instrument('MUSR',    True, '/instrument/%s/RBNumber/RB%s/autoreduced/%s'),
    Instrument('OSIRIS',  True, '/instrument/%s/RBNumber/RB%s/autoreduced/%s'),
    Instrument('POLARIS', True, '/instrument/%s/RBNumber/RB%s/autoreduced/%s'),
    Instrument('POLREF',  True, '/instrument/%s/RBNumber/RB%s/autoreduced/%s'),
    Instrument('WISH',    True, '/instrument/%s/RBNumber/RB%s/autoreduced/%s'),
]


def find_instrument_by_name(inst_name):
    """
    Find an instrument object based on it's name. Raise runtime error if can't be found
    :param inst_name: the name of the instrument to search for
    :return: the Instrument found by searching
    """
    for instrument in INSTRUMENTS:
        if instrument.name.lower() == inst_name.lower():
            return instrument
    raise RuntimeError('Unable to find instrument with name {}'.format(inst_name))


def get_instrument_names():
    """
    There are some cases where we only care about the names of the instruments
    :return: A list of valid instrument names
    """
    instrument_names = []
    for instrument in INSTRUMENTS:
        instrument_names.append(instrument.name)
    return instrument_names
