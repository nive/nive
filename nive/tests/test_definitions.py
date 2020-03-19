
import unittest

from nive.definitions import *
from nive.helper import FormatConfTestFailure

# -----------------------------------------------------------------
class DummyClass(object):
    def hello(self):
        return "hello"


class baseConfTest(unittest.TestCase):

    def test_init(self):
        c = Conf()
        c = Conf(**{"test":1})
        self.assertTrue(c.test==1)
        c = Conf(test=2)
        self.assertTrue(c.test==2)
        self.assertTrue(repr(c).find("<Conf ")==0)
        
    def test_set(self):
        c = Conf()
        c["test"] = 1
        self.assertTrue(c.test==1)
        c.test=2
        self.assertTrue(c.test==2)
        c.update({"test":4})
        self.assertTrue(c.test==4)

    def test_get(self):
        c = Conf()
        c.test=1
        self.assertTrue(c["test"]==1)
        self.assertTrue(c.get("test")==1)
        self.assertTrue(c.get("aaaa",3)==3)
        c.aaa=2
        c.ccc="3"
        self.assertTrue(c.get("ccc")=="3")
        self.assertTrue(c.get("aaa")==2)
        self.assertTrue(c.get("ooo",5)==5)
        
    def test_copy(self):
        c = Conf()
        c.test=1
        c.aaa=2
        c.bbb="4"
        c.ccc="3"
        x=c.copy()
        self.assertTrue(x.test==1)
        self.assertTrue(x.aaa==2)
        self.assertTrue(x.bbb=="4")
        self.assertTrue(x.ccc=="3")
        x=c.copy(test=5,bbb=1)
        self.assertTrue(x.test==5)
        self.assertTrue(x.aaa==2)
        self.assertTrue(x.bbb==1)
        self.assertTrue(x.ccc=="3")

    def test_copy2(self):
        c = Conf()
        c.test=1
        c.aaa=2
        c.bbb="4"
        c.ccc="3"
        x = Conf(c)
        self.assertTrue(x.test==1)
        self.assertTrue(x.aaa==2)
        self.assertTrue(x.bbb=="4")
        self.assertTrue(x.ccc=="3")
        
    def test_fncs(self):
        c = Conf(Conf(inparent=1), **{"test":1})
        c2 = c.copy(**{"test2":2})
        k=list(c2.keys())
        self.assertTrue("test2" in c2)
        self.assertTrue("test" in c2)
        c2.update({"test":3})
        self.assertTrue(c2.get("test")==3)
        self.assertTrue(c2.test==3)
        c2.test=4
        self.assertTrue(c2.inparent==1)
        self.assertTrue(c2.test==4)

    def test_lock(self):
        c = Conf(Conf(inparent=1), **{"test":1})
        c.test=2
        c.lock()
        self.assertRaises(ConfigurationError, c.update, {"test":4})
        self.assertTrue(c.test==2)
        c.unlock()
        c.test=4
        self.assertTrue(c.test==4)



class ConfTest(unittest.TestCase):


    def test_obj0(self, **kw):
        testconf = DatabaseConf(
            context = "Sqlite3",
            fileRoot = "",
            dbName = "",
            host = "",
            port = "",
            user = "",
            password = "",
            useTrashcan = False,
            unicode = True,
            timeout = 3,
            dbCodePage = "utf-8"
        )
        self.assertTrue(len(testconf.test())==0)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))

    def test_obj1(self, **kw):
        testconf = AppConf(
            id = "test",
            title = "Test",
            description = "",
            context = "nive.tests.test_definitions.ConfTest",
            fulltextIndex = False,
        )
        self.assertTrue(testconf.id=="test")
        self.assertTrue(testconf.context=="nive.tests.test_definitions.ConfTest")
        self.assertTrue(len(testconf.test())==0)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))

    def test_obj2(self, **kw):
        testconf = FieldConf(
            id = "aaa",
            datatype = "string",
            size = 100,
            default = "aaa",
            listItems = None,
            settings = {},
            fulltext = True,
        )
        self.assertTrue(testconf.id=="aaa")
        self.assertTrue(testconf.size==100)
        self.assertTrue(testconf.fulltext==True)
        self.assertTrue(len(testconf.test())==0)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))

    def test_obj3(self, **kw):
        testconf = ObjectConf(
            id = "text",
            name = "Text",
            dbparam = "texts",
            context = "nive.tests.test_helper.text",
            extensions = (DummyClass,),
            selectTag = 1,
            description = ""
        )
        self.assertTrue(testconf.id=="text")
        self.assertTrue(testconf.name=="Text")
        self.assertTrue(testconf.selectTag==1)
        self.assertTrue(len(testconf.test())==0)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))

    def test_obj4(self, **kw):
        testconf = RootConf(
            id = "root",
            name = "Root",
            context = "nive.tests.test_definitions.ConfTest",
            default = True
        )
        self.assertTrue(testconf.id=="root")
        self.assertTrue(testconf.name=="Root")
        self.assertTrue(testconf.default==True)
        self.assertTrue(len(testconf.test())==0)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))

    def test_obj5(self, **kw):
        testconf = ViewModuleConf(
            id = "viewing",
            name = "Oh",
            static = ({"path":"here:static", "name":"static", "maxage":12000}),
            containment = "nive.tests.test_definitions.ConfTest",
            widgets = (WidgetConf(apply=(IObject,),viewmapper="test",widgetType=IWidgetConf,id="test"),),
        )
        self.assertTrue(testconf.id=="viewing")
        self.assertTrue(testconf.name=="Oh")
        self.assertTrue(testconf.containment=="nive.tests.test_definitions.ConfTest")
        self.assertTrue(len(testconf.test())==0)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))

    def test_obj5_bw_static(self, **kw):
        testconf = ViewModuleConf(
            id = "viewing",
            name = "Oh",
            static = "here:static",
            containment = "nive.tests.test_definitions.ConfTest",
            widgets = (WidgetConf(apply=(IObject,),viewmapper="test",widgetType=IWidgetConf,id="test"),),
        )
        self.assertTrue(testconf.id=="viewing")
        self.assertTrue(testconf.name=="Oh")
        self.assertTrue(testconf.containment=="nive.tests.test_definitions.ConfTest")
        self.assertTrue(len(testconf.test())==0)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))

    def test_obj6(self, **kw):
        testconf = ViewConf(
            attr = "test_obj6",
            name = "",
            context = "nive.tests.test_definitions.SystemTest",
            view = "nive.tests.test_definitions.ConfTest",
            renderer = None
        )
        self.assertTrue(testconf.attr=="test_obj6")
        self.assertTrue(testconf.name=="")
        self.assertTrue(testconf.view=="nive.tests.test_definitions.ConfTest")
        self.assertTrue(len(testconf.test())==0)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))

    def test_obj7(self, **kw):
        testconf = ToolConf(
            id = "tool",
            name = "Tool",
            context = "nive.tests.test_definitions.ConfTest",
        )
        self.assertTrue(testconf.id=="tool")
        self.assertTrue(testconf.name=="Tool")
        self.assertTrue(testconf.context=="nive.tests.test_definitions.ConfTest")
        self.assertTrue(len(testconf.test())==0)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))
    
    def test_obj8(self, **kw):
        testconf = ModuleConf(
            id = "module",
            name = "Module",
            context = "nive.tests.test_definitions.ConfTest",
            extensions = (DummyClass,),
            events = None,
            description = ""
        )
        self.assertTrue(len(testconf.test())==0)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))

    def test_obj9(self, **kw):
        testconf = WidgetConf(
            apply = (IObject,IApplication),
            viewmapper = "viewme",
            widgetType = IWidgetConf,
            name = "widget",
            id = "widget",
            sort = 100,
            description = ""
        )
        self.assertTrue(testconf.id=="widget")
        self.assertTrue(testconf.name=="widget")
        self.assertTrue(len(testconf.test())==0)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))
    
    def test_obj10(self, **kw):
        testconf = GroupConf(
            id = "group",
            name = "Group",
            hidden = True,
            description = ""
        )
        self.assertTrue(testconf.id=="group")
        self.assertTrue(testconf.name=="Group")
        self.assertTrue(testconf.hidden==True)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))
    
    def test_obj11(self, **kw):
        testconf = Conf(
            id = "category",
            name = "Category",
            hidden = True,
            description = ""
        )
        self.assertTrue(testconf.id=="category")
        self.assertTrue(testconf.name=="Category")
        self.assertTrue(testconf.hidden==True)
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))
    
    def test_obj12(self, **kw):
        testconf = PortalConf(
            portalDefaultUrl = "/website/",
            loginUrl = "/userdb/udb/login",
            forbiddenUrl = "/userdb/udb/login",
            logoutUrl = "/userdb/udb/logout",
            accountUrl = "/userdb/udb/update",
            favicon = "",
            robots = ""
        )
        self.assertTrue(testconf.portalDefaultUrl=="/website/")
        self.assertTrue(testconf.loginUrl == "/userdb/udb/login")
        self.assertTrue(testconf.forbiddenUrl == "/userdb/udb/login")
        self.assertTrue(testconf.logoutUrl == "/userdb/udb/logout")
        self.assertTrue(testconf.accountUrl == "/userdb/udb/update")
        self.assertTrue(testconf.robots == "")
        self.assertTrue(len(testconf.uid()))
        str(testconf) # may be empty
        self.assertTrue(repr(testconf))
    
        
        
class SystemTest(unittest.TestCase):

    def test_data(self, **kw):
        self.assertTrue(len(DataTypes))
        self.assertTrue(len(SystemFlds))
        self.assertTrue(len(UserFlds))
        self.assertTrue(len(UtilityFlds))
        self.assertTrue(len(WorkflowFlds))
        self.assertTrue(len(ReadonlySystemFlds))
        
    def test_setup(self):
        testlist = (SystemFlds,UserFlds,UtilityFlds,WorkflowFlds)
        for l in testlist:
            # test each field
            for field in l:
                report = field.test()
                if len(report):
                    raise ConfigurationError(FormatConfTestFailure(report))


    def test_structure1(self, **kw):
        for tbl in list(Structure.items()):
            self.assertTrue(tbl[0])
            self.assertTrue("fields" in tbl[1])
        


