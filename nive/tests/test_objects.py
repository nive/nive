#-*- coding: utf-8 -*-

import unittest
from nive.helper import *

from nive.tests.db_app import *
from nive.tests import __local


class objTest_db:
    
    def setUp(self):
        self._loadApp()

    def tearDown(self):
        self.app.Close()


    def test_obj1(self):
        a=self.app
        r=root(a)
        user = User(u"test")
        o = createObj1(r)
        id = o.id
        o.Close()
        o = r.obj(id)
        self.assertTrue(o)
        self.assertTrue(o.app)
        self.assertTrue(o.dataroot)
        self.assertTrue(o.db)
        self.assertTrue(o.IsRoot()==False)
        self.assertTrue(o.GetParents())
        self.assertTrue(o.GetParentIDs())
        self.assertTrue(o.GetParentTitles())
        self.assertTrue(o.GetParentPaths())
        r.Delete(id, user=user)


    def test_obj_timezone(self):
        a=self.app
        r=root(a)
        user = User(u"test")
        o = createObj1(r)
        id = o.id
        self.assertTrue(o.meta.pool_create)
        self.assertTrue(o.meta.pool_create.hour==datetime.utcnow().hour)
        o.Update(data1_2, user)
        self.assertTrue(o.meta.pool_change)
        self.assertTrue(o.meta.pool_change.hour==datetime.utcnow().hour)

        r.Delete(id, user=user)


    def test_objectacl(self):
        #print "Testing object update and commit"
        a=self.app
        ccc = a.db.GetCountEntries()
        # create
        user = User(u"test")

        r=root(a)
        self.assertTrue(r.__acl__[0][2]=='view')

        oo = createObj1(r)
        self.assertTrue(oo.__acl__[0][2]=='view')

        r.Delete(oo, user=user)


    def test_objectedit(self):
        #print "Testing object update and commit"
        a=self.app
        ccc = a.db.GetCountEntries()
        r=root(a)
        # create
        user = User(u"test")

        oo = createObj1(r)
        o1 = createObj1(oo)
        self.assertTrue(oo.GetTypeID()=="type1")
        self.assertTrue(oo.GetTypeName()==u"Type 1 container")
        self.assertTrue(oo.GetFieldConf("ftext").name=="ftext")
        self.assertTrue(oo.GetTitle()==u"")
        self.assertTrue(oo.GetPath()==str(oo.id))
        self.assertTrue(str(o1.GetFld(u"ftime"))==str(datetime_time(16,55)), str(o1.GetFld(u"ftime")))

        id = o1.GetID()
        o1.Update(data1_2, user)
        self.assertTrue(o1.GetID()==id)
        self.assertTrue(o1.GetFld(u"ftext")==data1_2[u"ftext"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data1_2[u"pool_filename"])
        self.assertTrue(str(o1.GetFld(u"ftime"))==str(datetime_time(23,8,13,500)), str(o1.GetFld(u"ftime")))
        del o1
        o1 = oo.obj(id)
        self.assertTrue(o1.GetFld(u"ftext")==data1_2[u"ftext"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data1_2[u"pool_filename"])
        oo.Delete(id, user=user)


        o1 = createObj1(oo)
        id = o1.GetID()
        data, meta, files = o1.SplitData(data1_2)
        o1.meta.update(meta)
        o1.data.update(data)
        o1.files.update(files)
        o1.Commit(user)
        self.assertTrue(o1.GetID()==id)
        self.assertTrue(o1.GetFld(u"ftext")==data1_2[u"ftext"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data1_2[u"pool_filename"])
        del o1
        o1 = oo.obj(id)
        self.assertTrue(o1.GetFld(u"ftext")!=data1_1[u"ftext"])
        self.assertTrue(o1.GetFld(u"pool_filename")!=data1_1[u"pool_filename"])
        
        o1.UpdateInternal(data1_1)
        o1.CommitInternal(user)
        self.assertTrue(o1.GetFld(u"ftext")==data1_1[u"ftext"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data1_1[u"pool_filename"])

        self.assertRaises(ContainmentError, r.Delete, id, user)
        r.Delete(oo.GetID(), user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        a.Close()


    def test_objectfiles(self):
        #print "Testing object files update and commit"
        a=self.app
        r=root(a)
        ccc = a.db.GetCountEntries()
        # create
        user = User(u"test")

        # testing StoreFile()
        o1 = createObj2(r)
        o2 = createObj2(r)
        o1.Update(data2_1, user)
        o2.Update(data2_2, user)
        o1.StoreFile(u"file1", File(**file2_1), user=user)
        o1.StoreFile(u"file2", File(**file2_2), user=user)
        o2.StoreFile(u"file2", File(**file2_2), user=user)
        self.assertTrue(o1.GetFld(u"ftext")==data2_1[u"ftext"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assertTrue(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assertTrue(o1.GetFile(u"file2").filename==file2_2["filename"])
        self.assertTrue(o2.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assertTrue(o2.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assertTrue(o2.GetFile(u"file2").filename==file2_2["filename"])

        id1 = o1.id
        id2 = o2.id
        del o1
        del o2
        o1 = r.obj(id1)
        o2 = r.obj(id2)
        self.assertTrue(o1.GetFld(u"ftext")==data2_1[u"ftext"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assertTrue(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assertTrue(o1.GetFile(u"file2").filename==file2_2["filename"])
        self.assertTrue(o2.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assertTrue(o2.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assertTrue(o2.GetFile(u"file2").filename==file2_2["filename"])
        self.assertTrue(o2.GetFileByName(file2_2["filename"]))

        #delete files
        self.assertTrue(o1.DeleteFile(u"file1", user=user))
        self.assertTrue(o1.DeleteFile(u"file2", user=user))
        self.assertFalse(o1.GetFile(u"file1"))
        self.assertFalse(o1.GetFile(u"file2"))
        self.assertFalse(o1.GetFileByName(file2_2["filename"]))

        r.Delete(o1.GetID(), user=user)
        r.Delete(o2.GetID(), user=user)

        # testing files wrapper
        o1 = createObj2(r)
        o2 = createObj2(r)
        d = data2_1.copy()
        d[u"file1"] = File(**file2_1)
        d[u"file2"] = File(**file2_2)
        o1.Update(d, user)
        d = data2_2.copy()
        d[u"file2"] = File(**file2_2)
        o2.Update(d, user)
        self.assertTrue(o1.GetFld(u"ftext")==data2_1[u"ftext"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assertTrue(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assertTrue(o1.GetFile(u"file2").filename==file2_2["filename"])
        self.assertTrue(o2.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assertTrue(o2.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assertTrue(o2.GetFile(u"file2").filename==file2_2["filename"])

        id1 = o1.id
        id2 = o2.id
        del o1
        del o2
        o1 = r.obj(id1)
        o2 = r.obj(id2)
        self.assertTrue(o1.GetFld(u"ftext")==data2_1[u"ftext"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assertTrue(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assertTrue(o1.GetFile(u"file2").filename==file2_2["filename"])
        self.assertTrue(o2.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assertTrue(o2.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assertTrue(o2.GetFile(u"file2").filename==file2_2["filename"])

        r.Delete(o1.GetID(), user=user)
        r.Delete(o2.GetID(), user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        a.Close()


    def test_commitundo(self):
        #print "Testing object commit and undo for data and files"
        a=self.app
        ccc = a.db.GetCountEntries()
        r=root(a)
        # create
        user = User(u"test")

        # testing commit
        o1 = createObj2(r)
        d = data2_2.copy()
        d[u"file1"] = File(**file2_1)
        d[u"file2"] = File(**file2_2)
        data, meta, files = o1.SplitData(d)
        o1.data.update(data)
        o1.meta.update(meta)
        o1.files.update(files)
        self.assertTrue(o1.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assertTrue(o1.files[u"file1"]["filename"]==file2_1["filename"])
        self.assertTrue(o1.files[u"file2"]["filename"]==file2_2["filename"])
        o1.Commit(user)
        self.assertTrue(o1.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assertTrue(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assertTrue(o1.GetFile(u"file2").filename==file2_2["filename"])
        id = o1.id
        del o1
        o1 = r.obj(id)
        self.assertTrue(o1.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assertTrue(o1.GetFile(u"file1").filename==file2_1["filename"])
        self.assertTrue(o1.GetFile(u"file2").filename==file2_2["filename"])
        r.Delete(o1.GetID(), user=user)

        # testing undo
        o1 = createObj2(r)
        o1.StoreFile(u"file1", File(**file2_1), user=user)
        d = data2_2.copy()
        d[u"file1"] = File(**file2_2)
        data, meta, files = o1.SplitData(d)
        o1.data.update(data)
        o1.meta.update(meta)
        o1.files.update(files)
        self.assertTrue(o1.GetFld(u"fstr")==data2_2[u"fstr"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data2_2[u"pool_filename"])
        self.assertTrue(o1.files.get(u"file1").filename==file2_2["filename"])
        o1.Undo()
        self.assertTrue(o1.GetFld(u"fstr")==data2_1[u"fstr"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assertTrue(o1.files.get(u"file1").filename==file2_1["filename"])
        id = o1.id
        del o1
        o1 = r.obj(id)
        self.assertTrue(o1.GetFld(u"fstr")==data2_1[u"fstr"])
        self.assertTrue(o1.GetFld(u"pool_filename")==data2_1[u"pool_filename"])
        self.assertTrue(o1.GetFile(u"file1").filename==file2_1["filename"])
        r.Delete(o1.GetID(), user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        a.Close()

    
class objTest_db_sqlite(objTest_db, __local.SqliteTestCase):
    """
    see tests.__local
    """

class objTest_db_mysql(objTest_db, __local.MySqlTestCase):
    """
    see tests.__local
    """
        
class objTest_db_pg(objTest_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """


class groupsTest_db:
    
    def setUp(self):
        self._loadApp(["nive.extensions.localgroups"])
        self.remove=[]

    def tearDown(self):
        u = User(u"test")
        root = self.app.root()
        for r in self.remove:
            root.Delete(r, u)
        self.app.Close()

    def test_objectgroups(self):
        a=self.app
        r=root(a)
        # create
        user = User(u"test")
        o = createObj1(r)
        id = o.id
        
        userid = u"test"
        self.assertEqual(o.GetLocalGroups(userid), [u"group:owner"])
        r.RemoveLocalGroups(userid, None)
        o.RemoveLocalGroups(userid, None)
        self.assertFalse(o.GetLocalGroups(userid))
        o.AddLocalGroup(userid, u"group:local")
        self.assertEqual(o.GetLocalGroups(userid), [u"group:local"])
        o.RemoveLocalGroups(u"nouser", u"nogroup")
        self.assertEqual(o.GetLocalGroups(userid), [u"group:local"])
        o.RemoveLocalGroups(userid, u"nogroup")
        self.assertEqual(o.GetLocalGroups(userid), [u"group:local"])
        o.RemoveLocalGroups(u"nouser", u"group:local")
        self.assertEqual(o.GetLocalGroups(userid), [u"group:local"])
        o.RemoveLocalGroups(userid, u"group:local")
        self.assertFalse(o.GetLocalGroups(userid))
        o.AddLocalGroup(userid, u"group:local")
        o.RemoveLocalGroups(userid, None)
        self.assertFalse(o.GetLocalGroups(userid))
        o.Commit(user=user)

        r.Delete(id, user=user)


class groupsTest_db_sqlite(groupsTest_db, __local.SqliteTestCase):
    """
    see tests.__local
    """

class groupsTest_db_mysql(groupsTest_db, __local.MySqlTestCase):
    """
    see tests.__local
    """
        
class groupsTest_db_pg(groupsTest_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """
        
 
    
#tests!

class objToolTest_db:
    """
    """
    def setUp(self):
        self._loadApp()

    def tearDown(self):
        self.app.Close()
        pass

    
    """
    def test_tools(self):
        GetTool(name)
        GetTools(user)
    """

class objToolTest_db_: #(objToolTest_db, unittest.TestCase):
    """
    """

class objWfTest_db:
    """
    """
    def setUp(self):
        self._loadApp()

    def tearDown(self):
        self.app.Close()
        pass

    
    """
    def test_wf(self):
        GetWorkflow()
        GetNewWfID()
        GetWfStateName(user)
        GetWfInfo(user)
        WfAction(action, transition = None, user = None)
        WfAllow(action, transition = None, user = None)
        SetWfp(processID, user, force=False)
        SetWfState(stateID, user)
        SetWfData(state, key, data, user)
        GetWfData(state = None, key = None)
        DeleteWfData(user, state = None, key = None)
        GetWfLog(lastEntryOnly=1)
        AddWfLog(action, transition, user, comment="")
    """


class objWfTest_db_:#(objWfTest_db, unittest.TestCase):
    """
    """


