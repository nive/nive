

import copy

from nive.utils.dataPool2.mysql.tests import test_MySql
try:
    from nive.utils.dataPool2.mysql.mySqlPool import *
except:
    pass

from . import test_db
from nive.utils.dataPool2.sqlite.sqlite3Pool import *


mode = "mysql"
printed = [""]

def print_(*kw):
    if type(kw)!=type(""):
        v = ""
        for a in kw:
            v += " "+str(a)
    else:
        v = kw
    if v == "":
        print(".",)
        printed.append("")
    else:
        printed[-1] += v
        

def getConnection():
    if mode == "mysql":
        c = MySqlConn(test_MySql.conn, 0)
        print_( "MySQL        -")
    elif mode == "mysqlinno":
        c = test_MySql.conn
        c["dbName"] = "ut_dataPool2inno"
        c = MySqlConn(c, 0)
        print_( "MySQL InnoDB -")
    else:
        c = Sqlite3Conn(test_db.conn, 0)
        print_( "Sqlite 3     -")
    return c

def getPool():
    if mode == "mysql":
        pool = MySql(test_MySql.conf)
        pool.SetStdMeta(copy.copy(test_MySql.stdMeta))
        pool.GetPoolStructureObj().SetStructure(test_MySql.struct)
        pool.CreateConnection(test_MySql.conn)
        print_( "MySQL        -")
    elif mode == "mysqlinno":
        pool = MySql(test_MySql.conf)
        pool.SetStdMeta(copy.copy(test_MySql.stdMeta))
        pool.GetPoolStructureObj().SetStructure(test_MySql.struct)
        c = test_MySql.conn
        c["dbName"] = "ut_dataPool2inno"
        pool.CreateConnection(c)
        print_( "MySQL InnoDB -")
    else:
        pool = Sqlite3(test_db.conf)
        pool.SetStdMeta(copy.copy(test_db.stdMeta))
        pool.GetPoolStructureObj().SetStructure(test_db.struct)
        pool.CreateConnection(test_db.conn)
        print_( "Sqlite 3     -")
    return pool

def empty():
    #if mode == "mysql":
    #    test_MySql.emptypool()
    #elif mode == "mysqlinno":
    #    test_MySql.emptypool()
    #else:
    #    t_db.emptypool()
    pass

def connects(n):
    c = getConnection()

    print_( "Connection: ")
    t = time.time()
    for i in range(0,n):
        c.connect()
        c.Close()
    t2 = time.time()
    print_( n, " connects in ", t2-t, "secs. ", (t2-t)/n, " per connect")
    print_()




def cursors(n):
    c = getConnection()
    c.connect()

    print_( "Cursor: ")
    t = time.time()
    for i in range(0,n):
        cu = c.cursor()
        cu.close()
    t2 = time.time()

    c.Close()
    print_( n, " cursors in ", t2-t, "secs. ", (t2-t)/n, " per cursor")
    print_()


def createsql(n):
    pool = getPool()

    print_( "Create SQL: ")
    t = time.time()
    for i in range(0,n):
        sql, values = pool.FmtSQLSelect(list(test_MySql.stdMeta)+list(test_MySql.struct["data1"]),
            {"pool_type": "data1", "ftext": "", "fnumber": 3},
            sort = "title, id, fnumber",
            ascending = 0,
            dataTable = "data1",
            operators={"pool_type":"=", "ftext": "<>", "fnumber": ">"},
            start=1,
            max=123)
    t2 = time.time()

    pool.Close()
    print_( n, " sql statements in ", t2-t, "secs. ", (t2-t)/n, " per statement")
    print_()


def sqlquery1(n, start):
    pool = getPool()

    print_( "SQL Query data+meta (join no index): ")
    t = time.time()
    for i in range(0,n):
        sql, values = pool.FmtSQLSelect(list(test_MySql.stdMeta)+list(test_MySql.struct["data1"]),
            {"pool_type": "data1", "ftext": "123", "fnumber": i+start},
            sort = "title, id, fnumber",
            ascending = 0,
            dataTable = "data1",
            operators={"pool_type":"=", "ftext": "LIKE", "fnumber": "!="},
            start=1,
            max=123)
        pool.Query(sql, values)
    t2 = time.time()

    pool.Close()
    print_( n, " queries in ", t2-t, "secs. ", (t2-t)/n, " per statement")
    print_()


def sqlquery2(n, start):
    pool = getPool()

    print_( "SQL Query data+meta=id (join index): ")
    t = time.time()
    for i in range(0,n):
        sql, values = pool.FmtSQLSelect(list(test_MySql.stdMeta)+list(test_MySql.struct["data1"]),
            {"id": i+start},
            sort = "title",
            ascending = 0,
            dataTable = "data1",
            operators={},
            start=1,
            max=123)
        pool.Query(sql, values)
    t2 = time.time()

    pool.Close()
    print_( n, " queries in ", t2-t, "secs. ", (t2-t)/n, " per statement")
    print_()


def sqlquery3(n, start):
    pool = getPool()

    print_( "SQL Query meta=id (index): ")
    t = time.time()
    for i in range(0,n):
        sql, values = pool.FmtSQLSelect(list(test_MySql.stdMeta),
            {"id": start+i},
            sort = "id",
            ascending = 0,
            dataTable = "pool_meta",
            singleTable = 1,
            operators={},
            start=1,
            max=123)
        pool.Query(sql, values)
    t2 = time.time()

    pool.Close()
    print_( n, " queries in ", t2-t, "secs. ", (t2-t)/n, " per statement")
    print_()


def sqlquery4(n, start):
    pool = getPool()

    print_( "SQL Query meta=id+pool_type=data1 (index): ")
    t = time.time()
    for i in range(0,n):
        sql, values = pool.FmtSQLSelect(list(test_MySql.stdMeta),
            {"id": start+i, "pool_type": "data1"},
            sort = "id",
            ascending = 0,
            dataTable = "pool_meta",
            singleTable = 1,
            operators={"pool_type": "="},
            start=1,
            max=123)
        pool.Query(sql, values)
    t2 = time.time()

    pool.Close()
    print_( n, " queries in ", t2-t, "secs. ", (t2-t)/n, " per statement")
    print_()


def sqlquery5(n, start):
    pool = getPool()

    print_( "SQL Query meta=id+pool_type=data1+data.funit (join index): ")
    t = time.time()
    for i in range(0,n):
        sql, values = pool.FmtSQLSelect(list(test_MySql.stdMeta),
            {"id": start+i, "pool_type": "data1", "funit": 35},
            sort = "id",
            ascending = 0,
            dataTable = "data1",
            operators={"pool_type": "="},
            start=1,
            max=123)
        pool.Query(sql, values)
    t2 = time.time()

    pool.Close()
    print_( n, " queries in ", t2-t, "secs. ", (t2-t)/n, " per statement")
    print_()


def sqlquery6(n):
    pool = getPool()

    print_( "SQL Query filename (text index): ")
    t = time.time()
    for i in range(0,n):
        files = pool.SearchFilename("file1xxx.txt")
    t2 = time.time()

    pool.Close()
    print_( n, " queries in ", t2-t, "secs. ", (t2-t)/n, " per statement")
    print_()


def createentries(n):
    pool = getPool()

    print_( "Create entries (nodb): ")
    t = time.time()
    for i in range(0,n):
        e=pool._GetPoolEntry(i, version=None, datatbl="data1", preload="skip", virtual=True)
    t2 = time.time()

    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()


def checkentries(n):
    pool = getPool()

    print_( "Create entries (nodb) and check exists: ")
    t = time.time()
    for i in range(0,n):
        e=pool._GetPoolEntry(i, version=None, datatbl="data1", preload="skip", virtual=True)
        e.Exists()
    t2 = time.time()

    pool.Close()
    print_( n, " checks in ", t2-t, "secs. ", (t2-t)/n, " per check")
    print_()

def createentries2(n):
    pool = getPool()

    print_( "Create entries (nodata): ")
    t = time.time()
    for i in range(0,n):
        e=pool.CreateEntry("data1")
        #e.data.update(data1_1)
        #e.meta.update(meta1)
        e.Commit()
    t2 = time.time()

    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()

def createentries3(n):
    pool = getPool()

    print_( "Create entries (data+meta): ")
    t = time.time()
    for i in range(0,n):
        e=pool.CreateEntry("data1")
        if i==0:  id = e.GetID()
        e.data.update(test_MySql.data1_1)
        e.meta.update(test_MySql.meta1)
        e.Commit()
    t2 = time.time()

    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()
    return id

def createentries4(n):
    pool = getPool()

    print_( "Create entries (data+meta+file): ")
    t = time.time()
    for i in range(0,n):
        e=pool.CreateEntry("data1")
        if i==0:  id = e.GetID()
        e.data.update(test_MySql.data1_1)
        e.meta.update(test_MySql.meta1)
        e.CommitFile("file1", {"file":test_MySql.file1_1, "filename": "file1.txt"})
        e.Commit()
    t2 = time.time()

    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()
    return id


def getentries1(n, start):
    pool = getPool()

    print_( "Get entries (all): ")
    t = time.time()
    for i in range(0,n):
        e=pool.GetEntry(i+start)
    t2 = time.time()

    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()

def getentries2(n, start):
    pool = getPool()

    print_( "Get entries (all+file): ")
    t = time.time()
    for i in range(0,n):
        e=pool.GetEntry(i+start, preload="all")
        f=e.GetFile("file1")
    t2 = time.time()

    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()

def getentries5(n, start):
    pool = getPool()

    print_( "Get entries (all+filestream): ")
    t = time.time()
    for i in range(0,n):
        e=pool.GetEntry(i+start, preload="all")
        #f=e.GetFile("file1")
    t2 = time.time()

    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()

def getentries4(n, start):
    pool = getPool()

    print_( "Get entries (meta): ")
    t = time.time()
    for i in range(0,n):
        e=pool.GetEntry(i+start, preload="meta")
    t2 = time.time()

    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()

def getbatch1(n, start):
    pool = getPool()

    print_( "Get batch (no preload): ")
    t = time.time()
    ids = []
    for i in range(0,n):
        ids.append(i+start)
    e=pool.GetBatch(ids, preload="skip")
    t2 = time.time()

    del e
    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()

def getbatch2(n, start):
    pool = getPool()

    print_( "Get batch (meta): ")
    t = time.time()
    ids = []
    for i in range(0,n):
        ids.append(i+start)
    e=pool.GetBatch(ids, preload="meta")
    t2 = time.time()

    del e
    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()

def getbatch3(n, start):
    pool = getPool()

    print_( "Get batch (all): ")
    t = time.time()
    ids = []
    for i in range(0,n):
        ids.append(i+start)
    e=pool.GetBatch(ids, preload="all")
    t2 = time.time()

    del e
    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()

def delentries(n, start):
    pool = getPool()

    print_( "Delete entries (meta+data): ")
    t = time.time()
    for i in range(0,n):
        pool.DeleteEntry(i+start)
        pool.Commit()
    t2 = time.time()

    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()


def delentries2(n, start):
    pool = getPool()

    print_( "Delete entries (meta+data+file): ")
    t = time.time()
    for i in range(0,n):
        pool.DeleteEntry(i+start)
        pool.Commit()
    t2 = time.time()

    pool.Close()
    print_( n, " entries in ", t2-t, "secs. ", (t2-t)/n, " per entry")
    print_()


def report(modes, printed):
    rep=[]
    c = len(printed)/len(modes)
    for n in range(0, c):
        p = 0
        for m in modes:
            rep.append(printed[p*c+n])
            p+=1
    print()
    print()
    i=0
    for p in rep:
        print(p)
        i+=1
        if i==len(modes):
            print()
            i=0


def run(modes):
    global mode , printed
    n = 1000
    printed = [""]
    for m in modes:
        mode = m
        print()
        print(mode,)
        empty()
        connects(n)
        cursors(n)
        createsql(n)
        createentries(n)
        checkentries(n)
        createentries2(n)
        id = createentries3(n)
        id2 = createentries4(n)
        getentries1(n, id2)
        getentries2(n, id2)
        getentries5(n, id2)
        getentries4(n, id2)
        getbatch1(n, id2)
        getbatch2(n, id2)
        getbatch3(n, id2)
        sqlquery1(n, id2)
        sqlquery2(n, id)
        sqlquery3(n, id2)
        sqlquery4(n, id)
        sqlquery5(n, id2)
        sqlquery6(n)
        delentries(n, id)
        delentries2(n, id2)
    report(modes, printed)


if __name__ == '__main__':
    #run(("sqlite3",))
    run(("sqlite3","mysql","mysqlinno"))
