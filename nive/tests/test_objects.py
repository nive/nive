#-*- coding: utf-8 -*-

import unittest

from datetime import datetime
from datetime import time as datetime_time

from nive import File
from nive.definitions import ContainmentError

from nive.tests import db_app
from nive.tests import __local


class objTest_db:
    
    def setUp(self):
        self._loadApp()

    def tearDown(self):
        self._closeApp(True, True)


    def test_obj1(self):
        a=self.app
        r=db_app.root(a)
        user = db_app.User("test")
        o = db_app.createObj1(r)
        id = o.id
        o.Close()
        o = r.obj(id)
        self.assertTrue(o)
        self.assertTrue(o.app)
        self.assertTrue(o.root)
        self.assertTrue(o.db)
        self.assertTrue(o.IsRoot()==False)
        self.assertTrue(o.GetParents())
        self.assertTrue(o.GetParentIDs())
        self.assertTrue(o.GetParentTitles())
        self.assertTrue(o.GetParentPaths())
        self.assertTrue(o.relpath)
        o.Close()
        r.Delete(id, user=user)


    def test_obj_timezone(self):
        return
        a=self.app
        r=db_app.root(a)
        user = db_app.User("test")
        o = db_app.createObj1(r)
        id = o.id
        self.assertTrue(o.meta.pool_create)
        self.assertTrue(o.meta.pool_create.hour==datetime.utcnow().hour)
        o.Update(db_app.data1_2, user)
        self.assertTrue(o.meta.pool_change)
        self.assertTrue(o.meta.pool_change.hour==datetime.utcnow().hour)
        o.Close()

        r.Delete(id, user=user)


    def test_objectacl(self):
        #print "Testing object update and commit"
        a=self.app
        ccc = a.db.GetCountEntries()
        # create
        user = db_app.User("test")

        r=db_app.root(a)
        self.assertTrue(r.__acl__[0][2]=='view')

        oo = db_app.createObj1(r)
        self.assertTrue(oo.__acl__[0][2]=='view')

        r.Delete(oo, user=user)


    def test_objectedit(self):
        #print "Testing object update and commit"
        a=self.app
        ccc = a.db.GetCountEntries()
        r=db_app.root(a)
        # create
        user = db_app.User("test")

        oo = db_app.createObj1(r)
        o1 = db_app.createObj1(oo)
        self.assertTrue(oo.GetTypeID()=="type1")
        self.assertTrue(oo.GetTypeName()=="Type 1 container")
        self.assertTrue(oo.GetFieldConf("ftext").name=="ftext")
        self.assertTrue(oo.GetTitle()=="")
        self.assertTrue(oo.GetPath()==str(oo.id))
        self.assertTrue(str(o1.GetFld("ftime"))==str(datetime_time(16,55)), str(o1.GetFld("ftime")))

        id = o1.GetID()
        o1.Update(db_app.data1_2, user)
        self.assertTrue(o1.GetID()==id)
        self.assertTrue(o1.GetFld("ftext")==db_app.data1_2["ftext"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data1_2["pool_filename"])
        self.assertTrue(str(o1.GetFld("ftime"))==str(datetime_time(23,8,13,500)), str(o1.GetFld("ftime")))
        o1.Close()
        del o1

        o1 = oo.obj(id)
        self.assertTrue(o1.GetFld("ftext")==db_app.data1_2["ftext"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data1_2["pool_filename"])
        o1.Close()
        oo.Delete(id, user=user)

        o1 = db_app.createObj1(oo)
        id = o1.GetID()
        data, meta, files = o1.SplitData(db_app.data1_2)
        o1.meta.update(meta)
        o1.data.update(data)
        o1.files.update(files)
        o1.Commit(user)
        self.assertTrue(o1.GetID()==id)
        self.assertTrue(o1.GetFld("ftext")==db_app.data1_2["ftext"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data1_2["pool_filename"])
        del o1
        o1 = oo.obj(id)
        self.assertTrue(o1.GetFld("ftext")!=db_app.data1_1["ftext"])
        self.assertTrue(o1.GetFld("pool_filename")!=db_app.data1_1["pool_filename"])
        
        o1.UpdateInternal(db_app.data1_1)
        o1.CommitInternal(user)
        self.assertTrue(o1.GetFld("ftext")==db_app.data1_1["ftext"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data1_1["pool_filename"])

        self.assertRaises(ContainmentError, r.Delete, id, user)
        r.Delete(oo.GetID(), user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        a.Close()


    def test_objectfiles(self):
        #print "Testing object files update and commit"
        a=self.app
        r=db_app.root(a)
        ccc = a.db.GetCountEntries()
        # create
        user = db_app.User("test")

        # testing StoreFile()
        o1 = db_app.createObj2(r)
        o2 = db_app.createObj2(r)
        o1.Update(db_app.data2_1, user)
        o2.Update(db_app.data2_2, user)
        o1.StoreFile("file1", File(**db_app.file2_1), user=user)
        o1.StoreFile("file2", File(**db_app.file2_2), user=user)
        o2.StoreFile("file2", File(**db_app.file2_2), user=user)
        self.assertTrue(o1.GetFld("ftext")==db_app.data2_1["ftext"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data2_1["pool_filename"], o1.GetFld("pool_filename"))
        self.assertTrue(o1.GetFile("file1").filename==db_app.file2_1["filename"])
        self.assertTrue(o1.GetFile("file2").filename==db_app.file2_2["filename"])
        self.assertTrue(o2.GetFld("fstr")==db_app.data2_2["fstr"])
        self.assertTrue(o2.GetFld("pool_filename")==db_app.data2_2["pool_filename"])
        self.assertTrue(o2.GetFile("file2").filename==db_app.file2_2["filename"])

        id1 = o1.id
        id2 = o2.id
        del o1
        del o2
        o1 = r.obj(id1)
        o2 = r.obj(id2)
        self.assertTrue(o1.GetFld("ftext")==db_app.data2_1["ftext"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data2_1["pool_filename"])
        self.assertTrue(o1.GetFile("file1").filename==db_app.file2_1["filename"])
        self.assertTrue(o1.GetFile("file2").filename==db_app.file2_2["filename"])
        self.assertTrue(o2.GetFld("fstr")==db_app.data2_2["fstr"])
        self.assertTrue(o2.GetFld("pool_filename")==db_app.data2_2["pool_filename"])
        self.assertTrue(o2.GetFile("file2").filename==db_app.file2_2["filename"])
        self.assertTrue(o2.GetFileByName(db_app.file2_2["filename"]))

        #delete files
        self.assertTrue(o1.DeleteFile("file1", user=user))
        self.assertTrue(o1.DeleteFile("file2", user=user))
        self.assertFalse(o1.GetFile("file1"))
        self.assertFalse(o1.GetFile("file2"))
        self.assertFalse(o1.GetFileByName(db_app.file2_2["filename"]))

        r.Delete(o1.GetID(), user=user)
        r.Delete(o2.GetID(), user=user)

        # testing files wrapper
        o1 = db_app.createObj2(r)
        o2 = db_app.createObj2(r)
        d = db_app.data2_1.copy()
        d["file1"] = File(**db_app.file2_1)
        d["file2"] = File(**db_app.file2_2)
        o1.Update(d, user)
        d = db_app.data2_2.copy()
        d["file2"] = File(**db_app.file2_2)
        o2.Update(d, user)
        self.assertTrue(o1.GetFld("ftext")==db_app.data2_1["ftext"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data2_1["pool_filename"])
        self.assertTrue(o1.GetFile("file1").filename==db_app.file2_1["filename"])
        self.assertTrue(o1.GetFile("file2").filename==db_app.file2_2["filename"])
        self.assertTrue(o2.GetFld("fstr")==db_app.data2_2["fstr"])
        self.assertTrue(o2.GetFld("pool_filename")==db_app.data2_2["pool_filename"])
        self.assertTrue(o2.GetFile("file2").filename==db_app.file2_2["filename"])

        id1 = o1.id
        id2 = o2.id
        del o1
        del o2
        o1 = r.obj(id1)
        o2 = r.obj(id2)
        self.assertTrue(o1.GetFld("ftext")==db_app.data2_1["ftext"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data2_1["pool_filename"])
        self.assertTrue(o1.GetFile("file1").filename==db_app.file2_1["filename"])
        self.assertTrue(o1.GetFile("file2").filename==db_app.file2_2["filename"])
        self.assertTrue(o2.GetFld("fstr")==db_app.data2_2["fstr"])
        self.assertTrue(o2.GetFld("pool_filename")==db_app.data2_2["pool_filename"])
        self.assertTrue(o2.GetFile("file2").filename==db_app.file2_2["filename"])

        r.Delete(id1, user=user)
        r.Delete(id2, user=user)
        self.assertEqual(ccc, a.db.GetCountEntries())
        a.Close()


    def test_commitundo(self):
        #print "Testing object commit and undo for data and files"
        a=self.app
        ccc = a.db.GetCountEntries()
        r=db_app.root(a)
        # create
        user = db_app.User("test")

        # testing commit
        o1 = db_app.createObj2(r)
        d = db_app.data2_2.copy()
        d["file1"] = File(**db_app.file2_1)
        d["file2"] = File(**db_app.file2_2)
        data, meta, files = o1.SplitData(d)
        o1.data.update(data)
        o1.meta.update(meta)
        o1.files.update(files)
        self.assertTrue(o1.GetFld("fstr")==db_app.data2_2["fstr"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data2_2["pool_filename"])
        self.assertTrue(o1.files["file1"]["filename"]==db_app.file2_1["filename"])
        self.assertTrue(o1.files["file2"]["filename"]==db_app.file2_2["filename"])
        o1.Commit(user)
        self.assertTrue(o1.GetFld("fstr")==db_app.data2_2["fstr"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data2_2["pool_filename"])
        self.assertTrue(o1.GetFile("file1").filename==db_app.file2_1["filename"])
        self.assertTrue(o1.GetFile("file2").filename==db_app.file2_2["filename"])
        id = o1.id
        del o1
        o1 = r.obj(id)
        self.assertTrue(o1.GetFld("fstr")==db_app.data2_2["fstr"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data2_2["pool_filename"])
        self.assertTrue(o1.GetFile("file1").filename==db_app.file2_1["filename"])
        self.assertTrue(o1.GetFile("file2").filename==db_app.file2_2["filename"])
        o1.Close()
        r.Delete(o1.GetID(), user=user)

        # testing undo
        o1 = db_app.createObj2(r)
        o1.StoreFile("file1", File(**db_app.file2_1), user=user)
        d = db_app.data2_2.copy()
        d["file1"] = File(**db_app.file2_2)
        data, meta, files = o1.SplitData(d)
        o1.data.update(data)
        o1.meta.update(meta)
        o1.files.update(files)
        self.assertTrue(o1.GetFld("fstr")==db_app.data2_2["fstr"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data2_2["pool_filename"])
        self.assertTrue(o1.files.get("file1").filename==db_app.file2_2["filename"])
        o1.Undo()
        self.assertTrue(o1.GetFld("fstr")==db_app.data2_1["fstr"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data2_1["pool_filename"])
        self.assertTrue(o1.files.get("file1").filename==db_app.file2_1["filename"])
        id = o1.id
        del o1
        o1 = r.obj(id)
        self.assertTrue(o1.GetFld("fstr")==db_app.data2_1["fstr"])
        self.assertTrue(o1.GetFld("pool_filename")==db_app.data2_1["pool_filename"])
        self.assertTrue(o1.GetFile("file1").filename==db_app.file2_1["filename"])
        o1.Close()
        r.Delete(id, user=user)
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

    def tearDown(self):
        self._closeApp(True)


    def test_objectgroups(self):
        a=self.app
        r=db_app.root(a)
        # create
        user = db_app.User("test")
        o = db_app.createObj1(r)
        id = o.id
        
        userid = "test"
        #self.assertEqual(o.GetLocalGroups(userid), ["group:owner"]) # TODO MySQL failure pycharm?

        r.RemoveLocalGroups(userid, None)
        o.RemoveLocalGroups(userid, None)
        #r.db.Commit()
        self.assertFalse(o.GetLocalGroups(userid))
        o.AddLocalGroup(userid, "group:local")
        self.assertEqual(o.GetLocalGroups(userid), ["group:local"])
        o.RemoveLocalGroups("nouser", "nogroup")
        self.assertEqual(o.GetLocalGroups(userid), ["group:local"])
        o.RemoveLocalGroups(userid, "nogroup")
        self.assertEqual(o.GetLocalGroups(userid), ["group:local"])
        o.RemoveLocalGroups("nouser", "group:local")
        self.assertEqual(o.GetLocalGroups(userid), ["group:local"])
        o.RemoveLocalGroups(userid, "group:local")
        self.assertFalse(o.GetLocalGroups(userid))
        o.AddLocalGroup(userid, "group:local")
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
        
 
    
#TODO tests obj tool + workflow

class objToolTest_db:

    """
    def test_tools(self):
        GetTool(name)
    """


class objWfTest_db:

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


