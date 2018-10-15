"""
Script to hold common varibales used in building the project
"""
import os

from build.utils.build_logger import BuildLogger
from utils.project.structure import get_log_folder

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
BUILD_LOGGER = BuildLogger(get_log_folder())
