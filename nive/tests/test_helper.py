
import time
import unittest
import datetime

from nive.definitions import ObjectConf, FieldConf, Conf, ViewModuleConf
from nive.utils.path import DvPath
from nive.utils.dataPool2.files import File
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

    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_jsonencoder(self):
        self.assert_(JsonDataEncoder().encode({})=="{}")
        self.assert_(JsonDataEncoder().encode({"a":"a","b":1}))
        self.assert_(JsonDataEncoder().encode({"a":datetime.now()}))
        self.assert_(JsonDataEncoder().encode({"a":File()}))

    def test_confencoder(self):
        self.assert_(ConfEncoder().encode(Conf()))
        self.assert_(ConfEncoder().encode(Conf(**{"a":"a","b":1})))
        self.assert_(ConfEncoder().encode(ObjectConf()))
        self.assert_(ConfEncoder().encode(ObjectConf(**{"id":"a","name":"1"})))

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

    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    

    def test_resolve1(self, **kw):
        self.assert_(ResolveName("nive.tests.test_helper.text", base=None))
        self.assert_(ResolveName(".test_helper.text", base="nive.tests"))
        self.assert_(ResolveName("nive.tools.dbStructureUpdater", base=None))
        self.assert_(ResolveName(".dbStructureUpdater.dbStructureUpdater", base="nive.tools"))
        
    def test_resolve2(self, **kw):
        i,c = ResolveConfiguration(testconf, base=None)
        self.assert_(c)
        i,c = ResolveConfiguration("nive.tests.test_helper.testconf", base=None)
        self.assert_(c)
        i,c = ResolveConfiguration(".test_helper.testconf", base="nive.tests")
        self.assert_(c)
        i,c = ResolveConfiguration("nive.tests.test_helper", base=None)
        self.assert_(c)

    def test_load1(self, **kw):
        p=DvPath(__file__)
        p.SetNameExtension("app.json")
        i,c = ResolveConfiguration(str(p))
        self.assert_(c)

    def test_load2(self, **kw):
        p=DvPath(__file__)
        p.SetNameExtension("db.json")
        c = LoadConfiguration(str(p))
        self.assert_(c)
        
        
    def test_classref(self):
        #self.assert_(GetClassRef(testconf.context, reloadClass=False, raiseError=False)==text)
        self.assert_(GetClassRef(text, reloadClass=False, raiseError=False)==text)
        self.assert_(GetClassRef("nive.tests.test_helper.textxxxxxx", reloadClass=False, raiseError=False)==None)
        self.assertRaises(ImportError, GetClassRef, "nive.tests.test_helper.textxxxxxx", reloadClass=False, raiseError=True)
        

    def test_factory(self):
        #self.assert_(ClassFactory(testconf, reloadClass=False, raiseError=False)==text)
        c=testconf.copy()
        c.context=text
        self.assert_(ClassFactory(c, reloadClass=False, raiseError=False)==text)
        c=testconf.copy()
        c.context="nive.tests.test_helper.textxxxxxx"
        self.assert_(ClassFactory(c, reloadClass=False, raiseError=False)==None)
        c=testconf.copy()
        c.context="nive.tests.test_helper.textxxxxxx"
        self.assertRaises(ImportError, ClassFactory, c, reloadClass=False, raiseError=True)

        c=testconf.copy()
        c.extensions=(text1,text2,text3)
        self.assert_(len(ClassFactory(c, reloadClass=False, raiseError=False).mro())==6)
        c=testconf.copy()
        c.extensions=("text66666",text2,"text5555")
        self.assert_(len(ClassFactory(c, reloadClass=False, raiseError=False).mro())==4)
        c=testconf.copy()
        c.extensions=("nive.tests.test_helper.text1","nive.tests.test_helper.text2","nive.tests.test_helper.text3")
        self.assert_(len(ClassFactory(c, reloadClass=False, raiseError=False).mro())==6)


    def test_replace(self):
        alist = [Conf(id="1", value=123),Conf(id="2", value=456),Conf(id="3", value=789)]
        repl = Conf(id="2", value=999)
        new = ReplaceInListByID(alist, repl)
        self.assert_(new!=alist)
        self.assert_(new[1].value==999)


    def test_decorator(self):
        class someclass(object):
            pass
        conf = ViewModuleConf(id="test")
        newcls = DecorateViewClassWithViewModuleConf(conf, someclass)
        self.assert_(newcls.__configuration__)
        self.assert_(newcls.__configuration__().id=="test")

        newcls = DecorateViewClassWithViewModuleConf(conf, "nive.tests.test_helper.text")
        self.assert_(newcls.__configuration__)
        self.assert_(newcls.__configuration__().id=="test")


from nive.tests import db_app
from nive.tests import __local

class ListItemTest_db:

    def setUp(self):
        self._loadApp()
        r=self.app.root()

    def tearDown(self):
        self.app.Close()


    def test_listitems(self):
        self._loadApp()
        r=self.app.root()

        self.assert_(len(LoadListItems(self.app.GetFld("pool_type"), app=self.app, obj=None, pool_type=None, force=True))==3)
        LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"users"}), app=self.app)
        self.assert_(LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"groups"}), app=self.app))
        self.assert_(LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"languages"}), app=self.app))
        self.assert_(LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"countries"}), app=self.app))
        self.assert_(LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"types"}), app=self.app))
        self.assert_(LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"meta"}), app=self.app))
        #self.assert_(LoadListItems(FieldConf(id="test",datatype="list",settings={"codelist":"type:type1"})))


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
