
import unittest

from nive.definitions import DatabaseConf
from nive.utils.path import DvPath
from nive.utils.dataPool2.sqlite.sqlite3Pool import Sqlite3

from nive.utils.dataPool2.tests import test_db
from nive.utils.dataPool2.tests import test_Base

from nive.tests.__local import DB_CONF, SqliteTestCase

    

class Sqlite3Test(test_db.dbTest, SqliteTestCase):
    """
    Runs nive.utils.dataPool2.tests.test_db for mysql databases
    """

    def setUp(self):
        p = Sqlite3(connParam=DatabaseConf(DB_CONF), **test_Base.conf)
        p.structure.Init(structure=test_Base.struct, stdMeta=test_Base.struct["pool_meta"])
        dbfile = DvPath(DB_CONF["dbName"])
        if not dbfile.IsFile():
            dbfile.CreateDirectories()
        self.pool = p
        self.pool.connection.connect()

    def tearDown(self):
        cursor = self.pool.Execute("delete FROM pool_meta")
        self.pool.Execute("delete FROM pool_files", cursor=cursor)
        self.pool.Execute("delete FROM data2", cursor=cursor)
        self.pool.Execute("delete FROM data1", cursor=cursor)
        self.pool.Commit()
        self.pool.Close()


