import MySQLdb
import unittest


# All TABLES in the database Schema
EXPECTED_TABLE_NAMES = ["django_migrations",
                        "reduction_viewer_datalocation",
                        "reduction_viewer_experiment",
                        "reduction_viewer_instrument",
                        "reduction_viewer_notification",
                        "reduction_viewer_reductionlocation",
                        "reduction_viewer_reductionrun",
                        "reduction_viewer_setting",
                        "reduction_viewer_status"]


class TestDatabaseGeneration(unittest.TestCase):

    def test_localhost_db_construction(self):
        """
        Test that the local host database on travis is correctly
        generated from the .sql construction files
        """
        db = MySQLdb.connect(host="localhost",
                             user="test-user",
                             passwd="pass",
                             db="autoreduction")

        cur = db.cursor()
        cur.execute("SHOW TABLES")
        for row in cur.fetchall():
            self.assertTrue(row[0] in EXPECTED_TABLE_NAMES,
                            ("%s was not found in expected TABLE names" % row[0]))
        self.assertEqual(len(cur.fetchall()), len(EXPECTED_TABLE_NAMES))
        db.close()
