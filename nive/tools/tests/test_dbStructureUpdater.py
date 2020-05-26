
import time
import unittest

from nive.definitions import *
from nive.helper import ResolveName
from nive.tools.dbStructureUpdater import *

from nive.tests import __local


from nive.helper import FormatConfTestFailure


# -----------------------------------------------------------------

class DBStructureTest(unittest.TestCase):


    def test_conf1(self):
        r=configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


    def test_tool(self):
        t = dbStructureUpdater(configuration,None)
        self.assertTrue(t)

    
class DBStructureTest2(__local.DefaultTestCase):
    """
    """
    def setUp(self):
        self._loadApp()
        self.app.Register(configuration)

    def tearDown(self):
        self._closeApp(True)


    def test_toolrun1(self):
        t = self.app.GetTool("nive.tools.dbStructureUpdater")
        self.assertTrue(t)
        t.importWf = 0
        t.importSecurity = 0
        r = t()
        self.assertTrue(r)


    def test_toolrun2(self):
        t = self.app.GetTool("nive.tools.dbStructureUpdater")
        self.assertTrue(t)
        t.importWf = 1
        t.importSecurity = 1
        r = t()
        self.assertTrue(r)


    def test_toolrun3(self):
        tc = self.app.configuration.copy()
        tc["skipUpdateTables"] = ("pool_meta","pool_sys")
        self.app.configuration = tc
        t = self.app.GetTool("nive.tools.dbStructureUpdater")
        self.assertTrue(t)
        t.importWf = 1
        t.importSecurity = 1
        r = t()
        self.assertTrue(r)

