
import unittest
import sys
from nive.definitions import DatabaseConf
from nive.components.webapi.tests import db_app

ENABLE_SQLITE_TESTS = True
ENABLE_MYSQL_TESTS = False
ENABLE_POSTGRES_TESTS = False

# real database test configuration
# change these to fit your system

WIN = sys.platform.startswith("win")

# sqlite and mysql
if WIN:
    ROOT = "c:\\Temp\\nive3-test\\"
else:
    ROOT = "/tmp/nive3-test/"



DB_CONF = DatabaseConf(
    dbName = ROOT+"test-webapi.db",
    fileRoot = ROOT,
    context = "Sqlite3"
)


MYSQL_CONF = DatabaseConf(
    context = "MySql",
    dbName = "ut_nive-webapi",
    host = "localhost",
    user = "root",
    password = "root",
    port = "",
    fileRoot = ROOT
)


POSTGRES_CONF = DatabaseConf(
    context = "PostgreSql",
    dbName = "ut_nive-webapi",
    host = "localhost",
    user = "postgres",
    password = "postgres",
    port = "",
    fileRoot = ROOT
)



if ENABLE_SQLITE_TESTS:

    class SqliteTestCase(unittest.TestCase):
        def _loadApp(self, mods=None):
            if not mods:
                mods = []
            mods.append(DatabaseConf(DB_CONF))
            self.app = db_app.app_db(mods)

else:

    class SqliteTestCase(object):
        def _loadApp(self, mods=None):
            pass


if ENABLE_MYSQL_TESTS:

    class MySqlTestCase(unittest.TestCase):
        def _loadApp(self, mods=None):
            if not mods:
                mods = []
            mods.append(DatabaseConf(MYSQL_CONF))
            self.app = db_app.app_db(mods)

else:

    class MySqlTestCase(object):
        def _loadApp(self, mods=None):
            pass


if ENABLE_POSTGRES_TESTS:

    class PostgreSqlTestCase(unittest.TestCase):
        def _loadApp(self, mods=None):
            if not mods:
                mods = []
            mods.append(DatabaseConf(POSTGRES_CONF))
            self.app = db_app.app_db(mods)

else:

    class PostgreSqlTestCase(object):
        def _loadApp(self, mods=None):
            pass



# Higher level tests are only run for one database system, not multiple.
# The database type can be switched here
DefaultTestCase = SqliteTestCase

    
