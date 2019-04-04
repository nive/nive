
import unittest

from nive.definitions import DatabaseConf
from nive.utils.path import DvPath

from nive.utils.dataPool2.mysql.mySqlPool import MySql

from nive.utils.dataPool2.tests import test_db
from nive.utils.dataPool2.tests import test_Base

from nive.tests.__local import MYSQL_CONF, MySqlTestCase

    

class MySqlTest(test_db.dbTest, MySqlTestCase):
    """
    Runs nive.utils.dataPool2.tests.test_db for mysql databases
    """

    def setUp(self):
        p = MySql(connParam=DatabaseConf(MYSQL_CONF), **test_Base.conf)
        p.structure.Init(structure=test_Base.struct, stdMeta=test_Base.struct["pool_meta"])
        dbfile = DvPath(MYSQL_CONF["dbName"])
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



