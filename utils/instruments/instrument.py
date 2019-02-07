"""
Models an ISIS Instrument
"""


class Instrument(object):

    name = None
    use_nexus = True
    output_directory = None

    def __init__(self, name, use_nexus, output_directory):
        self.name = name
        self.use_nexus = use_nexus
        self.output_directory = output_directory

    def format_output_directory(self, meta_data_dict):
        """
        Construct the output directory using the meta_data_dict
        This should be overridden where required
        :param meta_data_dict: A dictionary of meta data relating to
        :return: A full path to the output data directory
        """
        return self.output_directory.format(self.name,
                                            meta_data_dict['rb'],
                                            meta_data_dict['run'])
