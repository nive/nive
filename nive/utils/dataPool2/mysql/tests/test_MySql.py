
import unittest

from nive.definitions import DatabaseConf

from nive.utils.dataPool2.mysql.mySqlPool import MySql

from nive.utils.dataPool2.tests import test_db
from nive.utils.dataPool2.tests import test_Base

from nive.tests import __local
from nive.tests.__local import MYSQL_CONF

    

class MySqlTest(test_db.dbTest, __local.MySqlTestCase):
    """
    Runs nive.utils.dataPool2.tests.test_db for mysql databases
    """

    def setUp(self):
        p = MySql(connParam=DatabaseConf(MYSQL_CONF), **test_Base.conf)
        p.structure.Init(structure=test_Base.struct, stdMeta=test_Base.struct[u"pool_meta"])
        self.pool = p
        self.pool.connection.connect()



