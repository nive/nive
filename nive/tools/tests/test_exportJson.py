
import time
import unittest

from nive.definitions import *
from nive.tools.exportJson import *

from nive.tests import db_app, __local

from nive.helper import FormatConfTestFailure
from nive.security import User

# -----------------------------------------------------------------

class DBExportTest1(unittest.TestCase):

    def test_conf1(self):
        r=configuration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")

    def test_tool(self):
        exportJson(configuration,None)
        
    
class DBExportTest1_db(__local.DefaultTestCase):

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
        t = self.app.GetTool("nive.tools.exportJson", self.app)
        self.assert_(t)
        r,v = t(tree=1,filedata="none")
        self.assert_(r)


    def test_toolrun2(self):
        t = self.app.GetTool("exportJson", self.app)
        self.assert_(t)
        r,v = t(tree=0,filedata="path")
        self.assert_(r)


    def test_toolrun3(self):
        t = self.app.GetTool("exportJson", self.app)
        self.assert_(t)
        r,v = t(tree=1,filedata="data")
        self.assert_(r)

