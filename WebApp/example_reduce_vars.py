# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint: skip-file
standard_vars = {
    'Minimum Extents': '-3,-5,-4,-5.0',
    'Maximum Extents': '5,2,4,30.0',
    'UB Matrix': [2.87, 2.87, 2.87],  # a, b, c
    'Run Range Starts': [22413, 22450],
    'Run Range Ends': [],
    'Psi Starts': [0, 7],
    'Psi Increments': [2, 0.5]
}
advanced_vars = {'Number of Runs to Merge': [5], 'Filenames': []}
variable_help = {
    'standard_vars': {
        'UB Matrix': "The list of a, b, c"
    },
    'advanced_vars': {
        'Number of Runs to Merge': "The total number of runs that should be merged."
    },
}
