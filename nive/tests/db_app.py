#-*- coding: utf-8 -*-

import time
import unittest

from nive.utils.path import DvPath

from nive.definitions import *
from nive.portal import Portal
from nive.security import User, Allow, Everyone

from nive.application import Application
from nive.utils.dataPool2.files import File

root = RootConf(
    id = u"root",
    name = u"Data root",
    default = 1,
    context = "nive.container.Root",
    subtypes = [IObject],
    acl = ((Allow, Everyone, 'view'),)
)

type1 = ObjectConf(
    id = u"type1",
    name = u"Type 1 container",
    hidden = False,
    dbparam = u"data1",
    context = "nive.container.Container",
    subtypes = [IObject],
    acl = ((Allow, Everyone, 'view'),)
)
type1.data = [
    FieldConf(id="ftext", datatype="text", size=1000, name=u"ftext", fulltext=1),
    FieldConf(id="fnumber", datatype="number", size=8, name=u"fnumber", required=1),
    FieldConf(id="fdate", datatype="datetime", size=8, name=u"fdate"),
    FieldConf(id="ftime", datatype="time",     size=8, name=u"ftime"),
    FieldConf(id="flist", datatype="list",     size=100, name=u"flist", listItems=[{"id": u"item 1", "name":u"Item 1"},{"id": u"item 2", "name":u"Item 2"},{"id": u"item 3", "name":u"Item 3"}]),
    FieldConf(id="fmselect", datatype="multilist", size=50, name=u"fmselect"),
    FieldConf(id="funit", datatype="unit", size=8, name=u"funit"),
    FieldConf(id="funitlist", datatype="unitlist", size=100, name=u"funitlist"),
    FieldConf(id="fjson", datatype="json", size=1000, name=u"fjson"),
]

type2 = ObjectConf(
    id = u"type2",
    name = u"Type 2 Object",
    hidden = True,
    dbparam = u"data2",
    context = "nive.objects.Object",
    subtypes = None
)
data2 = []
data2.append(FieldConf(**{"id":u"fstr", "datatype": "string", "size": 100, "name": u"fstr", "fulltext": 1}))
data2.append(FieldConf(**{"id":u"ftext", "datatype": "text", "size": 1000, "name": u"ftext"}))
data2.append(FieldConf(**{"id":u"file1", "datatype": "file", "size": 5*1024*1024, "name": u"file1"}))
data2.append(FieldConf(**{"id":u"file2", "datatype": "file", "size": 500*1024, "name": u"file2"}))
type2.data = data2

def create_callback(context, **kw):
    context.__kws_test__ = kw
    pass

type3 = ObjectConf(
    id = u"type3",
    name = u"Type 3 Object",
    hidden = True,
    dbparam = u"data3",
    context = "nive.container.Container",
    subtypes = [INonContainer],
    events = (Conf(event="create", callback=create_callback),)
)
data3 = []
data3.append(FieldConf(**{"id":u"fstr", "datatype": "string", "size": 100, "name": u"fstr", "fulltext": 1}))
type3.data = data3

cat1 = Conf(**{u"id":u"cat1", u"name":u"Category 1"})
cat2 = Conf(**{u"id":u"cat2", u"name":u"Category 2"})

group1 = GroupConf(**{u"id":u"group1", u"name":u"Group 1"})
group2 = GroupConf(**{u"id":u"group2", u"name":u"Group 2"})

# configuration
appconf = AppConf(
    id = u"unittest",
    context="nive.application.Application",
    title = u"nive application python unittest",
    timezone = "UTC",
    modules = [root, type1, type2, type3],
    categories = [cat1, cat2],
    groups = [group1, group2],
    fulltextIndex = True,
    # run tests with the minimum required set of meta fields
    meta = copy.deepcopy(list(SystemFlds)) + copy.deepcopy(list(UserFlds))
)
appconf.meta.append(FieldConf(id="testfld", datatype="number", size=4, name=u"Number"))
appconf.meta.append(FieldConf(id="title", datatype="string", size=100, name=u"Title"))
appconf.meta.append(FieldConf(id="pool_sort", datatype="number", size=4, name=u"Number"))
appconf.meta.append(FieldConf(id="pool_wfa", datatype="string", size=20, name=u"Workflow"))
appconf.meta.append(FieldConf(id="pool_wfp", datatype="string", size=20, name=u"Workflow"))

# test data -----------------------------------------------------------------------
data1_1 = { u"ftext": u"this is text!",
            u"fnumber": 123456,
            u"fdate": "2008/06/23 16:55:00",
            u"ftime": "16:55:00",
            u"flist": ["item 1", "item 2", "item 3"],
            u"fmselect": "item 5",
            u"funit": 35,
            u"funitlist": [34, 35, 36],
            u"pool_filename":u"äüöß and others",
            u"pool_type": "type1"}
data2_1 = { u"fstr": u"this is sting!",
            u"ftext": u"this is text!",
            u"pool_filename": u"äüöß and others",
            u"pool_type": u"type2"}
data3_1 = { u"pool_filename": u"title data 3",
            u"fstr": u"testing type 3!"}

data1_2 = { u"ftext": u"this is a new text!",
            u"ftime": "23:08:13.000500",
            u"funit": 0,
            u"pool_filename":u"new title data 1"}
data2_2 = { u"fstr": u"this is new sting!",
            u"pool_filename": u"new title data 2"}

file2_1_data="This is the first text"
file2_2_data=u"This is the text in the second file"
file2_1 = {"filename":"file1.txt", "file":file2_1_data}
file2_2 = {"filename":"file2.txt", "file":file2_2_data}


# empty -------------------------------------------------------------------------
def app_db(modules=None):
    a = Application()
    a.Register(appconf)
    if modules:
        for m in modules:
            a.Register(m)
    p = Portal()
    p.Register(a, "nive")
    a.SetupApplication()
    dbfile = DvPath(a.dbConfiguration.dbName)
    if not dbfile.IsFile():
        dbfile.CreateDirectories()
    root = DvPath(a.dbConfiguration.fileRoot)
    if not root.IsDirectory():
        root.CreateDirectories()
    
    try:
        a.Query("select id from pool_meta where id=1")
        a.Query("select id from data1 where id=1")
        a.Query("select id from data2 where id=1")
        a.Query("select id from data3 where id=1")
        a.Query("select id from pool_files where id=1")
        a.Query("select id from pool_sys where id=1")
        a.Query("select id from pool_groups where id=1")
        a.Query("select title from pool_meta where id=1")
    except:
        a.GetTool("nive.tools.dbStructureUpdater")()

    # disable this to update test tables each time the tests are called
    #a.GetTool("nive.tools.dbStructureUpdater")()
    a.Startup(None)
    # this will reset all testdata
    #emptypool(a)
    return a

def app_nodb():
    a = Application()
    a.Register(appconf)
    a.Register(DatabaseConf())
    p = Portal()
    p.Register(a, "nive")
    a.SetupApplication()
    try:
        a.Startup(None)
    except OperationalError:
        pass
    return a

def emptypool(app):
    db = app.db
    db.Query(u"delete FROM pool_meta")
    db.Query(u"delete FROM pool_files")
    db.Query(u"delete FROM pool_fulltext")
    db.Query(u"delete FROM pool_groups")
    db.Query(u"delete FROM pool_sys")
    db.Query(u"delete FROM data2")
    db.Query(u"delete FROM data1")
    db.Commit()
    import shutil
    shutil.rmtree(str(db.root), ignore_errors=True)
    db.root.CreateDirectories()

def createpool(path,app):
    path.CreateDirectories()
    app.GetTool("nive.tools.dbStructureUpdater")()


def statdb(app):
    c = app.db.GetCountEntries()
    ##print "Count entries in DB:", c
    return c

def root(a):
    r = a.GetRoot("root")
    return r

def createObj1(c):
    type = u"type1"
    data = data1_1
    user = User(u"test")
    o = c.Create(type, data = data, user = user)
    #o.Commit()
    return o

def createObj2(c):
    type = u"type2"
    data = data2_1
    user = User(u"test")
    o = c.Create(type, data = data, user = user)
    #o.Commit()
    return o

def createObj3(c):
    type = u"type3"
    data = data3_1
    user = User(u"test")
    o = c.Create(type, data = data, user = user)
    #o.Commit()
    return o

def createObj1file(c):
    type = "type1"
    data = data1_1.copy()
    data["file1"] = File(**file2_1)
    data["file2"] = File(**file2_2)
    user = User(u"test")
    o = c.Create(type, data = data, user = user)
    #o.Commit()
    return o

def createObj2file(c):
    type = u"type2"
    data = data2_1.copy()
    data["file2"] = File(**file2_1)
    user = User(u"test")
    o = c.Create(type, data = data, user = user)
    #o.Commit()
    return o

def maxobj(r):
    id = r.GetMaxID()
    return r.LookupObj(id)
