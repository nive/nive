
import unittest

from nive.definitions import DatabaseConf

from nive.utils.dataPool2.postgres.postgreSqlPool import PostgreSql

from nive.utils.dataPool2.tests import test_db
from nive.utils.dataPool2.tests import test_Base

from nive.tests import __local
from nive.tests.__local import POSTGRES_CONF

    

class PostgreSqlTest(test_db.dbTest, __local.PostgreSqlTestCase):
    """
    Runs nive.utils.dataPool2.tests.test_db for postgres databases
    """

    def setUp(self):
        p = PostgreSql(connParam=DatabaseConf(POSTGRES_CONF), **test_Base.conf)
        p.structure.Init(structure=test_Base.struct, stdMeta=test_Base.struct[u"pool_meta"])
        self.pool = p
        self.pool.connection.connect()


