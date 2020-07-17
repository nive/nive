

from nive.tests import __local
from nive.tests import db_app 

from nive.security import User


class TestSecurityContext(object):
    ppp="view"
    def has_permission(self,p,o):
        return p==self.ppp

class containerTest_db:
    
    def setUp(self):
        self._loadApp()
        self.remove=[]

    def tearDown(self):
        self._closeApp(True, True)


    def test_basics(self):
        #print "Testing shortcuts"
        a=self.app
        user = User("test")
        ccc = a.db.GetCountEntries()
        self.assertTrue(a.root)
        self.assertTrue(a.db)
        r = a.root
        o1 = db_app.createObj1(r)
        o2 = db_app.createObj2(o1)
        id1 = o1.id
        id2 = o2.id
        self.remove.append(id1)
        self.assertTrue(a.obj(id1))
        self.assertTrue(r.__getitem__(str(id1)))
        self.assertTrue(r.obj(id1))
        self.assertTrue(o1.obj(id2))
        self.assertTrue(o1.db==a.db)
        self.assertTrue(r.db==a.db)
        self.assertTrue(o1.relpath)
        self.assertTrue(o2.relpath)

        self.assertTrue(r.IsTypeAllowed("type1", user=user))
        self.assertTrue(o1.IsTypeAllowed("type1", user=user))
        
        try:
            o2.IsTypeAllowed("type1", user=user)
            self.assertTrue(False, "Object is not a container: IsTypeAllowed")
        except AttributeError:
            pass
        self.assertTrue(r.GetAllowedTypes(user=user))
        self.assertTrue(o1.GetAllowedTypes(user=user))
        r.Delete(id1, user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        

    def test_createroots(self):
        #print "Testing root basics"
        a=self.app
        ccc = a.db.GetCountEntries()
        r=db_app.root(a)
        user = User("test")
        #rootValues()
        self.assertTrue(r.GetID()<=0)
        self.assertTrue(r.GetTypeID())
        self.assertTrue(r.GetTitle())
        self.assertTrue(r.GetPath())
        #rootParents()
        self.assertTrue(len(r.GetParents())==0)
        self.assertTrue(len(r.GetParentTitles())==0)
        self.assertTrue(len(r.GetParentPaths())==0)
        self.assertEqual(ccc, a.db.GetCountEntries())
        

    def test_createobjs_kws(self):
        #print "Testing new object creation, values and delete"
        a=self.app
        r=db_app.root(a)
        # create
        user = User("test")
        type = "type3"
        data = {}
        user = User("test")
        o = r.Create(type, data=data, user=user, custom=123)
        self.assertTrue(o.__kws_test__.get("custom")==123)


    def test_createobjs(self):
        #print "Testing new object creation, values and delete"
        a=self.app
        r=db_app.root(a)
        # create
        user = User("test")
        ccc = a.db.GetCountEntries()

        o1 = db_app.createObj1(r)
        # -> o1
        o3 = db_app.createObj1(o1)
        o5 = db_app.createObj3(o1)
        o4 = db_app.createObj1(o3)
        o6 = db_app.createObj2(o5)

        o2 = db_app.createObj2(r)
        #import pdb
        #pdb.set_trace()

        # todo [3] fix containment non container
        #self.assertRaises(ContainmentError, createObj1, o5)
        
        self.assertTrue(r.IsContainer())
        self.assertTrue(o1.IsContainer())
        self.assertTrue(o2.IsContainer()==False)
        self.assertTrue(o1.GetID())
        self.assertTrue(o1.GetTypeID()=="type1")
        self.assertTrue(o1.GetTitle()=="")
        self.assertTrue(o1.GetPath())
        #Parents()
        self.assertTrue(len(o1.GetParents())==1)
        self.assertTrue(len(o1.GetParentIDs())==1)
        self.assertTrue(len(o1.GetParentTitles())==1)
        self.assertTrue(len(o1.GetParentPaths())==1)
        self.assertTrue(len(o1.GetObjsList())==2)

        self.assertTrue(o4.parent==o3)
        self.assertTrue(len(o4.GetParents())==3)
        self.assertTrue(len(o4.GetParentIDs())==3)
        self.assertTrue(len(o4.GetParentTitles())==3)
        self.assertTrue(len(o4.GetParentPaths())==3)
        self.assertTrue(len(o3.GetObjsList())==1)
        self.assertTrue(o3.GetObj(o4.GetID()))

        self.assertEqual(ccc+6, db_app.statdb(a))

        newO = r.Duplicate(o1, user)
        self.assertTrue(newO)
        self.assertTrue(newO.IsContainer())
        self.assertTrue(newO.GetID())
        self.assertTrue(newO.GetTypeID()=="type1")
        self.assertTrue(newO.GetTitle()=="")
        self.assertTrue(newO.GetPath())
        #Parents()
        self.assertTrue(len(newO.GetParents())==1)
        self.assertTrue(len(newO.GetParentIDs())==1)
        self.assertTrue(len(newO.GetParentTitles())==1)
        self.assertTrue(len(newO.GetParentPaths())==1)
        self.assertTrue(len(newO.GetObjsList())==2, len(newO.GetObjsList()))

        self.assertEqual(ccc+11, db_app.statdb(a))

        o1.Close()
        o2.Close()
        r.Delete(o1.GetID(), user=user)
        r.Delete(o2.GetID(), user=user)
        self.assertEqual(ccc+5, db_app.statdb(a))

        newO.Close()
        r.Delete(newO.GetID(), user=user)
        self.assertEqual(ccc, db_app.statdb(a))
        
    def test_createobjs_simple(self):
        #print "Testing new object creation, values and delete"
        a=self.app
        r=db_app.root(a)
        # create
        user = User("test")
        ccc = a.db.GetCountEntries()

        typedef = a.configurationQuery.GetObjectConf("type1")
        data = db_app.data1_1

        o1 = r.CreateWithoutEventsAndSecurity(typedef, data, user)
        self.assertTrue(o1)
        self.remove.append(o1.id)
        o1.Commit(user)
        self.assertTrue(r.obj(o1.id))

        o2 = r.CreateWithoutEventsAndSecurity(typedef, data, user)
        self.assertTrue(o2)
        self.remove.append(o2.id)
        o2.Commit(user)
        self.assertTrue(r.obj(o2.id))

        o3 = o2.CreateWithoutEventsAndSecurity(typedef, data, user)
        self.assertTrue(o3)
        self.assertTrue(o3.parent.id==o2.id)
        o3.Commit(user)
        self.assertTrue(o2.obj(o3.id))


    def test_lists(self):
        #print "Testing objects and subobjects"
        a=self.app
        r=db_app.root(a)
        ccc = a.db.GetCountEntries()
        user = User("test")
        # errors
        id = 9865898568444
        try:
            r.obj(id)
            self.assertTrue(False)
        except:
            pass
        try:
            r.GetObj(id)
            self.assertTrue(False)
        except:
            pass
        # objects and parents
        self.assertTrue(r.defaultSort)
        ccontainer = len(r.GetObjs(containerOnly=1, batch=False))
        cobjs = len(r.GetObjs(batch=False))
        ccontainer2 = len(r.GetObjsList(containerOnly=1, parameter={"pool_type":"type2"}))
        cobjs2 = len(r.GetObjsList(parameter={"pool_type":"type2"}))
        c=db_app.statdb(a)
        o1 = db_app.createObj1(r)
        self.assertTrue(o1)
        self.remove.append(o1.id)
        o2 = db_app.createObj2(r)
        self.assertTrue(o2)
        self.remove.append(o2.id)
        o3 = db_app.createObj1(o1)
        self.assertTrue(o3)
        o4 = db_app.createObj2(o3)
        self.assertTrue(o4)
        o5 = db_app.createObj2(o3)
        self.assertTrue(o5)
        self.assertEqual(c+5, db_app.statdb(a))
        try:
            db_app.createObj1(o5)
            self.assertTrue(False)
        except:
            pass
        try:
            db_app.createObj2(o5)
            self.assertTrue(False)
        except:
            pass

        # objects
        id = o1.GetID()
        self.assertTrue(r.obj(id))
        self.assertTrue(r.GetObj(id))
        self.assertTrue(o1.GetObj(o3.GetID()))
        self.assertTrue(o3.GetObj(o4.GetID()))
        id = o5.GetID()
        self.assertTrue(r.LookupObj(id))

        # subitems
        #root
        self.assertTrue(len(r.GetObjs(containerOnly=1, batch=False))==ccontainer+2)
        self.assertTrue(len(r.GetObjs(batch=False))==cobjs+2)
        self.assertTrue(len(r.GetObjs(containerOnly=1))==ccontainer+2)  # less failsafe than batch=False. On failure reset testdata.
        self.assertTrue(len(r.GetObjs())==cobjs+2)
        self.assertTrue(len(r.GetObjs(pool_type="type2")))
        self.assertTrue(len(r.GetObjsList(containerOnly=1, parameter={"pool_type":"type2"}))==ccontainer2+1)
        self.assertTrue(len(r.GetObjsList(parameter={"pool_type":"type2"}))==cobjs2+1)
        self.assertTrue(len(o3.GetObjsBatch([o4.id,o5.id])))
        # object
        self.assertTrue(len(o3.GetObjs(containerOnly=1))==2)
        self.assertTrue(len(o3.GetObjs())==2)
        self.assertTrue(len(o3.GetObjs(pool_type="type2"))==2)
        self.assertTrue(len(o3.GetObjsList(containerOnly=1, parameter={"pool_type":"type2"}))==2)
        self.assertTrue(len(o3.GetObjsList(parameter={"pool_type":"type2"}))==2)
        self.assertTrue(len(o3.GetObjsList(containerOnly=1, parameter={"pool_type":"type2"}, operators={"pool_type":"<>"}))==0)
        self.assertTrue(len(o3.GetObjsList(parameter={"pool_type":"type2"}, operators={"pool_type":"<>"}))==0)
        self.assertTrue(len(o1.GetSubtreeIDs())==3)
        
        r.DeleteInternal(o1.GetID(), user=user)
        r.DeleteInternal(o2.GetID(), user=user, obj=o2)
        self.assertEqual(ccc, a.db.GetCountEntries())
        


    def test_restraintsConf(self):
        #print "Testing new object creation, values and delete"
        a=self.app
        r=db_app.root(a)
        
        p,o=r.ObjQueryRestraints(self)
        p1,o1=r.queryRestraints
        self.assertTrue(p==p1)
        self.assertTrue(o==o1)
        
        r.queryRestraints = {"id":123}, {"id":"="}
        p,o=r.ObjQueryRestraints(self)
        self.assertTrue(p=={"id":123})
        self.assertTrue(o=={"id":"="})
        
        r.queryRestraints = {"id":123}, {"id":"="}
        p,o=r.ObjQueryRestraints(self, {"aa":123}, {"aa":"="})
        self.assertTrue(p=={"id":123,"aa":123})
        self.assertTrue(o=={"id":"=","aa":"="})
        
        def callback(**kw):
            kw["parameter"]["id"] = 456
            kw["operators"]["id"] = "LIKE"
        r.ListenEvent("loadRestraints", callback)
        p,o=r.ObjQueryRestraints(self)
        self.assertTrue(p=={"id":456})
        self.assertTrue(o=={"id":"LIKE"})


    def test_restraintsLookup(self):
        #print "Testing objects and subobjects"
        a=self.app
        r=db_app.root(a)
        ccc = a.db.GetCountEntries()
        user = User("test")
        # errors
        id = 9865898568444
        try:
            r.obj(id)
            self.assertTrue(False)
        except:
            pass
        try:
            r.GetObj(id)
            self.assertTrue(False)
        except:
            pass
        # objects and parents
        self.assertTrue(r.defaultSort)
        ccontainer = len(r.GetObjs(containerOnly=1, batch=False))
        cobjs = len(r.GetObjs(batch=False))
        ccontainer2 = len(r.GetObjsList(containerOnly=1, parameter={"pool_type":"type2"}))
        cobjs2 = len(r.GetObjsList(parameter={"pool_type":"type2"}))
        c=db_app.statdb(a)
        o1 = db_app.createObj1(r)
        self.assertTrue(o1)
        self.remove.append(o1.id)
        o2 = db_app.createObj2(r)
        self.assertTrue(o2)
        self.remove.append(o2.id)
        o3 = db_app.createObj1(o1)
        self.assertTrue(o3)
        o4 = db_app.createObj2(o3)
        self.assertTrue(o4)
        o5 = db_app.createObj2(o3)
        self.assertTrue(o5)
        self.assertTrue(c+5==db_app.statdb(a))
        try:
            db_app.createObj1(o5)
            self.assertTrue(False)
        except:
            pass
        try:
            db_app.createObj2(o5)
            self.assertTrue(False)
        except:
            pass

        r.queryRestraints = {"pool_state":99}, {"pool_state":">"}

        # objects
        id = o1.GetID()
        self.assertFalse(r.obj(id))
        self.assertFalse(r.GetObj(id))
        self.assertFalse(o1.GetObj(o3.GetID()))
        self.assertFalse(o3.GetObj(o4.GetID()))
        id = o5.GetID()
        self.assertFalse(r.obj(id))

        # subitems
        #root
        self.assertTrue(len(r.GetObjs(containerOnly=1, batch=False))==0)
        self.assertTrue(len(r.GetObjs(batch=False))==0)
        self.assertTrue(len(r.GetObjs(containerOnly=1))==0)
        self.assertTrue(len(r.GetObjs())==0)
        self.assertTrue(len(r.GetObjsList(containerOnly=1, parameter={"pool_type":"type2"}))==0)
        p,o=r.ObjQueryRestraints(r)
        p.update({"pool_type":"type2"})
        self.assertTrue(len(r.GetObjsList(parameter=p))==0)
        self.assertTrue(len(o3.GetObjsBatch([o4.id,o5.id]))==0)
        # object
        self.assertTrue(len(o3.GetObjs(containerOnly=1))==0)
        self.assertTrue(len(o3.GetObjs())==0)
        self.assertTrue(len(o3.GetObjsList(containerOnly=1, parameter={"pool_type":"type2"}))==0)
        p,o=r.ObjQueryRestraints(self)
        p.update({"pool_type":"type2"})
        self.assertTrue(len(o3.GetObjsList(parameter=p))==0)
        p,o=r.ObjQueryRestraints(self)
        self.assertTrue(len(o3.GetObjsList(containerOnly=1, parameter={"pool_type":"type2"}, operators={"pool_type":"<>"}))==0)
        p,o=r.ObjQueryRestraints(self)
        p.update({"pool_type":"type2"})
        o.update({"pool_type":"<>"})
        self.assertTrue(len(o3.GetObjsList(parameter=p, operators=o))==0)
        
        r.queryRestraints = {}, {}

        r.DeleteInternal(o1.GetID(), user=user)
        r.DeleteInternal(o2.GetID(), user=user, obj=o2)
        self.assertEqual(ccc, a.db.GetCountEntries())
        


    def test_shortcuts(self):
        #print "Testing shortcuts"
        a=self.app
        user = User("test")
        ccc = a.db.GetCountEntries()
        self.assertTrue(a.root)
        self.assertTrue(a.db)
        r = a.root
        #root
        r.app
        r.db
        r.root
        r.GetID()
        r.GetTypeID()
        r.GetTypeName()
        r.GetTitle()
        r.GetPath()
        r.IsRoot()
        r.GetParents()
        r.GetParentIDs()
        r.GetParentTitles()
        r.GetParentPaths()
        r.GetTool("nive.tools.example")
        r.Close()


    def test_shortcuts2(self):
        #print "Testing shortcuts"
        a=self.app
        user = User("test")
        ccc = a.db.GetCountEntries()
        self.assertTrue(a.root)
        self.assertTrue(a.db)
        r = a.root
        o1 = db_app.createObj1(r)
        self.assertTrue(o1)
        self.remove.append(o1.id)
        #root
        o1.app
        o1.db
        o1.root
        o1.GetID()
        o1.GetTypeID()
        o1.GetTypeName()
        o1.GetTitle()
        o1.GetPath()
        o1.IsRoot()
        o1.GetParents()
        o1.GetParentIDs()
        o1.GetParentTitles()
        o1.GetParentPaths()
        o1.GetTool("nive.tools.example")
        o1.Close()
        self.assertEqual(ccc+1, a.db.GetCountEntries())
        r.Delete(o1.id, user)






class containerTest_db_sqlite(containerTest_db, __local.SqliteTestCase):
    """
    see tests.__local
    """

class containerTest_db_mysql(containerTest_db, __local.MySqlTestCase):
    """
    see tests.__local
    """
    
class containerTest_db_pg(containerTest_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """
    


from pyramid import testing

class groupsrootTest_db:
    
    def setUp(self):
        self.request = testing.DummyRequest()
        self.request._LOCALE_ = "en"
        self.config = testing.setUp(request=self.request)
        self.request.content_type = ""
        self._loadApp(["nive.extensions.localgroups"])
        self.remove=[]

    def tearDown(self):
        db_app.emptypool(self.app)
        self.app.Close()

    def test_permissions(self):
        #print "Testing shortcuts"
        a=self.app
        user = User("test")
        ccc = a.db.GetCountEntries()
        self.assertTrue(a.root)
        self.assertTrue(a.db)
        r = a.root
        o1 = db_app.createObj1(r)
        self.assertTrue(o1)
        self.remove.append(o1.id)
        #root
        testsec = TestSecurityContext()
        self.assertTrue(a.root.GetObj(self.remove[-1], permission="view", securityContext=testsec))
        # todo: add authentication policy to tests
        #self.assertRaises(PermissionError, a.root.GetObj, self.remove[-1], permission="none", securityContext=testsec)
        #self.assert_(a.root.GetObj(self.remove[-1], permission="none", securityContext=testsec))
        r.Delete(o1.id, user)

    def test_rootsGroups(self):
        a=self.app
        r=db_app.root(a)

        userid = "test"
        r.RemoveLocalGroups(None, None)
        self.assertFalse(r.GetLocalGroups(userid))
        r.AddLocalGroup(userid, "group:local")
        self.assertEqual(r.GetLocalGroups(userid), ["group:local"])
        r.RemoveLocalGroups("nouser", "nogroup")
        self.assertEqual(r.GetLocalGroups(userid), ["group:local"])
        r.RemoveLocalGroups(userid, "nogroup")
        self.assertEqual(r.GetLocalGroups(userid), ["group:local"])
        r.RemoveLocalGroups("nouser", "group:local")
        self.assertEqual(r.GetLocalGroups(userid), ["group:local"])
        r.RemoveLocalGroups(userid, "group:local")
        self.assertFalse(r.GetLocalGroups(userid))
        r.AddLocalGroup(userid, "group:local")
        r.RemoveLocalGroups(userid, None)
        self.assertFalse(r.GetLocalGroups(userid))
        r.db.Undo()
        


class groupsrootTest_db_sqlite(groupsrootTest_db, __local.SqliteTestCase):
    """
    see tests.__local
    """

class groupsrootTest_db_mysql(groupsrootTest_db, __local.MySqlTestCase):
    """
    see tests.__local
    """

class groupsrootTest_db_pg(groupsrootTest_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """



