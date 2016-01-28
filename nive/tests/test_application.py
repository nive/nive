import time
import unittest

from nive.application import *
from nive.definitions import *
from nive.workflow import WfProcessConf
from nive.helper import *
from nive.events import Events
from nive.portal import Portal
from nive.components import baseobjects
from nive.security import User

from nive.tool import _IGlobal, _GlobalObject

from nive.tests import db_app
from nive.tests import __local


mApp = AppConf(id="app", 
               groups=[GroupConf(id="g1",name="G1")], 
               categories=[Conf(id="c1",name="C1")],
               modules = [DatabaseConf(dbName="test")],
               translations="nive:locale/")

mObject = ObjectConf(id="object", dbparam="object", name="Object",
                     data=(FieldConf(id="a1",datatype="string",name="A1"),FieldConf(id="a2",datatype="number",name="A2"),),
                     translations=("nive:locale/","nive:locale/"))

mRoot = RootConf(id="root")
mTool = ToolConf(id="tool", context="nive.tools.example.tool")
mViewm = ViewModuleConf(id="vm")
mView = ViewConf(id="v",context=mApp,view=mApp)
mMod = ModuleConf(id="mod", context=mApp)
mDb = DatabaseConf(dbName="test")

mWfObj = WfProcessConf("nive.tests.test_workflow.wf1", id="wf", apply=(IObject,))
mToolObj = ToolConf("nive.tools.example", id="tool", apply=(IObject,))

mToolErr = ToolConf(id="tool", context="nive.tools.no_example")


mApp2 = AppConf(id="app2", 
                context="nive.tests.test_application.testapp",
                modules=[mObject,mRoot,mTool,mViewm,mView,mMod,mDb], 
                groups=[GroupConf(id="g1",name="G1")], 
                categories=[Conf(id="c1",name="C1")]
)

mAppErr = AppConf(id="app2", 
                context="nive.tests.test_application.testapp",
                modules=[mObject,mRoot,mTool,mViewm,mView,mMod], 
                groups=[GroupConf(id="g1",name="G1")], 
                categories=[Conf(id="c1",name="C1")]
)


class testapp(Application, Registration, Configuration, AppFactory, Events):
    """
    """
    
def app():
    app = testapp()
    app.Register(mApp2)
    app.Startup(None)
    portal = Portal()
    portal.Register(app, "nive")
    return app



class modTest(unittest.TestCase):
    
    def setUp(self):
        self.app = testapp()

    def tearDown(self):
        pass


    def test_Register(self):
        self.app.Register(mApp)
        self.app.Register(mObject)
        self.assert_(self.app.GetObjectConf(mObject.id)==mObject)
        self.app.Register(mRoot)
        self.assert_(self.app.GetRootConf(mRoot.id)==mRoot)
        self.app.Register(mTool)
        self.assert_(self.app.GetToolConf(mTool.id)==mTool)
        self.app.Register(mViewm)
        self.app.Register(mView)
        self.app.Register(mMod)
        self.app.Register(mDb)
        self.app.Register(ModuleConf(id="aaa"), provided=IObject, name="testttttt")
        
        # python modules
        self.assertRaises(TypeError, self.app.Register, (testapp()))
        self.app.Register(baseobjects.ApplicationBase())
        
        # debug test
        self.app.debug = 1
        self.app.Register(mToolErr)
        
        self.app.Startup(None)
        self.assert_(self.app.db)
        self.app.Close()

    def test_startupErr(self):
        self.assertRaises(ConfigurationError, self.app.Startup, (None))

    def test_startup1(self):
        self.app.Register(mApp)
        self.app.Startup(None, True)
        self.assert_(self.app.db)
        self.app.Close()

    def test_startup2(self):
        self.app.Register(mApp)
        self.app.Setup(True)
        self.app.StartRegistration(None)
        self.app.FinishRegistration(None)
        self.app.Run()
        self.assert_(self.app.db)
        self.app.Close()

    def test_include2(self):
        self.app.Register(mApp2)
        self.app.Startup(None)
        self.assert_(self.app.db)

    def test_includefailure1(self):
        self.app.Register(mAppErr)
        #no database: self.app.Register(dbConfiguration2)
        self.assertRaises(ConfigurationError, self.app.Startup, None)



class simpleAppTest(unittest.TestCase):

    def test_debug(self):
        app = testapp()
        app.Register(mApp2)
        app.Startup(None, debug=True)
        
    def test_nometa(self):
        app = testapp()
        c=AppConf(mApp2)
        c.meta=[]
        app.Register(c)
        app.Startup(None, debug=True)

    def test_db(self):
        app = testapp()
        app.Register(mApp2)
        v,r=app.TestDB()
        self.assertFalse(v)


class appTest(unittest.TestCase):
    
    def setUp(self):
        self.app = testapp()
        self.app.Register(mApp2)
        self.portal = Portal()
        self.portal.Register(self.app, "nive")
        self.app.Startup(None)

    def tearDown(self):
        pass


    def test_include2(self):
        s = self.app._structure.structure
        self.assert_("pool_meta" in s)
        self.assert_("object" in s)
        self.assert_(len(s["pool_meta"])>10)
        self.assert_(len(s["object"])==2)
        pass


    def test_fncs(self):
        self.assert_(self.app.GetVersion())
        self.assert_(self.app.CheckVersion())
        self.assert_(self.app.GetApp())
        

    def test_del(self):
        self.app.__del__()
        
    def test_getitem(self):
        self.assert_(self.app["root"])
        try:
            self.app["no_root"]
            self.assert_(False)
        except KeyError:
            pass
        conf=self.app.root().configuration
        conf.unlock()
        conf.urlTraversal=False
        conf.lock()
        try:
            self.app["root"]
            conf.unlock()
            conf.urlTraversal=True
            conf.lock()
            self.assert_(False)
        except KeyError:
            conf.unlock()
            conf.urlTraversal=True
            conf.lock()
            pass
        
    def test_props(self):
        self.assert_(self.app.root())
        self.assert_(self.app.portal)
        self.assert_(self.app.db)
        self.assert_(self.app.app)
    
    def test_roots(self):
        self.assert_(self.app.root(name=""))
        self.assert_(self.app.root(name="root"))
        self.assert_(self.app.root(name="aaaaaaaa")==None)

        self.assert_(self.app.__getitem__("root"))
        self.assert_(self.app.GetRoot(name="root"))
        self.assert_(len(self.app.GetRoots())==1)

    def test_tools(self):
        self.assert_(self.app.GetTool("tool"))
        self.assert_(self.app.GetTool("nive.tools.example"))
        self.assertRaises(ImportError, self.app.GetTool, ("no_tool"))
        self.assertRaises(ImportError, self.app.GetTool, (""))

    def test_wfs(self):
        self.assertFalse(self.app.GetWorkflow(""))
        self.assertFalse(self.app.GetWorkflow("no_wf"))
        self.assertFalse(self.app.GetWorkflow("wfexample"))
        self.app.configuration.unlock()
        self.app.configuration.workflowEnabled = True
        self.assert_(self.app.GetWorkflow("nive.tests.test_workflow.wf1"))
        self.app.configuration.workflowEnabled = False
        self.app.configuration.lock()

    def test_confs(self):
        self.assert_(self.app.QueryConf(IRootConf))
        self.assert_(self.app.QueryConf("nive.definitions.IRootConf"))
        self.assert_(self.app.QueryConf(IToolConf, _GlobalObject()))
        self.assertFalse(self.app.QueryConf("nive.definitions.no_conf"))
        
        self.assert_(self.app.QueryConfByName(IRootConf, "root"))
        self.assert_(self.app.QueryConfByName("nive.definitions.IRootConf", "root"))
        self.assert_(self.app.QueryConfByName(IToolConf, "tool", _GlobalObject()))
        self.assertFalse(self.app.QueryConfByName("nive.definitions.no_conf", "root"))

        self.assert_(self.app.Factory(IRootConf, "root"))
        self.assert_(self.app.Factory("nive.definitions.IRootConf", "root"))
        self.assert_(self.app.Factory(IToolConf, "tool", _GlobalObject()))
        self.assertFalse(self.app.Factory("nive.definitions.no_conf", "root"))
        
    def test_rootconfs(self):
        self.assert_(self.app.GetRootConf(name=""))
        self.assert_(self.app.GetRootConf(name="root"))
        self.assert_(len(self.app.GetAllRootConfs()))
        self.assert_(len(self.app.GetRootIds())==1)
        self.assert_(self.app.GetDefaultRootName()=="root")

    def test_objconfs(self):
        self.assert_(self.app.GetObjectConf("object", skipRoot=False))
        self.assert_(self.app.GetObjectConf("root", skipRoot=True)==None)
        self.assert_(self.app.GetObjectConf("oooooh", skipRoot=False)==None)
        self.assert_(len(self.app.GetAllObjectConfs(visibleOnly = False))==1)
        self.assert_(self.app.GetTypeName("object")=="Object")

    def test_toolconfs(self):
        self.assert_(self.app.GetToolConf("tool"))
        self.assert_(len(self.app.GetAllToolConfs()))
        
    def test_categoriesconf(self):
        self.assert_(self.app.GetCategory(categoryID = "c1"))
        self.assert_(len(self.app.GetAllCategories(sort=u"name", visibleOnly=False))==1)
        self.assert_(self.app.GetCategoryName("c1")=="C1")
        self.assert_(self.app.GetCategoryName("no_cat")=="")

    def test_groups(self):
        self.assert_(self.app.GetGroups(sort=u"name", visibleOnly=False))
        self.assert_(self.app.GetGroups(sort=u"name", visibleOnly=True))
        self.assert_(self.app.GetGroups(sort=u"id", visibleOnly=False))
        self.assert_(self.app.GetGroupName("g1")=="G1")
        self.assert_(self.app.GetGroupName("no_group")=="")

    def test_flds(self):
        self.assert_(self.app.GetFld("pool_type", typeID = None))
        self.assert_(self.app.GetFld("aaaaa", typeID = None)==None)
        self.assert_(self.app.GetFld("pool_stag", typeID = "object"))
        self.assert_(self.app.GetFld("a1", typeID = "object"))
        self.assert_(self.app.GetFld("a1", typeID = None)==None)
        self.assert_(self.app.GetFld("a2", typeID = "object"))
        self.assert_(self.app.GetFld("a2", typeID = "ooooo")==None)
        self.assert_(self.app.GetFld("ooooo", typeID = "object")==None)
        
        self.assert_(self.app.GetFldName("a2", typeID = "object")=="A2")
        self.assert_(self.app.GetObjectFld("a1", "object"))
        self.assert_(len(self.app.GetAllObjectFlds("object"))==2)
        self.assert_(self.app.GetMetaFld("pool_type"))
        self.assert_(len(self.app.GetAllMetaFlds(ignoreSystem = True)))
        self.assert_(len(self.app.GetAllMetaFlds(ignoreSystem = False)))
        self.assert_(self.app.GetMetaFldName("pool_type")=="Type")
        self.assert_(self.app.GetMetaFldName("no_field")=="")
        
    def test_flds_conf(self):
        self.assert_(self.app.GetFld(FieldConf(id="pool_type"), typeID = None))
        self.assert_(self.app.GetFld(FieldConf(id="aaaaa"), typeID = None)==None)
        self.assert_(self.app.GetFld(FieldConf(id="pool_stag"), typeID = "object"))
        self.assert_(self.app.GetFld(FieldConf(id="a1"), typeID = "object"))
        self.assert_(self.app.GetFld(FieldConf(id="a1"), typeID = None)==None)
        self.assert_(self.app.GetFld(FieldConf(id="a2"), typeID = "object"))
        self.assert_(self.app.GetFld(FieldConf(id="a2"), typeID = "ooooo")==None)
        self.assert_(self.app.GetFld(FieldConf(id="ooooo"), typeID = "object")==None)

        self.assert_(self.app.GetObjectFld(FieldConf(id="a1"), "object"))
        self.assert_(self.app.GetMetaFld(FieldConf(id="pool_type")))

    def test_structure(self):
        self.app._LoadStructure(forceReload = False)
        self.assert_(self.app._structure)
        self.app._LoadStructure(forceReload = True)
        self.assert_(self.app._structure)

    def test_factory(self):
        self.assert_(self.app._GetDataPoolObj())
        self.assert_(self.app._GetRootObj("root"))
        self.app._CloseRootObj(name="root")
        self.assert_(self.app._GetRootObj("root"))
        self.assert_(self.app._GetToolObj("nive.tools.example", None))



class appTest_db:
    
    def setUp(self):
        self._loadApp([mWfObj,mToolObj])
        r = self.app.root()
        o = db_app.createObj1(r)
        self.oid = o.id
        
    def tearDown(self):
        user = User(u"test")
        if self.oid:
            self.app.root().Delete(self.oid, user=user)
        self.app.Close()


    def test_db(self):
        v,r=self.app.TestDB()
        self.assert_(v,r)
        self.app.db.connection.close()
        v,r=self.app.TestDB()
        self.assert_(v,r)

    
    def test_cacheddb(self):
        conn=self.app.db.usedconnection
        self.assert_(conn)
        
        from nive.components.objects.base import ApplicationBase
        from nive.tests.db_app import appconf
        a = ApplicationBase()
        a.Register(appconf)
        a.Register(conn.configuration)
        a.Startup(None, cachedDbConnection=conn)
        v,r=self.app.TestDB()
        self.assert_(v,r)

        
    def test_dbfncs(self):
        v,r=self.app.TestDB()
        self.assert_(v,r)
        self.assert_(self.app.db)
        self.assert_(self.app.GetDB())
        self.assert_(self.app.db.connection.VerifyConnection())
        self.assert_(len(self.app.Query("select id from pool_meta", values = [])))
        ph = self.app.db.placeholder
        self.assert_(len(self.app.Query("select id from pool_meta where pool_type="+ph, values = ["type1"])))
        v,r=self.app.TestDB()
        self.assert_(v,r)
        self.assert_(self.app.NewConnection())
        self.assert_(self.app.NewDBApi())
    

    def test_real_tools(self):
        o=self.app.obj(self.oid, rootname = "")
        self.assert_(o)
        # unregistered tool
        self.assert_(self.app.GetTool("nive.tools.example", o))
        # registered tool
        self.assert_(self.app.GetTool("tool", o))


    def test_real_wfs(self):
        o=self.app.obj(self.oid, rootname = "")
        self.assert_(o)
        self.app.configuration.unlock()
        self.app.configuration.workflowEnabled = True
        # unregistered workflow
        self.assert_(self.app.GetWorkflow("nive.tests.test_workflow.wf1", o))
        # registered workflow
        self.assert_(self.app.GetWorkflow("wf", o))
        self.app.configuration.workflowEnabled = False
        self.app.configuration.lock()
        


    def test_real_objects(self):
        id = self.oid

        self.assert_(self.app.LookupObj(id))
        self.assert_(self.app.LookupObj(id, rootname = ""))
        self.assert_(self.app.LookupObj(id, rootname = "root"))
        self.assertFalse(self.app.LookupObj(id, rootname = "no_root"))
        self.assert_(self.app.obj(id, rootname = ""))
        self.assert_(self.app.obj(id, rootname = "root"))
        self.assertFalse(self.app.obj(id, rootname = "no_root"))
        
        # should reopen the connection
        self.app.Close()
        self.app.db.usedconnection.IsConnected()
        self.assert_(self.app.LookupObj(id))


    def test_sysvalues(self):
        self.app.DeleteSysValue("testvalue")
        self.assert_(self.app.LoadSysValue("testvalue")==None)
        self.app.StoreSysValue("testvalue", "12345")
        self.assert_(self.app.LoadSysValue("testvalue")=="12345")
        self.app.StoreSysValue("testvalue", "67890")
        self.assert_(self.app.LoadSysValue("testvalue")=="67890")
        self.app.DeleteSysValue("testvalue")




class appTest_db_sqlite(appTest_db, __local.SqliteTestCase):
    """
    see tests.__local
    """


class appTest_db_mysql(appTest_db, __local.MySqlTestCase):
    """
    see tests.__local
    """

class appTest_db_pg(appTest_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """


