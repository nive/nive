
import time
import unittest

from nive.tools.dbJsonDump import *

from nive.tests import db_app, __local

from nive.helper import FormatConfTestFailure
from nive.security import User

# -----------------------------------------------------------------

class DBSqlDataTest1(unittest.TestCase):

    def test_conf1(self):
        r=configuration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")

    def test_tool(self):
        dbJsonDump(configuration,None)
        
    
class DBSqlDataTest1_db(__local.DefaultTestCase):

    def setUp(self):
        self._loadApp()
        self.app.Register(configuration)
        root = self.app.root()
        self.o=o=db_app.createObj1(root)
        db_app.createObj1(o)
        db_app.createObj2(o)
        db_app.createObj3(o)

    def tearDown(self):
        self.app.root().Delete(self.o.id, user=User("aaa"))
        self.app.Close()
    
    def test_toolrun1(self):
        t = self.app.GetTool("nive.tools.dbJsonDump", self.app)
        self.assert_(t)
        t.importWf = 0
        t.importSecurity = 0
        r,v = t()
        #print v
        self.assert_(r)


    def test_toolrun2(self):
        t = self.app.GetTool("dbJsonDump", self.app)
        self.assert_(t)
        t.importWf = 1
        t.importSecurity = 1
        r,v = t()
        self.assert_(r)

