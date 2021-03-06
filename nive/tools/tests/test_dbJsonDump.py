
import time
import unittest

from nive.tools.dbJsonDump import *

from nive.tests import db_app, __local

from nive.helper import FormatConfTestFailure

# -----------------------------------------------------------------

class DBSqlDataTest1(unittest.TestCase):

    def test_conf1(self):
        r=configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


    def test_tool(self):
        dbJsonDump(configuration,None)
        
    
class DBSqlDataTest1_db(__local.DefaultTestCase):

    def setUp(self):
        self._loadApp()
        self.app.Register(configuration)
        root = self.app.root
        o = db_app.createObj1(root)
        db_app.createObj1(o)
        db_app.createObj2(o)
        db_app.createObj3(o)
        self.o = o

    def tearDown(self):
        self._closeApp(True)
    

    def test_toolrun1(self):
        t = self.app.GetTool("nive.tools.dbJsonDump", self.app)
        self.assertTrue(t)
        t.importWf = 0
        t.importSecurity = 0
        r = t()
        #print v
        self.assertTrue(r)


    def test_toolrun2(self):
        t = self.app.GetTool("dbJsonDump", self.app)
        self.assertTrue(t)
        t.importWf = 1
        t.importSecurity = 1
        r = t()
        self.assertTrue(r)

