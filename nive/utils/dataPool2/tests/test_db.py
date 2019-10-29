# -*- coding: latin-1 -*-

import unittest

from time import time

from nive.utils.dataPool2.tests.test_Base import stdMeta, struct, data1_1, data2_1, meta1, file1_1, file1_2




class dbTest(object):

    def statdb(self):
        c = self.pool.GetCountEntries()
        #print "Count entries in DB:", c
        return c

    # entries ---------------------------------------------------------------------------
    def create1(self):
        #print "Create Entry",
        e=self.pool.CreateEntry("data1", user="unittest")
        e.Commit(user="unittest")
        #print e.GetID(), "OK"
        return e.GetID()

    def create2(self):
        #print "Create Entry",
        e=self.pool.CreateEntry("data2", user="unittest")
        e.Commit(user="unittest")
        #print e.GetID(), "OK"
        return e.GetID()

    def get(self, id):
        #print "Load entry", id
        e=self.pool.GetEntry(id)
        #print "OK"
        return e

    # set ---------------------------------------
    def set1(self, id):
        #print "Store data", id,
        e=self.pool.GetEntry(id)
        self.assertTrue(e)
        e.data.update(data1_1)
        e.meta.update(meta1)
        e.Commit(user="unittest")
        self.assertTrue(e.GetMeta())
        d=e.GetData()
        self.assertTrue(d.get("ftext")    == data1_1.get("ftext")    )
        self.assertTrue(d.get("fnumber")    == data1_1.get("fnumber")    )
        self.assertTrue(self.pool.GetDBDate(str(d.get("fdate"))) == self.pool.GetDBDate(str(data1_1.get("fdate"))))
        self.assertTrue(d.get("flist")    == data1_1.get("flist")    )
        self.assertTrue(d.get("fmselect") == data1_1.get("fmselect") )
        self.assertTrue(d.get("funit")    == data1_1.get("funit")    )
        self.assertTrue(d.get("funitlist")== data1_1.get("funitlist"))
        self.assertTrue(d.get("ftext"))
        #print "OK"

    def set2(self, id):
        #print "Store data", id,
        e=self.pool.GetEntry(id)
        self.assertTrue(e)
        e.data.update(data2_1)
        e.meta.update(meta1)
        e.Commit(user="unittest")
        self.assertTrue(e.GetMeta())
        d=e.GetData()
        self.assertTrue(d.get("ftext")    == data2_1.get("ftext")    )
        self.assertTrue(d.get("fstr")     == data2_1.get("fstr")    )
        self.assertTrue(d.get("ftext"))
        #print "OK"

    def setfile1(self, id):
        #print "Store file", id,
        e=self.pool.GetEntry(id)
        self.assertTrue(e)
        self.assertTrue(e.CommitFile("file1", {"file":file1_1, "filename":"file1.txt"}))
        e.Commit(user="unittest")
        self.assertTrue(e.GetFile("file1").read() == file1_1)
        #print "OK"

    def setfile2(self, id):
        #print "Store file", id,
        e=self.pool.GetEntry(id)
        self.assertTrue(e)
        self.assertTrue(e.CommitFile("file2", {"file":file1_2, "filename":"file2.txt"}))
        e.Commit(user="unittest")
        self.assertTrue(e.GetFile("file2").read() == file1_2)
        #print "OK"


    # get --------------------------------------------------------------------------
    def data1(self, id):
        #print "Check entry data", id,
        e=self.pool.GetEntry(id)
        d=e.GetData()
        self.assertTrue(d.get("ftext")    == data1_1.get("ftext")    )
        self.assertTrue(d.get("fnumber")    == data1_1.get("fnumber")    )
        self.assertTrue(self.pool.GetDBDate(str(d.get("fdate"))) == self.pool.GetDBDate(str(data1_1.get("fdate"))))
        self.assertTrue(d.get("flist")    == data1_1.get("flist")    )
        self.assertTrue(d.get("fmselect") == data1_1.get("fmselect") )
        self.assertTrue(d.get("funit")    == data1_1.get("funit")    )
        self.assertTrue(d.get("funitlist")== data1_1.get("funitlist"))
        self.assertTrue(d.get("ftext"))
        #print "OK"

    def data2(self, id):
        #print "Check entry data", id,
        e=self.pool.GetEntry(id)
        d=e.GetData()
        self.assertTrue(d.get("ftext")    == data2_1.get("ftext")    )
        self.assertTrue(d.get("fstr")     == data2_1.get("fstr")    )
        self.assertTrue(d.get("ftext"))
        #print "OK"

    def file1(self, id):
        #print "Load file", id,
        e=self.pool.GetEntry(id)
        self.assertTrue(e.GetFile("file1").read() == file1_1)
        #print "OK"

    def file2(self, id):
        #print "Load file", id,
        e=self.pool.GetEntry(id)
        self.assertTrue(e.GetFile("file2").read() == file1_2)
        #print "OK"

    def fileErr(self, id):
        #print "Load non existing file", id,
        e=self.pool.GetEntry(id)
        self.assertTrue(e.GetFile("file1") == None)
        #print "OK"

    # getstream --------------------------------------------------------------------------
    def file1stream(self, id):
        #print "Load file", id,
        e=self.pool.GetEntry(id)
        s=e.GetFile("file1")
        d = s.read()
        s.close()
        self.assertTrue(d == file1_1)
        #print "OK"

    def file2stream(self, id):
        #print "Load file", id,
        e=self.pool.GetEntry(id)
        s=e.GetFile("file2")
        d=s.read()
        s.close()
        self.assertTrue(d == file1_2)
        #print "OK"

    # functions ------------------------------------------------------------------------
    def stat(self, id):
        e=self.pool.GetEntry(id)
        self.assertTrue(e.GetMetaField("pool_createdby")=="unittest")
        self.assertTrue(e.GetMetaField("pool_changedby")=="unittest")
        #print "Create: %s by %s    Changed: %s by %s" % (e.GetMetaField("pool_create"), e.GetMetaField("pool_createdby"), e.GetMetaField("pool_change"), e.GetMetaField("pool_changedby"))

    def delete(self, id):
        #print "Delete", id,
        e=self.pool.GetEntry(id)
        self.assertTrue(e)
        del e
        self.assertTrue(self.pool.DeleteEntry(id))
        self.pool.Commit(user="unittest")

    def duplicate(self, id,file=True):
        #print "Duplicate", id,
        e=self.pool.GetEntry(id)
        n=e.Duplicate(file)
        self.assertTrue(n)
        n.Commit(user="unittest")
        #print "OK"
        return n.GetID()

    def filetest(self, id):
        #print "File test", id,
        e=self.pool.GetEntry(id)
        self.assertTrue(e)

        self.assertSetEqual(set(e.FileKeys()), {"file1","file2"})

        self.assertTrue(e.GetFile("file1").filename=="file1.txt")
        self.assertTrue(e.GetFile("file2").filename=="file2.txt")
        self.assertTrue(e.GetFile("file1").filename)
        self.assertTrue(e.GetFile("file2").filename)

        self.assertTrue(e.GetFile("file1"))
        self.assertTrue(e.GetFile("file2"))
        self.assertTrue(e.GetFile("file3")==None)
        self.assertTrue(e.GetFile("")==None)

        l=e.Files({})
        self.assertTrue(len(l)==2)
        l2=[]
        for f in l:
            l2.append(f["filekey"])
        self.assertTrue("file1" in l2)
        self.assertTrue("file2" in l2)
        #print "OK"





    # new test fncs -----------------------------------------------------------------------------

    def test_create_empty(self):

        t = time()
        c = self.statdb()
        # creating
        id1=self.create1()
        e=self.get(id1)
        del e
        self.stat(id1)

        id2=self.create2()
        e=self.get(id2)
        del e
        self.stat(id2)

        # cnt    ok
        c2 = self.statdb()
        self.assertTrue(c+2==c2)

        # deleting
        self.delete(id1)
        self.delete(id2)
        c3 = self.statdb()
        self.assertTrue(c==c3)




    def test_create_base(self):

        t = time()
        c = self.statdb()
        # creating
        id1=self.create1()
        e=self.get(id1)
        del e
        self.stat(id1)

        id2=self.create2()
        e=self.get(id2)
        del e
        self.stat(id2)

        # cnt    ok
        c2 = self.statdb()
        self.assertTrue(c+2==c2)

        #update data
        self.set1(id1)
        self.set2(id2)
        self.setfile1(id1)
        self.setfile2(id1)

        #load data
        self.data1(id1)
        self.data2(id2)
        self.file1(id1)
        self.file2(id1)

        # deleting
        self.delete(id1)
        self.delete(id2)
        c3 = self.statdb()
        self.assertTrue(c==c3)



    def test_files_base(self):

        t = time()
        c = self.statdb()

        # creating
        id1=self.create1()
        e=self.get(id1)

        #update data
        self.set1(id1)
        self.setfile1(id1)
        self.setfile2(id1)

        #load data
        self.file1(id1)
        self.file2(id1)

        # file
        self.filetest(id1)

        # deleting
        self.delete(id1)
        c3 = self.statdb()
        self.assertTrue(c==c3)


    def test_preload(self):

        t = time()
        self.statdb()

        id=self.create1()

        #print "Preload Skip", id,
        e = self.pool.GetEntry(id, preload="skip")
        self.assertTrue(e.GetDataRef()>0 and e.GetDataTbl()!="")
        del e
        #print "OK"

        #print "Preload Meta", id,
        e = self.pool.GetEntry(id, preload="meta")
        self.assertTrue(e.GetDataRef()>0 and e.GetDataTbl()!="")
        del e
        #print "OK"

        #print "Preload All", id,
        e = self.pool.GetEntry(id, preload="all")
        self.assertTrue(e.GetDataRef()>0 and e.GetDataTbl()!="")
        del e
        #print "OK"

        #print "Preload MetaData", id,
        e = self.pool.GetEntry(id, preload="metadata")
        self.assertTrue(e.GetDataRef()>0 and e.GetDataTbl()!="")
        del e
        #print "OK"

        #print "Preload StdMeta", id,
        e = self.pool.GetEntry(id, preload="stdmeta")
        self.assertTrue(e.GetDataRef()>0 and e.GetDataTbl()!="")
        del e
        #print "OK"

        #print "Preload StdMetaData", id,
        e = self.pool.GetEntry(id, preload="stdmetadata")
        self.assertTrue(e.GetDataRef()>0 and e.GetDataTbl()!="")
        del e
        #print "OK"

        self.delete(id)
        self.assertTrue(self.pool.IsIDUsed(id) == False)


    def test_duplicate_base(self):

        t = time()
        c=self.statdb()

        # creating
        id1=self.create1()
        id2=self.create2()

        # cnt    ok
        c2 = self.statdb()
        self.assertTrue(c+2==c2)

        #update data
        self.set1(id1)
        self.set2(id2)
        self.setfile1(id1)
        self.setfile2(id1)

        #load data
        self.data1(id1)
        self.data2(id2)
        self.file1(id1)
        self.file2(id1)

        # duplicate
        id3=self.duplicate( id1)
        id4=self.duplicate( id2)
        id5=self.duplicate( id1, file=False)

        #load dupl. data
        self.data1(id3)
        self.data1(id5)
        self.data2(id4)
        self.file1(id3)
        self.file2(id3)
        self.fileErr(id5)

        # deleting
        self.delete(id1)
        self.delete(id2)
        self.delete(id3)
        self.delete(id4)
        self.delete(id5)
        c3 = self.statdb()
        self.assertTrue(c==c3)


    def test_sql(self):

        t = time()
        sql, values=self.pool.FmtSQLSelect(list(stdMeta)+list(struct["data1"]),
                        {"pool_type": "data1", "ftext": "123", "fnumber": 300000},
                        sort = "title, id, fnumber",
                        ascending = 0,
                        dataTable = "data1",
                        operators={"pool_type":"=", "ftext": "<>", "fnumber": "<"},
                        start=1,
                        max=123)
        self.pool.Query(sql, values)
        c=self.pool.Execute(sql, values)
        c.close()
        #print "OK"

        sql, values=self.pool.FmtSQLSelect(list(struct["data1"]),
                                     {"ftext": "", "fnumber": 3},
                                     dataTable="data1",
                                     sort = "id, fnumber",
                                     ascending = 1,
                                     operators={"ftext": "=", "fnumber": "="},
                                     start=1,
                                     max=123,
                                     singleTable=1)
        self.pool.Query(sql, values)
        c=self.pool.Execute(sql, values)
        c.close()
        #print "OK"

        #print "GetFulltextSQL",
        sql, values=self.pool.GetFulltextSQL("is",
                            list(stdMeta)+list(struct["data1"]),
                            {},
                            sort = "title",
                            ascending = 1,
                            dataTable = "data1")
        self.pool.Query(sql, values)
        c=self.pool.Execute(sql, values)
        c.close()
        #print "OK"


    def test_sql2(self):

        t = time()
        sql1, values1=self.pool.FmtSQLSelect(list(stdMeta)+list(struct["data1"]),
                        {"pool_type": "data1", "ftext": "", "fnumber": 3},
                        sort = "title, id, fnumber",
                        ascending = 0,
                        dataTable = "data1",
                        operators={"pool_type":"=", "ftext": "<>", "fnumber": ">"},
                        start=1,
                        max=123)
        sql2, values2=self.pool.FmtSQLSelect(list(struct["data1"]),
                                     {"ftext": "", "fnumber": 3},
                                     dataTable="data1",
                                     sort = "id, fnumber",
                                     ascending = 1,
                                     operators={"ftext": "<>", "fnumber": ">"},
                                     start=1,
                                     max=123,
                                     singleTable=1)
        sql3, values3=self.pool.GetFulltextSQL("is",
                            list(stdMeta)+list(struct["data1"]),
                            {},
                            sort = "title",
                            ascending = 1,
                            dataTable = "data1")
        c=self.pool.connection.cursor()
        c.execute(sql1, values1)
        c.execute(sql2, values2)
        c.execute(sql3, values3)
        
        self.pool.SelectFields("data1", fields=("id",), idValues=[0], idColumn="id")
        self.pool.SelectFields("pool_meta", fields=("id","title","pool_type"), idValues=[1,2,3,4,5], idColumn="pool_unitref")


    def test_insertdelete(self):
        self.pool.DeleteRecords("pool_meta", {"pool_type": "notype", "title": "test entry"})
        self.pool.Commit()

        self.pool.InsertFields("pool_meta", {"pool_type": "notype", "title": "test entry"})
        self.pool.Commit()
        sql, values = self.pool.FmtSQLSelect(["id"], {"pool_type": "notype", "title": "test entry"}, dataTable="pool_meta", singleTable=1) 
        id = self.pool.Query(sql, values)
        self.assertTrue(id)
        
        self.pool.UpdateFields("pool_meta", id[0][0], {"pool_type": "notype 123", "title": "test entry 123"})
        self.pool.Commit()
        sql, values = self.pool.FmtSQLSelect(["id"], {"pool_type": "notype", "title": "test entry"}, dataTable="pool_meta", singleTable=1) 
        id = self.pool.Query(sql, values)
        self.assertFalse(id)
        sql, values = self.pool.FmtSQLSelect(["id"], {"pool_type": "notype 123", "title": "test entry 123"}, dataTable="pool_meta", singleTable=1) 
        id = self.pool.Query(sql, values)
        self.assertTrue(id)
        
        for i in id:
            self.pool.DeleteRecords("pool_meta", {"id":i[0]})
        self.pool.Commit()
        sql, values = self.pool.FmtSQLSelect(["id"], {"pool_type": "notype 123", "title": "test entry 123"}, dataTable="pool_meta", singleTable=1) 
        id = self.pool.Query(sql, values)
        self.assertFalse(id)


    def test_groups(self):
        userid = "123"
        group = "group:test"
        id = 1
        ref = "o"
        self.pool.RemoveGroups(id=id)
        self.assertFalse(self.pool.GetGroups(id, userid, group))
        self.assertFalse(self.pool.GetGroups(id))
        self.assertFalse(self.pool.GetGroups((id,id)))
        self.pool.AddGroup(id, userid, group)
        self.assertTrue(self.pool.GetGroups(id, userid, group))
        self.assertTrue(self.pool.GetGroups(id))
        self.assertTrue(self.pool.GetGroups((id,id)))

        self.pool.RemoveGroups(userid=userid, group=group, id=id)
        self.assertFalse(self.pool.GetGroups(id, userid, group))


    def test_search_files(self):

        t = time()
        c = self.statdb()

        # creating
        id1=self.create1()
        id2=self.create1()
        id3=self.create1()

        #update data
        self.set1(id1)
        self.setfile1(id1)
        self.setfile2(id1)

        self.set1(id2)
        self.setfile1(id2)
        self.setfile2(id2)

        self.set1(id3)
        self.setfile1(id3)
        self.setfile2(id3)

        dbfile = self.pool
        #print "SearchFilename",
        f1 = dbfile.SearchFilename("file1.txt")
        #print len(f1),
        self.assertTrue(len(f1)>=3)
        f2 = dbfile.SearchFilename("file2.txt")
        #print len(f2),
        self.assertTrue(len(f2)>=3)
        f3 = dbfile.SearchFilename("fileXXX.txt")
        #print len(f3),
        self.assertTrue(len(f3)==0)

        #print "SearchFiles",
        parameter={"id": (id1,id2,id3)}
        operators={"id": "IN"}
        f = dbfile.SearchFiles(parameter, operators=operators) #sort="filename",
        #print len(f),
        self.assertTrue(len(f)==6)
        parameter["filename"] = "file2.txt"
        operators["filename"] = "="
        f = dbfile.SearchFiles(parameter, operators=operators) #sort="size",
        #print len(f),
        self.assertTrue(len(f)==3)
        #print "OK"

        # deleting
        self.delete(id1)
        self.delete(id2)
        self.delete(id3)
        c3 = self.statdb()
        self.assertTrue(c==c3)


    def test_tree(self):
        base = self.pool
        #base.GetContainedIDs(base=0, sort="title", parameter="")
        #base.GetTree(flds=["id"], sort="title", base=0, parameter="")
        base.GetParentPath(1)
        base.GetParentTitles(1)





