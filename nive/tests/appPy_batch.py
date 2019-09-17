
import time

from nive.definitions import *
from nive.security import User

from nive.tests import db_app
from nive.tests.__local import DB_CONF



level1 = 5
level2 = 30
level3_1 = 9
level3_2 = 10


def test1():
    print("1) Testing objects create / delete, 3 level, no files")
    t = time.time()
    a=db_app.app_db([DB_CONF])
    print(time.time() - t, "Creating db (contains", db_app.statdb(a), "Entries)")
    t2 = time.time()
    r=a.root
    print(time.time() - t2, "Creating root")
    t2 = time.time()

    c=r
    ids=[]
    n=0
    user = User("test")
    for i in range(0,level1):
        o=db_app.createObj1(c)
        n+=1
        ids.append(o.id)
        for i2 in range(0,level2):
            o2=db_app.createObj1(o)
            n+=1
            for i3 in range(0,level3_1):
                db_app.createObj1(o2)
                n+=1
            for i3 in range(0,level3_2):
                db_app.createObj2(o2)
                n+=1

    print(time.time() - t2, "Creating", n, "objects")
    t2 = time.time()

    for id in ids:
        r.Delete(id, user=user)
    print(time.time() - t2, "Deleting objects recursively")

    print("------------")
    print(time.time() - t, "Total. Finished (contains", db_app.statdb(a), "Entries)")
    a.Close()
    print("--------------------------------------------------------")


def test2():
    print("2) Testing objects create / delete, 3 level, with files")
    t = time.time()
    a=db_app.app_db([DB_CONF])
    print(time.time() - t, "Creating db (contains", db_app.statdb(a), "Entries)")
    t2 = time.time()
    r=a.root
    print(time.time() - t2, "Creating root")
    t2 = time.time()

    c=r
    ids=[]
    n=0
    for i in range(0,level1):
        o=db_app.createObj1file(c)
        n+=1
        ids.append(o.id)
        for i2 in range(0,level2):
            o2=db_app.createObj1file(o)
            n+=1
            for i3 in range(0,level3_1):
                db_app.createObj1file(o2)
                n+=1
            for i3 in range(0,level3_2):
                db_app.createObj2file(o2)
                n+=1

    print(time.time() - t2, "Creating", n, "objects")
    t2 = time.time()

    user = User("test")
    for id in ids:
        r.Delete(id, user=user)
    print(time.time() - t2, "Deleting objects recursively")

    print("------------")
    print(time.time() - t, "Total Finished (contains", db_app.statdb(a), "Entries)")
    a.Close()
    print("--------------------------------------------------------")



def test3():
    print("3) Testing objects create / load / load batch / delete, 3 level, no files")
    t = time.time()
    a=db_app.app_db([DB_CONF])
    print(time.time() - t, "Creating db (contains", db_app.statdb(a), "Entries)")
    t2 = time.time()
    r=a.root
    print(time.time() - t2, "Creating root")
    t2 = time.time()

    c=r
    ids=[]
    n=0
    for i in range(0,level1):
        o=db_app.createObj1(c)
        n+=1
        ids.append(o.id)
        for i2 in range(0,level2):
            o2=db_app.createObj1(o)
            n+=1
            for i3 in range(0,level3_1):
                db_app.createObj1(o2)
                n+=1
            for i3 in range(0,level3_2):
                db_app.createObj2(o2)
                n+=1

    print(time.time() - t2, "Creating", n, "objects")
    t2 = time.time()
    del r
    del a

    a=db_app.app_db([DB_CONF])
    print(time.time() - t2, "Creating db (contains", db_app.statdb(a), "Entries)")
    t2 = time.time()
    r=a.root
    print(time.time() - t2, "Creating root")
    t2 = time.time()

    o1 = r.GetObjs(batch=True)
    cc = len(o1)
    for o in o1:
        o2 = o.GetObjs(batch=True)
        cc+=len(o2)
        for a in o2:
            o3 = a.GetObjs(batch=True)
            cc+=len(o3)
    print(time.time() - t2, "Loading batch", cc, "objects")
    t2 = time.time()

    user = User("test")
    for id in ids:
        r.Delete(id, user=user)
    print(time.time() - t2, "Deleting objects recursively")

    print("------------")
    print(time.time() - t, "Total. Finished (contains", db_app.statdb(a), "Entries)")
    a.Close()
    print("--------------------------------------------------------")



def test4():
    print("4) Testing objects create / load cache / delete, 3 level, no files")
    t = time.time()
    a=db_app.app_db([DB_CONF])
    print(time.time() - t, "Creating db (contains", db_app.statdb(a), "Entries)")
    t2 = time.time()
    r=a.root
    print(time.time() - t2, "Creating root")
    t2 = time.time()

    c=r
    ids=[]
    n=0
    c.useCache = True
    for i in range(0,level1):
        o=db_app.createObj1(r)
        o.useCache = True
        ids.append(o.id)
        #print(o.id)
        n+=1
        for i2 in range(0,level2):
            o2=db_app.createObj1(o)
            o2.useCache = True
            #print(o2.id,
            n+=1
            for i3 in range(0,level3_1):
                o3 = db_app.createObj1(o2)
                o3.useCache = True
                #print(o3.id,)
                n+=1
            for i3 in range(0,level3_2):
                o3 = db_app.createObj2(o2)
                o3.useCache = True
                #print(o3.id,)
                n+=1

    print(time.time() - t2, "Creating", n, "objects")
    t2 = time.time()

    o1 = r.GetObjs()
    cc = len(o1)
    for o in o1:
        o2 = o.GetObjs()
        cc+=len(o2)
        for a in o2:
            o3 = a.GetObjs()
            cc+=len(o3)
    print(time.time() - t2, "Loading", cc, "objects")
    t2 = time.time()

    r.Close()
    print(time.time() - t2, "Closing", cc, "objects")
    t2 = time.time()

    user = User("test")
    for id in ids:
        try:
            r.Delete(id, user=user)
        except Exception as e:
            raise Exception(str(ids)+ " " + str(id))
    print(time.time() - t2, "Deleting objects recursively")

    print("------------")
    print(time.time() - t, "Total. Finished (contains", db_app.statdb(a), "Entries)")
    a.Close()
    print("--------------------------------------------------------")


def test5():
    print("5) Testing objects create / close load cache / delete, 3 level, no files")
    t = time.time()
    a=db_app.app_db([DB_CONF])
    print(time.time() - t, "Creating db (contains", db_app.statdb(a), "Entries)")
    t2 = time.time()
    r=a.root
    print(time.time() - t2, "Creating root")
    t2 = time.time()

    c=r
    ids=[]
    n=0
    c.useCache = True
    for i in range(0,level1):
        o=db_app.createObj1(r)
        o.useCache = True
        ids.append(o.id)
        #print(o.id)
        n+=1
        for i2 in range(0,level2):
            o2=db_app.createObj1(o)
            o2.useCache = True
            #print(o2.id,)
            n+=1
            for i3 in range(0,level3_1):
                o3 = db_app.createObj1(o2)
                o3.useCache = True
                #print(o3.id,)
                n+=1
            for i3 in range(0,level3_2):
                o3 = db_app.createObj2(o2)
                o3.useCache = True
                #print(o3.id,)
                n+=1

    print(time.time() - t2, "Creating", n, "objects")
    t2 = time.time()

    r.Close()
    print(time.time() - t2, "Closing", n, "objects")
    t2 = time.time()

    r=a.root
    r.useCache = True
    o1 = r.GetObjs()
    cc = len(o1)
    for o in o1:
        o.useCache = True
        o2 = o.GetObjs()
        cc+=len(o2)
        for a in o2:
            a.useCache = True
            o3 = a.GetObjs()
            cc+=len(o3)
    print(time.time() - t2, "Loading after Close", cc, "objects")
    t2 = time.time()

    user = User("test")
    for id in ids:
        r.Delete(id, user=user)
        #try:
        #    r.Delete(id)
        #except Exception, e:
        #    raise Exception, str(ids)+ " " + str(id)
    print(time.time() - t2, "Deleting objects recursively")

    print("------------")
    print(time.time() - t, "Total. Finished (contains", db_app.statdb(a), "Entries)")
    a.Close()
    print("--------------------------------------------------------")



if __name__ == '__main__':
    db_app.emptypool(db_app.app_db([DB_CONF]))
    test1()
    test2()
    test3()
    test4()
    test5()
    db_app.emptypool(db_app.app_db([DB_CONF]))
