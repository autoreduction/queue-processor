"""
Instrument model for EnginX
"""
from utils.instruments.instrument import Instrument


class EnginX(Instrument):

    def __init__(self, use_nexus, output_directory):
        Instrument.__init__(self, 'ENGINX', use_nexus, output_directory)

    def format_output_directory(self, meta_data_dict):
        """
        Construct the output directory using the meta_data_dict
        This should be overridden where required
        :param meta_data_dict: A dictionary of meta data relating to
        :return: A full path to the output data directory
        """
        return self.output_directory.format(self.name,
                                            meta_data_dict['rb'])
