
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
        Test that the local host database is correctly generated 
        from django migrations performed in generate-test-db.sh
        """
        db = MySQLdb.connect(host="localhost",
                             user="test-user",
                             passwd="pass",
                             db="autoreduction")
        cur = db.cursor()
        cur.execute("SHOW TABLES")
        for row in cur.fetchall():
            self.assertTrue(row[0] in TABLE_NAMES.append(REDUCTION_VIEWER_TABLES),
                            ("%s was not found in expected TABLE names" % row[0]))

    def test_localhost_reduction_viewer_db_population(self):
        """
        Test that the local host database has been populated with data
        Current test data adds 3 rows per table (so check this)
        exception to this is status that has 5 columns
        """
        db = MySQLdb.connect(host="localhost",
                     user="test-user",
                     passwd="pass",
                     db="autoreduction")
        cur = db.cursor()
        counter = 0
        for table in REDUCTION_VIEWER_TABLES:
            cur.execute("SELECT * FROM {};".format(table))
            if table == "reduction_viewer_status":
                self.assertTrue(len(cur.fetchall()) == 5,
                                "{} does not contain 5 rows.{} : {}".
                                format(table, table, cur.fetchall()))
            else:
                self.assertTrue(len(cur.fetchall()) == 3,
                                "{} does not contain 3 rows.{} : {}".
                                format(table, table, cur.fetchall()))
            counter +=1 
        self.assertEqual(counter, len(EXPECTED_TABLE_NAMES))
        db.close()
