import unittest

from scripts.mysql_dump.reset_database_post_cycle import CycleReset


class TestMySQLDump(unittest.TestCase):

    def test_invalid_cycle(self):
        self.assertRaisesRegexp(RuntimeError, 'not_cycle did not match the expected regex'
                                              ' for a cycle', CycleReset, 'not_cycle', 'user')
        self.assertRaisesRegexp(RuntimeError, 'cycle_100_10 did not match the expected regex'
                                              ' for a cycle', CycleReset, 'cycle_100_10', 'user')
