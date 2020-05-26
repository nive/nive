
import time
import unittest

from nive.definitions import *
from nive.tools.cmsstatistics import *

from nive.tests import __local

from nive.helper import FormatConfTestFailure

# -----------------------------------------------------------------

class DBSqlDataTest1(unittest.TestCase):

    def test_conf1(self):
        r=configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


    def test_tool(self):
        cmsstatistics(configuration,None)
        
    
class DBSqlDataTest1_db(__local.DefaultTestCase):

    def setUp(self):
        self._loadApp()
        self.app.Register(configuration)

    def tearDown(self):
        self._closeApp()
    
    def test_toolrun1(self):
        t = self.app.GetTool("cmsstatistics", self.app)
        self.assertTrue(t)
        r = t()
        #print v.getvalue()
        self.assertTrue(r)

