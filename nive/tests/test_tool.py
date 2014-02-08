
import time
import unittest

from nive.definitions import *
from nive.tool import *
from nive.security import User 

from nive.tools.example import configuration
from nive.tests import db_app
from nive.tests import __local



class ToolTest1(unittest.TestCase):

    def test_tool(self):
        t=Tool(ToolConf(id="test",data=[FieldConf(id="test",datatype="string")], values={"test":"aaaaa"}), None)
        t.Run()
        self.assert_(t.ExtractValues()["test"]=="aaaaa")
        t.AppliesTo("type1")
        self.assert_(t.GetAllParameters())
        self.assert_(t.GetParameter("test"))


class ToolTest_db:

    def setUp(self):
        self._loadApp()

    def tearDown(self):
        self.app.Close()

    def test_toolapp(self):
        t = self.app.GetTool("nive.tools.example")
        self.assert_(t)
        r,v = t()
        self.assert_(r)

    def test_toolapp2(self):
        self.app.Register("nive.tools.example")
        t = self.app.GetTool("exampletool")
        self.assert_(t)
        r,v = t()
        self.assert_(r)

    def test_toolapp3(self):
        c2 = ToolConf(configuration)
        c2.id = "exampletool2"
        c2.apply = (IApplication,)
        self.app.Register(c2)
        t = self.app.GetTool("exampletool2", self.app)
        self.assert_(t)
        r,v = t()
        self.assert_(r)

    def test_toolobj(self):
        user = User(u"test")
        r = self.app.root()
        o = db_app.createObj1(r)
        t = o.GetTool("nive.tools.example")
        r1,v = t()
        self.assert_(r1)
        r.Delete(o.GetID(), user=user)


class ToolTest_db_sqlite(ToolTest_db, __local.SqliteTestCase):
    """
    see tests.__local
    """

class ToolTest_db_mysql(ToolTest_db, __local.MySqlTestCase):
    """
    see tests.__local
    """

class ToolTest_db_pg(ToolTest_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """
