
import sys
import unittest
from nive.definitions import DatabaseConf
from nive.tests import db_app


# real database test configuration
# change these to fit your system

WIN = sys.platform.startswith("win")

# sqlite and mysql
if WIN:
    ROOT = "c:\\Temp\\nive3-test\\"
else:
    ROOT = "/tmp/nive3-test/"



DB_CONF = DatabaseConf(
    dbName = ROOT+"test.db",
    fileRoot = ROOT,
    context = "Sqlite3"
)


MYSQL_CONF = DatabaseConf(
    context = "MySql",
    dbName = "ut_nive",
    host = "localhost",
    user = "root",
    password = "root",
    port = "",
    fileRoot = ROOT
)


POSTGRES_CONF = DatabaseConf(
    context = "PostgreSql",
    dbName = "ut_nive",
    host = "localhost",
    user = "postgres",
    password = "postgres",
    port = "",
    fileRoot = ROOT
)

# essential system tests are run for multiple database systems if installed.
# These switches also allow to manually enable or disable database system tests.
ENABLE_SQLITE_TESTS = True
ENABLE_MYSQL_TESTS = False
ENABLE_POSTGRES_TESTS = False


if ENABLE_SQLITE_TESTS:

    class SqliteTestCase(unittest.TestCase):
        def _loadApp(self, mods=None):
            if not mods:
                mods = []
            mods.append(DatabaseConf(DB_CONF))
            self.app = db_app.app_db(mods)

        def _closeApp(self, data=False, files=False):
            pass
            #if data:
            #    db_app.emptypool(self.app, files)
            #self.app.Close()

else:

    class SqliteTestCase(object):
        def _loadApp(self, mods=None):
            pass

        def _closeApp(self, delete=False, files=False):
            pass


if ENABLE_MYSQL_TESTS:

    class MySqlTestCase(unittest.TestCase):
        def _loadApp(self, mods=None):
            if not mods:
                mods = []
            mods.append(DatabaseConf(MYSQL_CONF))
            self.app = db_app.app_db(mods)

        def _closeApp(self, delete=False, files=False):
            if delete:
                db_app.emptypool(self.app, files)
            self.app.Close()

else:

    class MySqlTestCase(object):
        def _loadApp(self, mods=None):
            pass
        def _closeApp(self, delete=False, files=False):
            pass


if ENABLE_POSTGRES_TESTS:

    class PostgreSqlTestCase(unittest.TestCase):
        def _loadApp(self, mods=None):
            if not mods:
                mods = []
            mods.append(DatabaseConf(POSTGRES_CONF))
            self.app = db_app.app_db(mods)

        def _closeApp(self, delete=False, files=False):
            if delete:
                db_app.emptypool(self.app, files)
            self.app.Close()

else:

    class PostgreSqlTestCase(object):
        def _loadApp(self, mods=None):
            pass
        def _closeApp(self, delete=False, files=False):
            pass



# Higher level tests are only run for one database system (sqlite if activated), not multiple.
DefaultTestCase = SqliteTestCase
if not ENABLE_SQLITE_TESTS:
    if ENABLE_POSTGRES_TESTS:
        DefaultTestCase = PostgreSqlTestCase
    else:
        DefaultTestCase = MySqlTestCase

    
