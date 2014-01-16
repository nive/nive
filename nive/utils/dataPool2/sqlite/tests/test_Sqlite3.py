
import unittest

from nive.definitions import DatabaseConf
from nive.utils.path import DvPath
from nive.utils.dataPool2.sqlite.sqlite3Pool import Sqlite3

from nive.utils.dataPool2.tests import test_db
from nive.utils.dataPool2.tests import test_Base

from nive.tests import __local
from nive.tests.__local import DB_CONF

    

class Sqlite3Test(test_db.dbTest, __local.SqliteTestCase):
    """
    Runs nive.utils.dataPool2.tests.test_db for mysql databases
    """

    def setUp(self):
        conn = DatabaseConf(DB_CONF)
        p = Sqlite3(connParam=conn, **test_Base.conf)
        p.structure.Init(structure=test_Base.struct, stdMeta=test_Base.struct[u"pool_meta"])
        dbfile = DvPath(conn["dbName"])
        if not dbfile.IsFile():
            dbfile.CreateDirectories()
        self.pool = p
        self.pool.connection.connect()

    def tearDown(self):
        self.pool.Close()



