import MySQLdb
import unittest

# All TABLES in the database Schema
EXPECTED_TABLE_NAMES = {"auth_group",
                        "auth_group_permissions",
                        "auth_permission",
                        "auth_user",
                        "auth_user_groups",
                        "auth_user_user_permissions",
                        "django_content_type",
                        "django_migrations",
                        "reduction_viewer_datalocation",
                        "reduction_viewer_experiment",
                        "reduction_viewer_instrument",
                        "reduction_viewer_notification",
                        "reduction_viewer_reductionlocation",
                        "reduction_viewer_reductionrun",
                        "reduction_viewer_setting",
                        "reduction_viewer_status"}


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
        all_tables = set()
        for row in cur.fetchall():
            all_tables.add(row[0])
        self.assertEqual(EXPECTED_TABLE_NAMES, all_tables)
        db.close()
