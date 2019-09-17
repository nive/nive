import time
import unittest

from nive.application import *
from nive.definitions import Conf, GroupConf, DatabaseConf, ObjectConf, FieldConf, RootConf, ToolConf, AppConf, \
    ViewConf, ViewModuleConf, ModuleConf
from nive.definitions import IObject, IRootConf, IToolConf
from nive.workflow import WfProcessConf
from nive.portal import Portal
from nive.security import User

from nive.tool import _IGlobal, _GlobalObject

from nive.tests import db_app
from nive.tests import __local


mApp = AppConf(id="app", 
               groups=[GroupConf(id="g1",name="G1")], 
               categories=[Conf(id="c1",name="C1")],
               modules = [DatabaseConf(dbName=__local.ROOT+"nive3-testapp.db")],
               translations="nive:locale/")

mObject = ObjectConf(id="object", dbparam="object", name="Object",
                     data=(FieldConf(id="a1",datatype="string",name="A1"),FieldConf(id="a2",datatype="number",name="A2"),),
                     translations=("nive:locale/","nive:locale/"))

mRoot = RootConf(id="root")
mTool = ToolConf(id="tool", context="nive.tools.example.tool")
mViewm = ViewModuleConf(id="vm")
mView = ViewConf(id="v",context=mApp,view=mApp)
mMod = ModuleConf(id="mod", context=mApp)
mDb = DatabaseConf(dbName=__local.ROOT+"nive3-testapp2.db")

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


class testapp(Application):
    """
    """
    
def app():
    # uses sqlite
    app = testapp()
    app.Register(mApp2)
    app.Startup(None)
    portal = Portal()
    portal.Register(app, "nive")
    return app


# todo [3] move to registration_tests.py
class modTest(unittest.TestCase):

    def setUp(self):
        self.app = testapp()

    def tearDown(self):
        #db_app.emptypool(self.app)
        self.app.Close()

    def test_Register(self):
        self.app.Register(mApp)
        self.app.Register(mObject)
        self.assertTrue(self.app.configurationQuery.GetObjectConf(mObject.id)==mObject)
        self.app.Register(mRoot)
        self.assertTrue(self.app.configurationQuery.GetRootConf(mRoot.id)==mRoot)
        self.app.Register(mTool)
        self.assertTrue(self.app.configurationQuery.GetToolConf(mTool.id)==mTool)
        self.app.Register(mViewm)
        self.app.Register(mView)
        self.app.Register(mMod)
        self.app.Register(mDb)
        self.app.Register(ModuleConf(id="aaa"), provided=IObject, name="testttttt")
        
        # debug test
        self.app.debug = 0
        self.app.Register(mToolErr)
        
        self.app.Startup(None)
        self.assertTrue(self.app.db)
        self.app.Close()

    def test_startupErr(self):
        self.assertRaises(ConfigurationError, self.app.Startup, (None))

    def test_startup1(self):
        self.app.Register(mApp)
        self.app.Startup(None, debug=True)
        self.assertTrue(self.app.db)
        c = self.app.db.Execute("select id from pool_meta")
        c.close()
        self.app.Close()

    def test_startup2(self):
        self.app.Register(mApp)
        self.app.Setup()
        self.app.StartRegistration(None)
        self.app.FinishRegistration(None)
        self.app.Run()
        self.assertTrue(self.app.db)
        self.app.Close()

    def test_include2(self):
        self.app.Register(mApp2)
        self.app.Startup(None)
        self.assertTrue(self.app.db)

    def test_includefailure1(self):
        self.app.Register(mAppErr)
        #no database: self.app.Register(dbConfiguration2)
        self.assertRaises(ConfigurationError, self.app.Startup, None)



class simpleAppTest(unittest.TestCase):

    def test_debug(self):
        app = testapp()
        app.Register(mApp2)
        app.Startup(None)
        app.Close()
        
    def test_nometa(self):
        app = testapp()
        c=AppConf(mApp2)
        c.meta=[]
        app.Register(c)
        app.Startup(None)
        app.Close()

    def test_db(self):
        app = testapp()
        app.Register(mApp2)
        v,r=app.TestDB()
        self.assertFalse(v)
        app.Close()


class appTest(unittest.TestCase):
    
    def setUp(self):
        self.app = testapp()
        self.app.Register(mApp2)
        self.portal = Portal()
        self.portal.Register(self.app, "nive")
        self.app.Startup(None)

    def tearDown(self):
        #db_app.emptypool(self.app)
        self.app.Close()


    def test_include2(self):
        s = self.app._structure.structure
        self.assertTrue("pool_meta" in s)
        self.assertTrue("object" in s)
        self.assertTrue(len(s["pool_meta"])>10)
        self.assertTrue(len(s["object"])==2)
        pass


    def test_del(self):
        self.app.__del__()
        
    def test_getitem(self):
        self.assertTrue(self.app["root"])
        try:
            self.app["no_root"]
            self.assertTrue(False)
        except KeyError:
            pass
        conf=self.app.root.configuration
        conf.unlock()
        conf.urlTraversal=False
        conf.lock()
        try:
            self.app["root"]
            conf.unlock()
            conf.urlTraversal=True
            conf.lock()
            self.assertTrue(False)
        except KeyError:
            conf.unlock()
            conf.urlTraversal=True
            conf.lock()
            pass
        
    def test_props(self):
        self.assertTrue(self.app.root)
        self.assertTrue(self.app.portal)
        self.assertTrue(self.app.db)
        self.assertTrue(self.app.app)
    
    def test_roots(self):
        self.assertTrue(self.app.root)
        self.assertTrue(self.app.GetRoot(name=""))
        self.assertTrue(self.app.GetRoot(name="root"))
        self.assertTrue(self.app.GetRoot(name="aaaaaaaa")==None)

        self.assertTrue(self.app.__getitem__("root"))
        self.assertTrue(self.app.GetRoot(name="root"))
        self.assertTrue(len(self.app.GetRoots())==1)

    def test_tools(self):
        self.assertTrue(self.app.GetTool("tool"))
        self.assertTrue(self.app.GetTool("nive.tools.example"))
        self.assertRaises(ImportError, self.app.GetTool, ("no_tool"))
        self.assertRaises(ImportError, self.app.GetTool, (""))

    def test_wfs(self):
        self.assertFalse(self.app.GetWorkflow(""))
        self.assertFalse(self.app.GetWorkflow("no_wf"))
        self.assertFalse(self.app.GetWorkflow("wfexample"))
        self.app.configuration.unlock()
        self.app.configuration.workflowEnabled = True
        self.assertTrue(self.app.GetWorkflow("nive.tests.test_workflow.wf1"))
        self.app.configuration.workflowEnabled = False
        self.app.configuration.lock()

    def test_groups(self):
        self.assertTrue(self.app.GetGroups(sort="name", visibleOnly=False))
        self.assertTrue(self.app.GetGroups(sort="name", visibleOnly=True))
        self.assertTrue(self.app.GetGroups(sort="id", visibleOnly=False))
        self.assertTrue(self.app.GetGroupName("g1")=="G1")
        self.assertTrue(self.app.GetGroupName("no_group")=="")


class appFactoryTest(unittest.TestCase):

    def setUp(self):
        self.app = testapp()
        self.app.Register(mApp2)
        self.portal = Portal()
        self.portal.Register(self.app, "nive")
        self.app.Startup(None)

    def tearDown(self):
        #db_app.emptypool(self.app)
        self.app.Close()


    def test_structure(self):
        self.app._LoadStructure(forceReload=False)
        self.assertTrue(self.app._structure)
        self.app._LoadStructure(forceReload=True)
        self.assertTrue(self.app._structure)

    def test_factory(self):
        self.assertTrue(self.app.factory.GetDataPoolObj())
        self.assertTrue(self.app.factory.GetRootObj("root"))
        self.app.factory.CloseRootObj(name="root")
        self.assertTrue(self.app.factory.GetRootObj("root"))
        self.assertTrue(self.app.factory.GetToolObj("nive.tools.example", None))


class appConfigurationQueryTest(unittest.TestCase):

    def setUp(self):
        self.app = testapp()
        self.app.Register(mApp2)
        self.portal = Portal()
        self.portal.Register(self.app, "nive")
        self.app.Startup(None)

    def tearDown(self):
        #db_app.emptypool(self.app)
        self.app.Close()


    def test_include2(self):
        s = self.app._structure.structure
        self.assertTrue("pool_meta" in s)
        self.assertTrue("object" in s)
        self.assertTrue(len(s["pool_meta"]) > 10)
        self.assertTrue(len(s["object"]) == 2)
        pass

    def test_del(self):
        self.app.__del__()

    def test_getitem(self):
        self.assertTrue(self.app["root"])
        try:
            self.app["no_root"]
            self.assertTrue(False)
        except KeyError:
            pass
        conf = self.app.root.configuration
        conf.unlock()
        conf.urlTraversal = False
        conf.lock()
        try:
            self.app["root"]
            conf.unlock()
            conf.urlTraversal = True
            conf.lock()
            self.assertTrue(False)
        except KeyError:
            conf.unlock()
            conf.urlTraversal = True
            conf.lock()
            pass

    def test_confs(self):
        self.assertTrue(self.app.configurationQuery.QueryConf(IRootConf))
        self.assertTrue(self.app.configurationQuery.QueryConf("nive.definitions.IRootConf"))
        self.assertTrue(self.app.configurationQuery.QueryConf(IToolConf, _GlobalObject()))
        self.assertFalse(self.app.configurationQuery.QueryConf("nive.definitions.no_conf"))

        self.assertTrue(self.app.configurationQuery.QueryConfByName(IRootConf, "root"))
        self.assertTrue(self.app.configurationQuery.QueryConfByName("nive.definitions.IRootConf", "root"))
        self.assertTrue(self.app.configurationQuery.QueryConfByName(IToolConf, "tool", _GlobalObject()))
        self.assertFalse(self.app.configurationQuery.QueryConfByName("nive.definitions.no_conf", "root"))

        self.assertTrue(self.app.NewModule(IRootConf, "root"))
        self.assertTrue(self.app.NewModule("nive.definitions.IRootConf", "root"))
        self.assertTrue(self.app.NewModule(IToolConf, "tool", _GlobalObject()))
        self.assertFalse(self.app.NewModule("nive.definitions.no_conf", "root"))

    def test_rootconfs(self):
        self.assertTrue(self.app.configurationQuery.GetRootConf(name=""))
        self.assertTrue(self.app.configurationQuery.GetRootConf(name="root"))
        self.assertTrue(len(self.app.configurationQuery.GetAllRootConfs()))
        self.assertTrue(len(self.app.GetRootNames()) == 1)
        self.assertTrue(self.app.rootname == "root")

    def test_objconfs(self):
        self.assertTrue(self.app.configurationQuery.GetObjectConf("object", skipRoot=False))
        self.assertTrue(self.app.configurationQuery.GetObjectConf("root", skipRoot=True) == None)
        self.assertTrue(self.app.configurationQuery.GetObjectConf("oooooh", skipRoot=False) == None)
        self.assertTrue(len(self.app.configurationQuery.GetAllObjectConfs(visibleOnly=False)) == 1)
        self.assertTrue(self.app.configurationQuery.GetTypeName("object") == "Object")

    def test_toolconfs(self):
        self.assertTrue(self.app.configurationQuery.GetToolConf("tool"))
        self.assertTrue(len(self.app.configurationQuery.GetAllToolConfs()))

    def test_categoriesconf(self):
        self.assertTrue(self.app.configurationQuery.GetCategory(categoryID="c1"))
        self.assertTrue(len(self.app.configurationQuery.GetAllCategories(sort="name", visibleOnly=False)) == 1)
        self.assertTrue(self.app.configurationQuery.GetCategoryName("c1") == "C1")
        self.assertTrue(self.app.configurationQuery.GetCategoryName("no_cat") == "")

    def test_flds(self):
        self.assertTrue(self.app.configurationQuery.GetFld("pool_type", typeID=None))
        self.assertTrue(self.app.configurationQuery.GetFld("aaaaa", typeID=None) == None)
        self.assertTrue(self.app.configurationQuery.GetFld("pool_stag", typeID="object"))
        self.assertTrue(self.app.configurationQuery.GetFld("a1", typeID="object"))
        self.assertTrue(self.app.configurationQuery.GetFld("a1", typeID=None) == None)
        self.assertTrue(self.app.configurationQuery.GetFld("a2", typeID="object"))
        self.assertTrue(self.app.configurationQuery.GetFld("a2", typeID="ooooo") == None)
        self.assertTrue(self.app.configurationQuery.GetFld("ooooo", typeID="object") == None)

        self.assertTrue(self.app.configurationQuery.GetFldName("a2", typeID="object") == "A2")
        self.assertTrue(self.app.configurationQuery.GetObjectFld("a1", "object"))
        self.assertTrue(len(self.app.configurationQuery.GetAllObjectFlds("object")) == 2)
        self.assertTrue(self.app.configurationQuery.GetMetaFld("pool_type"))
        self.assertTrue(len(self.app.configurationQuery.GetAllMetaFlds(ignoreSystem=True)))
        self.assertTrue(len(self.app.configurationQuery.GetAllMetaFlds(ignoreSystem=False)))
        self.assertTrue(self.app.configurationQuery.GetMetaFldName("pool_type") == "Type")
        self.assertTrue(self.app.configurationQuery.GetMetaFldName("no_field") == "")

    def test_flds_conf(self):
        self.assertTrue(self.app.configurationQuery.GetFld(FieldConf(id="pool_type"), typeID=None))
        self.assertTrue(self.app.configurationQuery.GetFld(FieldConf(id="aaaaa"), typeID=None) == None)
        self.assertTrue(self.app.configurationQuery.GetFld(FieldConf(id="pool_stag"), typeID="object"))
        self.assertTrue(self.app.configurationQuery.GetFld(FieldConf(id="a1"), typeID="object"))
        self.assertTrue(self.app.configurationQuery.GetFld(FieldConf(id="a1"), typeID=None) == None)
        self.assertTrue(self.app.configurationQuery.GetFld(FieldConf(id="a2"), typeID="object"))
        self.assertTrue(self.app.configurationQuery.GetFld(FieldConf(id="a2"), typeID="ooooo") == None)
        self.assertTrue(self.app.configurationQuery.GetFld(FieldConf(id="ooooo"), typeID="object") == None)

        self.assertTrue(self.app.configurationQuery.GetObjectFld(FieldConf(id="a1"), "object"))
        self.assertTrue(self.app.configurationQuery.GetMetaFld(FieldConf(id="pool_type")))

    def test_structure(self):
        self.app._LoadStructure(forceReload=False)
        self.assertTrue(self.app._structure)
        self.app._LoadStructure(forceReload=True)
        self.assertTrue(self.app._structure)



class appTest_db:
    
    def setUp(self):
        self._loadApp([mWfObj,mToolObj])
        r = self.app.root
        o = db_app.createObj1(r)
        self.oid = o.id
        
    def tearDown(self):
        self._closeApp(True)


    def test_db(self):
        v,r=self.app.TestDB()
        self.assertTrue(v,r)
        self.app.db.connection.close()
        v,r=self.app.TestDB()
        self.assertTrue(v,r)

    
    def test_cacheddb(self):
        conn=self.app.db.usedconnection
        self.assertTrue(conn)
        
        from nive.application import Application
        from nive.tests.db_app import appconf
        a = Application()
        a.Register(appconf)
        a.Register(conn.configuration)
        a.Startup(None, cachedDbConnection=conn)
        v,r=self.app.TestDB()
        self.assertTrue(v,r)

        
    def test_dbfncs(self):
        v,r=self.app.TestDB()
        self.assertTrue(v,r)
        self.assertTrue(self.app.db)
        self.assertTrue(self.app.GetDB())
        self.assertTrue(self.app.db.connection.VerifyConnection())
        self.assertTrue(len(self.app.Query("select id from pool_meta", values = [])))
        ph = self.app.db.placeholder
        self.assertTrue(len(self.app.Query("select id from pool_meta where pool_type="+ph, values = ["type1"])))
        v,r=self.app.TestDB()
        self.assertTrue(v,r)
        self.assertTrue(self.app.NewConnection())
        self.assertTrue(self.app.NewDBApi())
    

    def test_real_tools(self):
        o=self.app.obj(self.oid, rootname = "")
        self.assertTrue(o)
        # unregistered tool
        self.assertTrue(self.app.GetTool("nive.tools.example", o))
        # registered tool
        self.assertTrue(self.app.GetTool("tool", o))


    def test_real_wfs(self):
        o=self.app.obj(self.oid, rootname = "")
        self.assertTrue(o)
        self.app.configuration.unlock()
        self.app.configuration.workflowEnabled = True
        # unregistered workflow
        self.assertTrue(self.app.GetWorkflow("nive.tests.test_workflow.wf1", o))
        # registered workflow
        self.assertTrue(self.app.GetWorkflow("wf", o))
        self.app.configuration.workflowEnabled = False
        self.app.configuration.lock()
        


    def test_real_objects(self):
        id = self.oid

        self.assertTrue(self.app.obj(id))
        self.assertTrue(self.app.obj(id, rootname = ""))
        self.assertTrue(self.app.obj(id, rootname = "root"))
        self.assertFalse(self.app.obj(id, rootname = "no_root"))
        self.assertTrue(self.app.obj(id, rootname = ""))
        self.assertTrue(self.app.obj(id, rootname = "root"))
        self.assertFalse(self.app.obj(id, rootname = "no_root"))
        
        # should reopen the connection
        self.app.Close()
        self.app.db.usedconnection.IsConnected()
        self.assertTrue(self.app.obj(id))


    def test_sysvalues(self):
        self.app.DeleteSysValue("testvalue")
        self.assertTrue(self.app.LoadSysValue("testvalue")==None)
        self.app.StoreSysValue("testvalue", "12345")
        self.assertTrue(self.app.LoadSysValue("testvalue")=="12345")
        self.app.StoreSysValue("testvalue", "67890")
        self.assertTrue(self.app.LoadSysValue("testvalue")=="67890")
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


