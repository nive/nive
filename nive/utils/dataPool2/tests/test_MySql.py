
import unittest

from nive.definitions import DatabaseConf

from nive.utils.dataPool2.tests import test_db
from nive.utils.dataPool2.tests import test_Base

from nive.tests import __local
from nive.tests.__local import MYSQL_CONF
from nive.tests import test_mysql


# switch test class to enable / disable tests
if not __local.ENABLE_MYSQL_TESTS:
    class utc:
        pass
    uTestCase = utc
else:
    from nive.utils.dataPool2.mySqlPool import *
    uTestCase = unittest.TestCase
    

class MySqlTest(test_db.dbTest, uTestCase):
    """
    Runs nive.utils.dataPool2.tests.test_db for mysql databases
    """

    def setUp(self):
        p = MySql(connParam=DatabaseConf(MYSQL_CONF), **test_Base.conf)
        p.structure.Init(structure=test_Base.struct, stdMeta=test_Base.struct[u"pool_meta"])
        self.pool = p
        self.checkdb()
        self.connect()

    def connect(self):
        #print "Connect DB on", conn["host"],
        self.pool.CreateConnection(DatabaseConf(MYSQL_CONF))
        self.assert_(self.pool.connection.IsConnected())
        #print "OK"

    def checkdb(self):
        test_mysql.myapp()
    

