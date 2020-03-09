# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit test setup default variables for use in mocks accross system performance package
"""


class MockInstrumentModels:  # pylint: disable=too-few-public-methods
    """Mocking instrument models name and id properties"""

    def __init__(self, name, inst_Id):
        self.name = name
        self.id = inst_Id  # pylint disable=invalid-name


class Setup_Variables:
    """Class containing setup variables for use in unit test mocks"""

    def __init__(self):
        self.invalid_method = 'invalid_method'
        self.valid_method = 'missing_run_numbers_report'

        # List of instrument to evaluate against db returned row proxy objects
        self.instruments = [MockInstrumentModels('GEM', 1),
                            MockInstrumentModels('WISH', 2),
                            MockInstrumentModels('OSIRIS', 3),
                            MockInstrumentModels('POLARIS', 4),
                            MockInstrumentModels('MUSR', 5),
                            MockInstrumentModels('POLREF', 6),
                            MockInstrumentModels('ENGINX', 7),
                            MockInstrumentModels('MARI', 8),
                            MockInstrumentModels('MAPS', 9)]

        # Default arguments for test cases
        self.arguments_dict = {'selection': 'run_number',
                               'status_id': 4,
                               'retry_run': '',
                               'run_state_column': 'finished',
                               'end_date': 'CURDATE()',
                               'interval': 1,
                               'time_scale': 'DAY',
                               'start_date': None,
                               'instrument_id': None}

        # Missing_run_numbers_report expected method return
        self.missing_run_numbers_report_mock_return = {'GEM': {'Count_of_runs': 101,
                                                               'Missing_runs_count': 0,
                                                               'Missing_runs': []},
                                                       'WISH': {'Count_of_runs': 295,
                                                                'Missing_runs_count': 2,
                                                                'Missing_runs': [47173, 47174]}}
