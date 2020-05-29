#-*- coding: utf-8 -*-

from nive.utils.path import DvPath
from nive.definitions import *
from nive.portal import Portal
from nive.security import User, Allow, Everyone

from nive.application import Application
from nive.utils.dataPool2.files import File

root = RootConf(
    id = "root",
    name = "Data root",
    default = 1,
    context = "nive.container.Root",
    subtypes = [IObject],
    acl = ((Allow, Everyone, 'view'),)
)

type1 = ObjectConf(
    id = "type1",
    name = "Type 1 container",
    hidden = False,
    dbparam = "data1",
    context = "nive.container.Container",
    subtypes = [IObject],
    acl = ((Allow, Everyone, 'view'),)
)
type1.data = [
    FieldConf(id="ftext", datatype="text", size=1000, name="ftext", fulltext=1),
    FieldConf(id="fnumber", datatype="number", size=8, name="fnumber", required=1),
    FieldConf(id="fdate", datatype="datetime", size=8, name="fdate"),
    FieldConf(id="ftime", datatype="time",     size=8, name="ftime"),
    FieldConf(id="flist", datatype="list",     size=100, name="flist", listItems=[{"id": "item 1", "name":"Item 1"},{"id": "item 2", "name":"Item 2"},{"id": "item 3", "name":"Item 3"}]),
    FieldConf(id="fmselect", datatype="multilist", size=50, name="fmselect"),
    FieldConf(id="funit", datatype="unit", size=8, name="funit"),
    FieldConf(id="funitlist", datatype="unitlist", size=100, name="funitlist"),
    FieldConf(id="fjson", datatype="json", size=1000, name="fjson"),
]

type2 = ObjectConf(
    id = "type2",
    name = "Type 2 Object",
    hidden = False,
    dbparam = "data2",
    context = "nive.objects.Object",
    subtypes = None
)
data2 = []
data2.append(FieldConf(**{"id":"fstr", "datatype": "string", "size": 100, "name": "fstr", "fulltext": 1}))
data2.append(FieldConf(**{"id":"ftext", "datatype": "text", "size": 1000, "name": "ftext"}))
data2.append(FieldConf(**{"id":"file1", "datatype": "file", "size": 5*1024*1024, "name": "file1"}))
data2.append(FieldConf(**{"id":"file2", "datatype": "file", "size": 500*1024, "name": "file2"}))
type2.data = data2

def create_callback(context, **kw):
    context.__kws_test__ = kw
    pass

type3 = ObjectConf(
    id = "type3",
    name = "Type 3 Object",
    hidden = True,
    dbparam = "data3",
    context = "nive.container.Container",
    subtypes = [INonContainer],
    events = (Conf(event="create", callback=create_callback),)
)
data3 = []
data3.append(FieldConf(**{"id":"fstr", "datatype": "string", "size": 100, "name": "fstr", "fulltext": 1}))
type3.data = data3

cat1 = Conf(**{"id":"cat1", "name":"Category 1"})
cat2 = Conf(**{"id":"cat2", "name":"Category 2"})

group1 = GroupConf(**{"id":"group1", "name":"Group 1"})
group2 = GroupConf(**{"id":"group2", "name":"Group 2"})

# configuration
appconf = AppConf(
    id = "unittest",
    context="nive.application.Application",
    title = "nive application python unittest",
    timezone = "UTC",
    modules = [root, type1, type2, type3],
    categories = [cat1, cat2],
    groups = [group1, group2],
    fulltextIndex = True,
    # run tests with the minimum required set of meta fields
    meta = copy.deepcopy(list(SystemFlds)) + copy.deepcopy(list(UserFlds))
)
appconf.meta.append(FieldConf(id="testfld", datatype="number", size=4, name="Number"))
appconf.meta.append(FieldConf(id="title", datatype="string", size=100, name="Title"))
appconf.meta.append(FieldConf(id="pool_sort", datatype="number", size=4, name="Number"))
appconf.meta.append(FieldConf(id="pool_wfa", datatype="string", size=20, name="Workflow"))
appconf.meta.append(FieldConf(id="pool_wfp", datatype="string", size=20, name="Workflow"))

# test data -----------------------------------------------------------------------
data1_1 = { "ftext": "this is text!",
            "fnumber": 123456,
            "fdate": "2008/06/23 16:55:00",
            "ftime": "16:55:00",
            "flist": ["item 1", "item 2", "item 3"],
            "fmselect": "item 5",
            "funit": 35,
            "funitlist": [34, 35, 36],
            "pool_filename":"äüöß and others",
            "pool_type": "type1"}
data2_1 = { "fstr": "this is sting!",
            "ftext": "this is text!",
            "pool_filename": "äüöß and others",
            "pool_type": "type2"}
data3_1 = { "pool_filename": "title data 3",
            "fstr": "testing type 3!"}

data1_2 = { "ftext": "this is a new text!",
            "ftime": "23:08:13.000500",
            "funit": 0,
            "pool_filename":"new title data 1"}
data2_2 = { "fstr": "this is new sting!",
            "pool_filename": "new title data 2"}

file2_1_data=b"This is the first text"
file2_2_data=b"This is the text in the second file"
file2_1 = {"filename":"file1.txt", "file":file2_1_data}
file2_2 = {"filename":"file2.txt", "file":file2_2_data}


# empty -------------------------------------------------------------------------
def app_db(modules=None):
    app = Application()
    app.Register(appconf)
    if modules:
        for m in modules:
            app.Register(m)
    p = Portal()
    p.Register(app, "nive")
    app.SetupApplication()
    dbfile = DvPath(app.dbConfiguration.dbName)
    if not dbfile.IsFile():
        dbfile.CreateDirectories()
    root = DvPath(app.dbConfiguration.fileRoot)
    if not root.IsDirectory():
        root.CreateDirectories()

    """
    db = app.db
    try:
        cursor = db.Execute("select id from pool_meta where id=1")
        db.Execute("select id from data1 where id=1", cursor=cursor)
        db.Execute("select id from data2 where id=1", cursor=cursor)
        db.Execute("select id from data3 where id=1", cursor=cursor)
        db.Execute("select id from pool_files where id=1", cursor=cursor)
        db.Execute("select id from pool_sys where id=1", cursor=cursor)
        db.Execute("select id from pool_groups where id=1", cursor=cursor)
        db.Execute("select title from pool_meta where id=1", cursor=cursor)
        cursor.close()
    except:
        app.GetTool("nive.tools.dbStructureUpdater")()
    """

    # disable this to update test tables each time the tests are called
    app.GetTool("nive.tools.dbStructureUpdater")()
    app.Startup(None)
    return app

def app_nodb():
    app = Application()
    app.Register(appconf)
    app.Register(DatabaseConf())
    p = Portal()
    p.Register(app, "nive")
    app.SetupApplication()
    try:
        app.Startup(None)
    except OperationalError:
        pass
    return app

def emptypool(app, files=False):
    db = app.db
    cursor = db.Execute("delete FROM pool_meta")
    db.Execute("delete FROM pool_files", cursor=cursor)
    db.Execute("delete FROM pool_fulltext", cursor=cursor)
    db.Execute("delete FROM pool_groups", cursor=cursor)
    db.Execute("delete FROM pool_sys", cursor=cursor)
    db.Execute("delete FROM data3", cursor=cursor)
    db.Execute("delete FROM data2", cursor=cursor)
    db.Execute("delete FROM data1", cursor=cursor)
    db.Commit()
    if files:
        import shutil
        shutil.rmtree(str(db.root), ignore_errors=True)
        db.root.CreateDirectories()

def createpool(path, app):
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
    type = "type1"
    data = data1_1
    user = User("test")
    o = c.Create(type, data = data, user = user)
    return o

def createObj2(c):
    type = "type2"
    data = data2_1
    user = User("test")
    o = c.Create(type, data = data, user = user)
    return o

def createObj3(c):
    type = "type3"
    data = data3_1
    user = User("test")
    o = c.Create(type, data = data, user = user)
    return o

def createObj1file(c):
    type = "type1"
    data = data1_1.copy()
    data["file1"] = File(**file2_1)
    data["file2"] = File(**file2_2)
    user = User("test")
    o = c.Create(type, data = data, user = user)
    return o

def createObj2file(c):
    type = "type2"
    data = data2_1.copy()
    data["file2"] = File(**file2_1)
    user = User("test")
    o = c.Create(type, data = data, user = user)
    return o

def maxobj(r):
    id = r.GetMaxID()
    return r.obj(id)


def populate(testobj):
    # create three levels of entries
    level1 = 5
    level2 = 5
    level3_1 = 5
    level3_2 = 5
    c = testobj.app.root
    ids = []
    n = 0
    for i in range(0, level1):
        o = createObj1(c)
        n += 1
        ids.append(o.id)
        for i2 in range(0, level2):
            o2 = createObj1(o)
            n += 1
            for i3 in range(0, level3_1):
                createObj1(o2)
                n += 1
            for i3 in range(0, level3_2):
                o4 = createObj2(o2)
                id = o4.id
                n += 1
    testobj.ids = ids
    testobj.lastid = id

