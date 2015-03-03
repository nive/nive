from nive.tests.db_app import *

from nive.tests import __local


class TestSecurityContext(object):
    ppp="view"
    def has_permission(self,p,c):
        return p==self.ppp

class containerTest_db:
    
    def setUp(self):
        self._loadApp()
        self.remove=[]

    def tearDown(self):
        u = User(u"test")
        root = self.app.root()
        for r in self.remove:
            root.Delete(r, u)
        self.app.Close()


    def test_basics(self):
        #print "Testing shortcuts"
        a=self.app
        user = User(u"test")
        ccc = a.db.GetCountEntries()
        self.assert_(a.root())
        self.assert_(a.db)
        r = a.root()
        o1 = createObj1(r)
        o2 = createObj2(o1)
        id1 = o1.id
        id2 = o2.id
        self.remove.append(id1)
        self.assert_(a.obj(id1))
        self.assert_(r.__getitem__(str(id1)))
        self.assert_(r.obj(id1))
        self.assert_(o1.obj(id2))
        self.assert_(o1.db==a.db)
        self.assert_(r.db==a.db)
        
        self.assert_(r.IsTypeAllowed("type1", user=user))
        self.assert_(o1.IsTypeAllowed("type1", user=user))
        
        try:
            o2.IsTypeAllowed("type1", user=user)
            self.assert_(False, "ObjectBase is not a container: IsTypeAllowed")
        except AttributeError:
            pass
        self.assert_(r.GetAllowedTypes(user=user))
        self.assert_(o1.GetAllowedTypes(user=user))
        r.Delete(id1, user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        

    def test_createroots(self):
        #print "Testing root basics"
        a=self.app
        ccc = a.db.GetCountEntries()
        r=root(a)
        user = User(u"test")
        #rootValues()
        self.assert_(r.GetID()<=0)
        self.assert_(r.GetTypeID())
        self.assert_(r.GetTitle())
        self.assert_(r.GetPath())
        #rootParents()
        self.assert_(len(r.GetParents())==0)
        self.assert_(len(r.GetParentTitles())==0)
        self.assert_(len(r.GetParentPaths())==0)
        self.assertEqual(ccc, a.db.GetCountEntries())
        

    def test_createobjs_kws(self):
        #print "Testing new object creation, values and delete"
        a=self.app
        r=root(a)
        # create
        user = User(u"test")
        type = u"type3"
        data = {}
        user = User(u"test")
        o = r.Create(type, data=data, user=user, custom=123)
        self.assert_(o.__kws_test__.get("custom")==123)


    def test_createobjs(self):
        #print "Testing new object creation, values and delete"
        a=self.app
        r=root(a)
        # create
        user = User(u"test")
        ccc = a.db.GetCountEntries()
        o1 = createObj1(r)
        self.assert_(o1)
        self.remove.append(o1.id)
        o2 = createObj2(r)
        self.assert_(o2)
        self.remove.append(o2.id)
        o3 = createObj1(o1)
        self.assert_(o3)
        o4 = createObj1(o3)
        self.assert_(o4)
        
        o5 = createObj3(o1)
        self.assert_(o5)
        o6 = createObj2(o5)
        self.assert_(o6)
        self.assertRaises(ContainmentError, createObj1, o5)
        
        self.assert_(ccc+6==statdb(a))
        #Values()
        self.assert_(r.IsContainer())
        self.assert_(o1.IsContainer())
        self.assert_(o2.IsContainer()==False)
        self.assert_(o1.GetID())
        self.assert_(o1.GetTypeID()=="type1")
        self.assert_(o1.GetTitle()=="")
        self.assert_(o1.GetPath())
        #Parents()
        self.assert_(len(o1.GetParents())==1)
        self.assert_(len(o1.GetParentIDs())==1)
        self.assert_(len(o1.GetParentTitles())==1)
        self.assert_(len(o1.GetParentPaths())==1)

        self.assert_(o4.parent==o3)
        self.assert_(len(o4.GetParents())==3)
        self.assert_(len(o4.GetParentIDs())==3)
        self.assert_(len(o4.GetParentTitles())==3)
        self.assert_(len(o4.GetParentPaths())==3)
        self.assert_(o3.GetObj(o4.GetID()))
        
        newO = r.Duplicate(o1, user)
        self.assert_(newO)
        self.remove.append(newO.id)
        
        r.Delete(o1.GetID(), user=user)
        r.Delete(o2.GetID(), user=user)
        self.assertEqual(ccc+5, a.db.GetCountEntries())
        r.Delete(newO.GetID(), user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        
    def test_createobjs_simple(self):
        #print "Testing new object creation, values and delete"
        a=self.app
        r=root(a)
        # create
        user = User(u"test")
        ccc = a.db.GetCountEntries()

        typedef = a.GetObjectConf("type1")
        data = data1_1

        o1 = r.CreateWithoutEventsAndSecurity(typedef, data, user)
        self.assert_(o1)
        self.remove.append(o1.id)
        o1.Commit(user)
        self.assert_(r.obj(o1.id))

        o2 = r.CreateWithoutEventsAndSecurity(typedef, data, user)
        self.assert_(o2)
        self.remove.append(o2.id)
        o2.Commit(user)
        self.assert_(r.obj(o2.id))

        o3 = o2.CreateWithoutEventsAndSecurity(typedef, data, user)
        self.assert_(o3)
        self.assert_(o3.parent.id==o2.id)
        o3.Commit(user)
        self.assert_(o2.obj(o3.id))


    def test_lists(self):
        #print "Testing objects and subobjects"
        a=self.app
        r=root(a)
        ccc = a.db.GetCountEntries()
        user = User(u"test")
        # errors
        id = 9865898568444
        try:
            r.LookupObj(id)
            self.assert_(False)
        except:
            pass
        try:
            r.GetObj(id)
            self.assert_(False)
        except:
            pass
        # objects and parents
        self.assert_(r.GetSort())
        ccontainer = len(r.GetContainers(batch=False))
        cobjs = len(r.GetObjs(batch=False))
        ccontainer2 = len(r.GetContainerList(parameter={u"pool_type":u"type2"}))
        cobjs2 = len(r.GetObjsList(parameter={u"pool_type":u"type2"}))
        c=statdb(a)
        o1 = createObj1(r)
        self.assert_(o1)
        self.remove.append(o1.id)
        o2 = createObj2(r)
        self.assert_(o2)
        self.remove.append(o2.id)
        o3 = createObj1(o1)
        self.assert_(o3)
        o4 = createObj2(o3)
        self.assert_(o4)
        o5 = createObj2(o3)
        self.assert_(o5)
        self.assert_(c+5==statdb(a))
        try:
            createObj1(o5)
            self.assert_(False)
        except:
            pass
        try:
            createObj2(o5)
            self.assert_(False)
        except:
            pass

        # objects
        id = o1.GetID()
        self.assert_(r.LookupObj(id))
        self.assert_(r.GetObj(id))
        self.assert_(o1.GetObj(o3.GetID()))
        self.assert_(o3.GetObj(o4.GetID()))
        id = o5.GetID()
        self.assert_(r.LookupObj(id))

        # subitems
        #root
        self.assert_(len(r.GetContainers(batch=False))==ccontainer+2)
        self.assert_(len(r.GetObjs(batch=False))==cobjs+2)
        self.assert_(len(r.GetContainers())==ccontainer+2)  # less failsafe than batch=False. On failure reset testdata.
        self.assert_(len(r.GetObjs())==cobjs+2)
        self.assert_(len(r.GetObjs(pool_type="type2")))
        self.assert_(len(r.GetContainerList(parameter={u"pool_type":u"type2"}))==ccontainer2+1)
        self.assert_(len(r.GetObjsList(parameter={u"pool_type":u"type2"}))==cobjs2+1)
        self.assert_(len(o3.GetObjsBatch([o4.id,o5.id])))
        # object
        self.assert_(len(o3.GetContainers())==2)
        self.assert_(len(o3.GetObjs())==2)
        self.assert_(len(o3.GetObjs(pool_type="type2"))==2)
        self.assert_(len(o3.GetContainerList(parameter={u"pool_type":u"type2"}))==2)
        self.assert_(len(o3.GetObjsList(parameter={u"pool_type":u"type2"}))==2)
        self.assert_(len(o3.GetContainerList(parameter={u"pool_type":u"type2"}, operators={"pool_type":u"<>"}))==0)
        self.assert_(len(o3.GetObjsList(parameter={u"pool_type":u"type2"}, operators={u"pool_type":u"<>"}))==0)
        self.assert_(len(o1.GetContainedIDs())==3)
        
        r.DeleteInternal(o1.GetID(), user=user)
        r.DeleteInternal(o2.GetID(), user=user, obj=o2)
        self.assertEqual(ccc, a.db.GetCountEntries())
        


    def test_restraintsConf(self):
        #print "Testing new object creation, values and delete"
        a=self.app
        r=root(a)
        
        p,o=r.ObjQueryRestraints(self)
        p1,o1=r.queryRestraints
        self.assert_(p==p1)
        self.assert_(o==o1)
        
        r.queryRestraints = {"id":123}, {"id":"="}
        p,o=r.ObjQueryRestraints(self)
        self.assert_(p=={"id":123})
        self.assert_(o=={"id":"="})
        
        r.queryRestraints = {"id":123}, {"id":"="}
        p,o=r.ObjQueryRestraints(self, {"aa":123}, {"aa":"="})
        self.assert_(p=={"id":123,"aa":123})
        self.assert_(o=={"id":"=","aa":"="})
        
        def callback(**kw):
            kw["parameter"]["id"] = 456
            kw["operators"]["id"] = "LIKE"
        r.ListenEvent("loadRestraints", callback)
        p,o=r.ObjQueryRestraints(self)
        self.assert_(p=={"id":456})
        self.assert_(o=={"id":"LIKE"})


    def test_restraintsLookup(self):
        #print "Testing objects and subobjects"
        a=self.app
        r=root(a)
        ccc = a.db.GetCountEntries()
        user = User(u"test")
        # errors
        id = 9865898568444
        try:
            r.LookupObj(id)
            self.assert_(False)
        except:
            pass
        try:
            r.GetObj(id)
            self.assert_(False)
        except:
            pass
        # objects and parents
        self.assert_(r.GetSort())
        ccontainer = len(r.GetContainers(batch=False))
        cobjs = len(r.GetObjs(batch=False))
        ccontainer2 = len(r.GetContainerList(parameter={u"pool_type":u"type2"}))
        cobjs2 = len(r.GetObjsList(parameter={u"pool_type":u"type2"}))
        c=statdb(a)
        o1 = createObj1(r)
        self.assert_(o1)
        self.remove.append(o1.id)
        o2 = createObj2(r)
        self.assert_(o2)
        self.remove.append(o2.id)
        o3 = createObj1(o1)
        self.assert_(o3)
        o4 = createObj2(o3)
        self.assert_(o4)
        o5 = createObj2(o3)
        self.assert_(o5)
        self.assert_(c+5==statdb(a))
        try:
            createObj1(o5)
            self.assert_(False)
        except:
            pass
        try:
            createObj2(o5)
            self.assert_(False)
        except:
            pass

        r.queryRestraints = {"pool_state":99}, {"pool_state":">"}

        # objects
        id = o1.GetID()
        self.assertFalse(r.LookupObj(id))
        self.assertFalse(r.GetObj(id))
        self.assertFalse(o1.GetObj(o3.GetID()))
        self.assertFalse(o3.GetObj(o4.GetID()))
        id = o5.GetID()
        self.assertFalse(r.LookupObj(id))

        # subitems
        #root
        self.assert_(len(r.GetContainers(batch=False))==0)
        self.assert_(len(r.GetObjs(batch=False))==0)
        self.assert_(len(r.GetContainers())==0)
        self.assert_(len(r.GetObjs())==0)
        self.assert_(len(r.GetContainerList(parameter={u"pool_type":u"type2"}))==0)
        p,o=r.ObjQueryRestraints(r)
        p.update({u"pool_type":u"type2"})
        self.assert_(len(r.GetObjsList(parameter=p))==0)
        self.assert_(len(o3.GetObjsBatch([o4.id,o5.id]))==0)
        # object
        self.assert_(len(o3.GetContainers())==0)
        self.assert_(len(o3.GetObjs())==0)
        self.assert_(len(o3.GetContainerList(parameter={u"pool_type":u"type2"}))==0)
        p,o=r.ObjQueryRestraints(self)
        p.update({u"pool_type":u"type2"})
        self.assert_(len(o3.GetObjsList(parameter=p))==0)
        p,o=r.ObjQueryRestraints(self)
        self.assert_(len(o3.GetContainerList(parameter={u"pool_type":u"type2"}, operators={u"pool_type":u"<>"}))==0)
        p,o=r.ObjQueryRestraints(self)
        p.update({u"pool_type":u"type2"})
        o.update({u"pool_type":u"<>"})
        self.assert_(len(o3.GetObjsList(parameter=p, operators=o))==0)
        
        r.queryRestraints = {}, {}

        r.DeleteInternal(o1.GetID(), user=user)
        r.DeleteInternal(o2.GetID(), user=user, obj=o2)
        self.assertEqual(ccc, a.db.GetCountEntries())
        


    def test_shortcuts(self):
        #print "Testing shortcuts"
        a=self.app
        user = User(u"test")
        ccc = a.db.GetCountEntries()
        self.assert_(a.root())
        self.assert_(a.db)
        r = a.root()
        #root
        r.Close()
        r.app
        r.db
        r.dataroot
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


    def test_shortcuts2(self):
        #print "Testing shortcuts"
        a=self.app
        user = User(u"test")
        ccc = a.db.GetCountEntries()
        self.assert_(a.root())
        self.assert_(a.db)
        r = a.root()
        o1 = createObj1(r)
        self.assert_(o1)
        self.remove.append(o1.id)
        #root
        o1.app
        o1.db
        o1.dataroot
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
        u = User(u"test")
        root = self.app.root()
        for r in self.remove:
            root.Delete(r, u)
        self.app.Close()

    def test_permissions(self):
        #print "Testing shortcuts"
        a=self.app
        user = User(u"test")
        ccc = a.db.GetCountEntries()
        self.assert_(a.root())
        self.assert_(a.db)
        r = a.root()
        o1 = createObj1(r)
        self.assert_(o1)
        self.remove.append(o1.id)
        #root
        testsec = TestSecurityContext()
        self.assert_(a.root().GetObj(self.remove[-1], permission="view", securityContext=testsec))
        # todo: add authentication policy to tests
        #self.assertRaises(PermissionError, a.root().GetObj, self.remove[-1], permission="none", securityContext=testsec)
        #self.assert_(a.root().GetObj(self.remove[-1], permission="none", securityContext=testsec))
        r.Delete(o1.id, user)

    def test_rootsGroups(self):
        a=self.app
        r=root(a)

        userid = u"test"
        r.RemoveLocalGroups(None, None)
        self.assertFalse(r.GetLocalGroups(userid))
        r.AddLocalGroup(userid, u"group:local")
        self.assertItemsEqual(r.GetLocalGroups(userid), [u"group:local"])
        r.RemoveLocalGroups(u"nouser", u"nogroup")
        self.assertItemsEqual(r.GetLocalGroups(userid), [u"group:local"])
        r.RemoveLocalGroups(userid, u"nogroup")
        self.assertItemsEqual(r.GetLocalGroups(userid), [u"group:local"])
        r.RemoveLocalGroups(u"nouser", u"group:local")
        self.assertItemsEqual(r.GetLocalGroups(userid), [u"group:local"])
        r.RemoveLocalGroups(userid, u"group:local")
        self.assertFalse(r.GetLocalGroups(userid))
        r.AddLocalGroup(userid, u"group:local")
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



