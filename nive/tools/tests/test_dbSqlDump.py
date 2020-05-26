
import time
import unittest

from nive.tools.dbSqlDump import *

from nive.tests import db_app, __local

from nive.helper import FormatConfTestFailure
from nive.security import User

# -----------------------------------------------------------------

class DBSqlDataTest1(unittest.TestCase):

    def test_conf1(self):
        r=configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


    def test_tool(self):
        dbSqlDump(configuration,None)
        
    
class DBSqlDataTest1_db(__local.DefaultTestCase):

    def setUp(self):
        self._loadApp()
        self.app.Register(configuration)
        root = self.app.root
        self.o=o=db_app.createObj1(root)
        db_app.createObj1(o)
        db_app.createObj2(o)
        db_app.createObj3(o)

    def tearDown(self):
        self._closeApp(True)
            

    def test_toolrun1(self):
        t = self.app.GetTool("dbSqlDump", self.app)
        self.assertTrue(t)
        t.importWf = 0
        t.importSecurity = 0
        r = t()
        #print v
        self.assertTrue(r)


    def test_toolrun2(self):
        t = self.app.GetTool("dbSqlDump", self.app)
        self.assertTrue(t)
        t.importWf = 1
        t.importSecurity = 1
        r = t()
        self.assertTrue(r)

