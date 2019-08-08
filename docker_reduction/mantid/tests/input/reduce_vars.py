standard_vars = {
    'crop_type': None,
    'crop_on': None,
    'grouping_file': None,
}
advanced_vars = {
    'vanadium': "236516",
    'ceria_run': "241391",
    'force_vanadium': True,
    'force_calibration': True,
    'pre_process_run': False,
    'params': None,
    'time_period': None,
}
variable_help = {
    'standard_vars' : {
        'crop_type' : "Must be either \'banks\' or \'spectra\'",
        'crop_on': "Banks: North or South. Spectra: spectrum number or range of spectra (e.g. 1-5)",
        'grouping_file': "Specify the file you wish to use for texture mode. Leave as None if you don't want to use Texture mode."
    },
    'advanced_vars' : {
        'vanadium' : "The run number for the vanadium to use.",
        'ceria_run': "The run number for the ceria run to use.",
        'force_vanadium': "Forces the vanadium to be re-processed",
        'force_calibration': "Forces the calibration to be re-processed",
        'pre_process_run' : "Pre-process the run using the rebinning params",
        'params': "Rebinning parameters for pre-processing",
        'time_period': "time period for pre-processing",
    },
}