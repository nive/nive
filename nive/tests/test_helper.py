
import time
import unittest
import datetime

from nive.definitions import ObjectConf, FieldConf, ViewModuleConf
from nive.utils.path import DvPath
from nive.helper import *

# -----------------------------------------------------------------

class text(object):
    pass

class text1(object):
    pass
class text2(object):
    pass
class text3(object):
    pass

testconf = ObjectConf(
    id = "text",
    name = "Text",
    dbparam = "texts",
    context = "nive.tests.test_helper.text",
    selectTag = 1,
    description = ""
)

testconf.data = (
    FieldConf(id="textblock", datatype="htext", size=10000, default="", name="Text", fulltext=True, description="")
)

testconf.forms = {
    "create": { "fields":  ["textblock"],
                "actions": ["create"]},
    "edit":   { "fields":  ["textblock"], 
                "actions": ["save"]}
}
configuration = testconf


class EncoderTest(unittest.TestCase):

    def test_jsonencoder(self):
        self.assertTrue(JsonDataEncoder().encode({})=="{}")
        self.assertTrue(JsonDataEncoder().encode({"a":"a","b":1}))
        self.assertTrue(JsonDataEncoder().encode({"a":datetime.now()}))
        self.assertTrue(JsonDataEncoder().encode({"a":File()}))

    def test_confencoder(self):
        self.assertTrue(ConfEncoder().encode(Conf()))
        self.assertTrue(ConfEncoder().encode(Conf(**{"a":"a","b":1})))
        self.assertTrue(ConfEncoder().encode(ObjectConf()))
        self.assertTrue(ConfEncoder().encode(ObjectConf(**{"id":"a","name":"1"})))

    # automatic class exports as ccc not supported yet
    #def test_confdecoder(self):
    #    c=ConfEncoder().encode(Conf())
    #    self.assert_(ConfDecoder().decode(c)!=None)
    #    c=ConfEncoder().encode(Conf(**{"a":"a","b":1}))
    #    self.assert_(ConfDecoder().decode(c).a=="a",c)
    #    c=ConfEncoder().encode(ObjectConf())
    #    self.assert_(ConfDecoder().decode(c),c)
    #    c=ConfEncoder().encode(ObjectConf(**{"id":"a","name":"1"}))
    #    self.assert_(ConfDecoder().decode(c).id=="a",c)


class ConfigurationTest(unittest.TestCase):

    def test_resolve1(self, **kw):
        self.assertTrue(ResolveName("nive.tests.test_helper.text", base=None))
        self.assertTrue(ResolveName(".test_helper.text", base="nive.tests"))
        self.assertTrue(ResolveName("nive.tools.dbStructureUpdater", base=None))
        self.assertTrue(ResolveName(".dbStructureUpdater.dbStructureUpdater", base="nive.tools"))
        
    def test_resolve2(self, **kw):
        i,c = ResolveConfiguration(testconf, base=None)
        self.assertTrue(c)
        i,c = ResolveConfiguration("nive.tests.test_helper.testconf", base=None)
        self.assertTrue(c)
        i,c = ResolveConfiguration(".test_helper.testconf", base="nive.tests")
        self.assertTrue(c)
        i,c = ResolveConfiguration("nive.tests.test_helper", base=None)
        self.assertTrue(c)

    def test_load1(self, **kw):
        p=DvPath(__file__)
        p.SetNameExtension("app.json")
        i,c = ResolveConfiguration(str(p))
        self.assertTrue(c)

    def test_load2(self, **kw):
        p=DvPath(__file__)
        p.SetNameExtension("db.json")
        c = LoadConfiguration(str(p))
        self.assertTrue(c)
        
        
    def test_classref(self):
        #self.assert_(GetClassRef(testconf.context, reloadClass=False, raiseError=False)==text)
        self.assertTrue(GetClassRef(text, reloadClass=False, raiseError=False)==text)
        self.assertTrue(GetClassRef("nive.tests.test_helper.textxxxxxx", reloadClass=False, raiseError=False)==None)
        self.assertRaises(ImportError, GetClassRef, "nive.tests.test_helper.textxxxxxx", reloadClass=False, raiseError=True)
        

    def test_factory(self):
        #self.assert_(ClassFactory(testconf, reloadClass=False, raiseError=False)==text)
        c=testconf.copy()
        c.context=text
        self.assertTrue(ClassFactory(c, reloadClass=False, raiseError=False)==text)
        c=testconf.copy()
        c.context="nive.tests.test_helper.textxxxxxx"
        self.assertTrue(ClassFactory(c, reloadClass=False, raiseError=False)==None)
        c=testconf.copy()
        c.context="nive.tests.test_helper.textxxxxxx"
        self.assertRaises(ImportError, ClassFactory, c, reloadClass=False, raiseError=True)

        c=testconf.copy()
        c.extensions=(text1,text2,text3)
        self.assertTrue(len(ClassFactory(c, reloadClass=False, raiseError=False).mro())==6)
        c=testconf.copy()
        c.extensions=("text66666",text2,"text5555")
        self.assertTrue(len(ClassFactory(c, reloadClass=False, raiseError=False).mro())==4)
        c=testconf.copy()
        c.extensions=("nive.tests.test_helper.text1","nive.tests.test_helper.text2","nive.tests.test_helper.text3")
        self.assertTrue(len(ClassFactory(c, reloadClass=False, raiseError=False).mro())==6)


    def test_replace(self):
        alist = [Conf(id="1", value=123),Conf(id="2", value=456),Conf(id="3", value=789)]
        repl = Conf(id="2", value=999)
        new = ReplaceInListByID(alist, repl)
        self.assertTrue(new!=alist)
        self.assertTrue(new[1].value==999)


    def test_update(self):
        alist = [Conf(id="1", value=123),Conf(id="2", value=456),Conf(id="3", value=789)]
        repl = Conf(id="2", value=999)
        new = UpdateInListByID(alist, repl)
        self.assertTrue(new==alist)
        self.assertTrue(new[1].value==999)


    def test_decorator(self):
        class someclass(object):
            pass
        conf = ViewModuleConf(id="test")
        newcls = DecorateViewClassWithViewModuleConf(conf, someclass)
        self.assertTrue(newcls.__configuration__)
        self.assertTrue(newcls.__configuration__().id=="test")

        newcls = DecorateViewClassWithViewModuleConf(conf, "nive.tests.test_helper.text")
        self.assertTrue(newcls.__configuration__)
        self.assertTrue(newcls.__configuration__().id=="test")


from nive.tests import db_app
from nive.tests import __local

class ListItemTest_db:

    def setUp(self):
        self._loadApp()

    def tearDown(self):
        self._closeApp(True)


    def test_listitems(self):
        val = LoadListItems(self.app.configurationQuery.GetFld("pool_type"), app=self.app, obj=None, pool_type=None, force=True)
        self.assertTrue(len(val)==2, val) # one type is hidden
        self.assertTrue(LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"groups"}), app=self.app))
        self.assertTrue(LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"languages"}), app=self.app))
        self.assertTrue(LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"countries"}), app=self.app))
        self.assertTrue(LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"types"}), app=self.app))
        # TODO fill database
        LoadListItems(FieldConf(id="test", datatype="list", settings={"codelist": "users"}), app=self.app)
        LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"meta"}), app=self.app)
        LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"type:type1"}), app=self.app)



class ListItemTest_db_sqlite(ListItemTest_db, __local.SqliteTestCase):
    """
    see tests.__local
    """

class ListItemTest_db_mysql(ListItemTest_db, __local.MySqlTestCase):
    """
    see tests.__local
    """

class ListItemTest_db_pg(ListItemTest_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """
