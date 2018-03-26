import MySQLdb
import unittest


# All TABLES in the database Schema
expected_table_names = ["auth_group",
                        "auth_group_permissions",
                        "auth_permission",
                        "auth_user",
                        "auth_user_groups",
                        "auth_user_user_permissions",
                        "autoreduce_webapp_cache",
                        "autoreduce_webapp_experimentcache",
                        "autoreduce_webapp_instrumentcache",
                        "autoreduce_webapp_usercache",
                        "django_admin_log",
                        "django_content_type",
                        "django_migrations",
                        "django_session",
                        "reduction_variables_instrumentvariable",
                        "reduction_variables_runvariable",
                        "reduction_variables_variable",
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
            self.assertTrue(row[0] in expected_table_names, ("%s was not found in expected TABLE names" % row[0]))

        db.close()
