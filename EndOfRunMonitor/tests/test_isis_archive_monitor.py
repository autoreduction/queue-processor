"""
Unit tests and associated helpers to exercise the ISIS Archive Checker
"""
import os
import time
import unittest

from EndOfRunMonitor.archive_monitor.isis_archive_monitor import ArchiveMonitor
from EndOfRunMonitor.database_client import ReductionRun
from EndOfRunMonitor.settings import INST_PATH, ARCHIVE_MONITOR_LOG
from EndOfRunMonitor.tests.data_archive_creator import DataArchiveCreator

# List of variables to create a valid path and expected result _find_path_to_current_cycle
# [[start_year, end_year, current_cycle, expected_result], ...]
VALID_PATHS = [[0, 9, 3, 'cycle_09_3'],
               [1, 2, 5, 'cycle_02_5'],
               [10, 14, 1, 'cycle_14_1']]

# List of data to add to a directory and expected result from _find_most_recent_run
FILES_TO_TEST = [['MUSR01.raw', 'MUSR02.raw', 'MUSR03.raw', 'MUSR03.raw'],  # .raw
                 ['MUSR01.RAW', 'MUSR02.RAW', 'MUSR03.RAW', 'MUSR03.RAW'],  # .RAW
                 ['MUSR01.nxs', 'MUSR02.nxs', 'MUSR03.nxs', 'MUSR03.nxs'],  # .nxs
                 ['MUSR01.NXS', 'MUSR02.NXS', 'MUSR03.NXS', 'MUSR03.NXS'],  # .NXS
                 ['MUSR01.nxs', 'MUSR02.raw', 'MUSR03.nxs', 'MUSR03.nxs'],  # .raw/.nxs
                 ['MUSR01.raw', 'MUSR02.RAW', 'MUSR03.raw', 'MUSR03.raw'],  # .raw/.RAW
                 ['MUSR01.raw', 'MUSR03.raw', 'MUSR03.log', 'MUSR03.raw'],  # .log file
                 ['MUSR01.txt', 'MUSR02.log', 'MUSR01.out', None],  # no .raw
                 [None]]  # Empty file

# List of valid instruments
INST = ['MUSR', 'WISH', 'GEM']


# pylint: disable=missing-docstring
class TestISISArchiveChecker(unittest.TestCase):
    """
    Contains test cases for the ArchiveMonitor
    """

    def setUp(self):
        path_to_file = os.path.dirname(os.path.realpath(__file__))
        self.archive_creator = DataArchiveCreator(path_to_file)

    def tearDown(self):
        del self.archive_creator

    # ======================= init ======================== #

    '''def test_valid_init(self):
        monitor = ArchiveMonitor('GEM')
        self.assertIsInstance(monitor, ArchiveMonitor)
        self.assertEqual((INST_PATH.format('GEM')), monitor.instrument_path)

    def test_init_db_connection(self):
        monitor = ArchiveMonitor('GEM')
        self.assertIsNotNone(monitor.database_session)
        self.assertIsNotNone(monitor.database_session.query(ReductionRun).first())

    def test_init_with_invalid_inst(self):
        self.assertRaises(RuntimeError, ArchiveMonitor, 'not-instrument')

    def test_init_case_insensitive(self):
        self.assertIsNotNone(ArchiveMonitor('PoLaRiS'))

    # ============== get_most_recent_in_archive ============== #

    def test_valid_recent_in_archive(self):
        monitor = ArchiveMonitor('MUSR')
        self.archive_creator.make_data_archive(['MUSR'],
                                               VALID_PATHS[2][0],
                                               VALID_PATHS[2][1],
                                               VALID_PATHS[2][2])
        self.archive_creator.add_data_files_to_most_recent_cycle('MUSR',
                                                                 FILES_TO_TEST[0][:-1])
        self.assertEqual(monitor.get_most_recent_in_archive(), 'MUSR03.raw')

    # ============= find_most_recent_run_in_archive ============ #

    def test_valid_find_most_recent_run(self):
        """
        Test that find_most_recent_run produces the expected output
        given the input of FILES_TO_TEST
        """
        monitor = ArchiveMonitor('MUSR')
        self.archive_creator.make_data_archive(['MUSR'],
                                               VALID_PATHS[2][0],
                                               VALID_PATHS[2][1],
                                               VALID_PATHS[2][2])
        for test_files in FILES_TO_TEST:
            self.archive_creator.add_data_files_to_most_recent_cycle('MUSR',
                                                                     test_files[:-1])
            # pylint: disable=protected-access
            actual = monitor._find_most_recent_run_in_archive(
                self.archive_creator.get_most_recent_cycle_for_instrument('MUSR'))
            self.assertEqual(test_files[-1], actual)
            self.archive_creator.delete_all_files()

    # ============ get_most_recent_in_database =============== #

    def test_valid_most_recent_in_db(self):
        expected_runs = ['MUSR1', 'WISH2', 'GEM3']
        for index, instrument in enumerate(INST):
            monitor = ArchiveMonitor(instrument)
            self.assertEqual(monitor.get_most_recent_run_in_database(),
                             expected_runs[index])

    # ========== compare_archive_and_database ================ #

    def test_valid_compare_archive_db(self):
        # overwrite data_archive
        monitor = ArchiveMonitor('GEM')
        self.archive_creator.make_data_archive(["GEM"],
                                               VALID_PATHS[2][0],
                                               VALID_PATHS[2][1],
                                               VALID_PATHS[2][2])
        self.archive_creator.add_data_files_to_most_recent_cycle("GEM",
                                                                 ['GEM1.raw',
                                                                  'GEM2.raw',
                                                                  'GEM3.raw'])
        self.assertTrue(monitor.compare_archive_to_database())

    # ============== restart_reduction_run =================== #

    def test_valid_restart_run(self):
        monitor = ArchiveMonitor('GEM')
        most_recent_file = _setup_send_message_params(self.archive_creator)
        data_to_send = monitor._construct_data_to_send(most_recent_file)
        monitor.resubmit_run_to_queue(data_to_send)
        log = _get_log_content()[-1]
        self.assertTrue("\"instrument\": \"GEM\"" in log)
        self.assertTrue("\"run_number\": \"03\"" in log)
        self.assertTrue("\"rb_number\": \"1234\"" in log)
        self.assertTrue("\"facility\": \"ISIS\"" in log)
        self.assertTrue("destination:/queue/DataReady" in log)

    # ============ perform_check ================ #
    # ToDo: Will need to add these data files to the reduction database mock

    def test_perform_check_no_archive(self):
        monitor = ArchiveMonitor('GEM')
        self.assertRaises(RuntimeError, monitor.perform_check)

    def test_perform_check_part_archive(self):
        self.archive_creator.make_data_archive(["GEM", "WISH"],
                                               VALID_PATHS[2][0],
                                               VALID_PATHS[2][1],
                                               VALID_PATHS[2][2])
        monitor = ArchiveMonitor('GEM')
        self.assertRaises(RuntimeError, monitor.perform_check)

    def test_perform_check_empty_directories(self):
        self.archive_creator.make_data_archive(["GEM", "POLARIS", "WISH", "MUSR", "OSIRIS"],
                                               VALID_PATHS[2][0],
                                               VALID_PATHS[2][1],
                                               VALID_PATHS[2][2])
        monitor = ArchiveMonitor('GEM')
        monitor.perform_check()
        self._check_polling_did_not_update()'''

    def test_perform_check_no_new_files(self):
        self.archive_creator.make_data_archive(["GEM", "POLARIS", "WISH", "MUSR", "OSIRIS"],
                                               VALID_PATHS[2][0],
                                               VALID_PATHS[2][1],
                                               VALID_PATHS[2][2])
        monitor = ArchiveMonitor('GEM')
        self.archive_creator.add_data_files_to_most_recent_cycle('GEM', ['GEM001.raw'])
        self.archive_creator.add_data_files_to_most_recent_cycle('WISH', ['WISH001.raw'])
        monitor.perform_check()
        self._check_polling_did_not_update()

    def _check_polling_did_not_update(self):
        actual = _get_log_content()[-12:]
        performing_check_msg = "Performing Archive Check for {}"
        no_file_msg = "There are no new files since last check at"
        expected = [performing_check_msg.format("GEM"),
                    no_file_msg,
                    performing_check_msg.format("POLARIS"),
                    no_file_msg,
                    performing_check_msg.format("WISH"),
                    no_file_msg,
                    performing_check_msg.format("MUSR"),
                    no_file_msg,
                    performing_check_msg.format("OSIRIS")]
        for index, expected_msg in enumerate(expected):
            self.assertTrue(expected_msg in actual[index],
                            "{} is not in {}".format(expected_msg, actual[index]))

    '''def test_perform_check_update_required(self):
        self.archive_creator.make_data_archive(["GEM", "WISH"],
                                               VALID_PATHS[2][0],
                                               VALID_PATHS[2][1],
                                               VALID_PATHS[2][2])
        self.archive_creator.add_data_files_to_most_recent_cycle('GEM', ['GEM001.raw'])
        self.archive_creator.add_data_files_to_most_recent_cycle('WISH', ['WISH001.raw'])
        monitor = ArchiveMonitor('GEM')
        monitor.perform_check()
        self.archive_creator.add_data_files_to_most_recent_cycle('GEM', ['GEM002.raw'])
        monitor.perform_check()'''


'''class TestArchiveMonitorHelpers(unittest.TestCase):
    """
    Contains test cases for ArchiveMonitor helper functions
    The cases in here are for static members of the class
    """

    def setUp(self):
        path_to_file = os.path.dirname(os.path.realpath(__file__))
        self.archive_creator = DataArchiveCreator(path_to_file)
        self.monitor = ArchiveMonitor('GEM')

    def tearDown(self):
        del self.archive_creator
        del self.monitor

    # ========== find_path_to_current_cycle_in_archive ========= #

    def test_valid_path_to_cycle(self):
        for index, path in enumerate(VALID_PATHS):
            self.archive_creator.make_data_archive(["GEM"], path[0], path[1], path[2])
            # pylint: disable=protected-access
            path_to_data_dir = self.archive_creator.get_data_most_recent_dir_for_instrument("GEM")
            actual = self.monitor._find_path_to_current_cycle_in_archive(path_to_data_dir)
            self.assertEqual(path[3], actual)
            self.archive_creator.delete_archive()

    def test_update_check_time(self):
        # pylint: disable=protected-access
        start_time = self.monitor._time_of_last_check
        time.sleep(0.2)
        self.monitor._update_check_time()
        future_time = self.monitor._time_of_last_check
        self.assertTrue(start_time < future_time)

    def test_valid_get_rb_number(self):
        self.archive_creator.make_data_archive(["GEM"], 1, 2, 3)
        self.archive_creator.add_journal_file("GEM", 'test 1234')
        journal_dir = self.archive_creator.get_journal_dir_for_instrument("GEM")
        actual = self.monitor._get_rb_num(journal_dir)
        self.assertEqual(actual, '1234')

    def test_invalid_get_rb_number(self):
        self.archive_creator.make_data_archive(["GEM"], 1, 2, 3)
        self.archive_creator.add_journal_file("GEM", 'test')
        journal_dir = self.archive_creator.get_journal_dir_for_instrument("GEM")
        actual = self.monitor._get_rb_num(journal_dir)
        self.assertEqual(actual, None)

    def test_valid_message_construction(self):
        most_recent_file = _setup_send_message_params(self.archive_creator)
        actual = self.monitor._construct_data_to_send(most_recent_file)

        expected = {'data': '{}'.format(os.path.join(most_recent_file)),
                    'facility': 'ISIS',
                    'instrument': 'GEM',
                    'rb_number': '1234',
                    'run_number': '03'}
        self.assertEqual(actual, expected)

    def test_get_run_number_from_file(self):
        self.archive_creator.make_data_archive(["GEM"], 1, 2, 2)
        self.archive_creator.add_data_files_to_most_recent_cycle("GEM", ['MUSR123.raw', 'test.txt'])
        most_recent_cycle = self.archive_creator.get_most_recent_cycle_for_instrument("GEM")
        print(most_recent_cycle)
        self.assertEqual(self.monitor._get_run_number_from_file_path(
            os.path.join(most_recent_cycle, 'MUSR123.raw')), '123')
        self.assertEqual(self.monitor._get_run_number_from_file_path(
            os.path.join(most_recent_cycle, 'test.txt')), '')'''


# =========== Test helpers ============== #
def _get_log_content():
    """
    Reads the log file and returns the most recent input
    :return: String of the most recent log
    """
    file_handle = open(ARCHIVE_MONITOR_LOG, "r")
    line_list = file_handle.readlines()
    file_handle.close()
    return line_list


def _setup_send_message_params(archive_creator):
    """
    Create all the file structure dependencies required for a message to be sent
    :param archive_creator: The data archive creator
    :return: file path to the most recent file
    """
    # Create archive
    archive_creator.make_data_archive(["GEM"],
                                      VALID_PATHS[2][0],
                                      VALID_PATHS[2][1],
                                      VALID_PATHS[2][2])
    # Add journal summary
    archive_creator.add_journal_file('GEM', 'test 1234')
    # Add data
    archive_creator.add_data_files_to_most_recent_cycle("GEM", FILES_TO_TEST[0][:-1])
    return os.path.join(archive_creator.get_most_recent_cycle_for_instrument("GEM"),
                        FILES_TO_TEST[0][3])
