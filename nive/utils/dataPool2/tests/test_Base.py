# -*- coding: latin-1 -*-

import copy, time, StringIO
import unittest

from nive.utils.dataPool2.base import *
from nive.utils.dataPool2.connection import Connection

from nive.tests import __local

conf = {}
conf["root"] = __local.ROOT
conf["log"] = __local.ROOT+"sqllog.txt"
conf["codePage"] =    u"utf-8"
conf["dbCodePage"] = u"utf-8"
conf["backupVersions"] = 0
conf["useTrashcan"] = 0

conf["debug"] = 0


stdMeta = [u"id",
u"title",
u"pool_type",
u"pool_state",
u"pool_create",
u"pool_change",
u"pool_createdby",
u"pool_changedby",
u"pool_unitref",
u"pool_wfp",
u"pool_wfa",
u"pool_filename",
u"pool_stag",
u"pool_datatbl",
u"pool_dataref"]

struct = {}
struct[u"pool_meta"] = stdMeta
struct[u"data1"] = (u"ftext",u"fnumber",u"fdate",u"flist",u"fmselect",u"funit",u"funitlist")
struct[u"data2"] = (u"fstr",u"ftext")

ftypes = {}
ftypes[u"data2"] = {u"fstr":"string" ,u"ftext":"text"}

SystemFlds = (
{"id": u"id",             "datatype": "number",    "size": 8,   "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1000, "name": "ID",},
{"id": u"title",          "datatype": "string",    "size": 255, "default": "",    "required": 0,     "readonly": 0, "settings": {}, "sort":  1100, "name": "Title"},
{"id": u"pool_type",      "datatype": "list",      "size": 35,  "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1200, "name": "Type"},
{"id": u"pool_filename",  "datatype": "string",    "size": 255, "default": "",    "required": 0,     "readonly": 0, "settings": {}, "sort":  1400, "name": "Filename"},
{"id": u"pool_create",    "datatype": "date",      "size": 0,   "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1500, "name": "Created"},
{"id": u"pool_change",    "datatype": "datetime",  "size": 0,   "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1600, "name": "Changed"},
{"id": u"pool_createdby", "datatype": "string",    "size": 35,  "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1700, "name": "Created by"},
{"id": u"pool_changedby", "datatype": "string",    "size": 35,  "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1800, "name": "Changed by"},
{"id": u"pool_wfp",       "datatype": "list",      "size": 35,  "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1900, "name": "Workflow Process"},
{"id": u"pool_wfa",       "datatype": "list",      "size": 35,  "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  2000, "name": "Workflow Activity"},
{"id": u"pool_state",     "datatype": "number",    "size": 4,   "default": 1,     "required": 0,     "readonly": 1, "settings": {}, "sort":  2100, "name": "State"},
{"id": u"pool_unitref",   "datatype": "number",    "size": 8,   "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  5000, "name": "Reference"},
{"id": u"pool_stag",      "datatype": "float",     "size": 4,   "default": 0.0,   "required": 0,     "readonly": 1, "settings": {}, "sort":  5100, "name": "Select Number"},
{"id": u"pool_datatbl",   "datatype": "string",    "size": 35,  "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  5200, "name": "Data Table Name"},
{"id": u"pool_dataref",   "datatype": "number",    "size": 8,   "default":  0,    "required": 1,     "readonly": 1, "settings": {}, "sort":  5200, "name": "Data Table Name"},
)
Fulltext = ("id","text","files")
Files = ("id","filename","path","size","extension","filekey","version")

    
# test data ----------------------------------------------------------------------
data1_1 = {u"ftext": "this is text!",
             u"fnumber": 123456,
             u"fdate": "2008/06/23 16:55",
             u"flist": "item 2",
             u"fmselect": ["item 1", "item 2", "item 3"],
             u"funit": 35,
             u"funitlist": [34, 35, 36]}
data2_1 = {u"fstr": u"this is sting!",
           u"ftext": u"this is text!"}
meta1 = {u"title":"title "}
file1_1 = "File 1 content, text text text text."
file1_2 = "File 2 content, text text text text."




class BaseTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_structure(self):
        base = Base()
        base.structure.Init(structure=struct, stdMeta=struct[u"pool_meta"])
        self.assert_(len(base.structure.stdMeta)==len(struct[u"pool_meta"]))

    def test_config(self):
        base = Base(**conf)
        self.assert_(str(base.GetRoot()).find(conf["root"])!=-1)

    def test_database(self):
        base = Base()
        try:
            base.SetConnection(Connection())
        except TypeError:
            pass
        base.usedconnection
        base.connection
        try:
            base.dbapi
        except ConnectionError:
            pass
            
    def test_sql(self):
        base = Base()
        base.structure.Init(structure=struct, stdMeta=struct[u"pool_meta"])
        try:
            base.SetConnection(Connection())
        except TypeError:
            pass
        #FmtSQLSelect(self, flds, parameter={}, dataTable = "", start = 0, max = 1000, **kw)
        flds = list(struct[u"pool_meta"])+list(struct[u"data1"])
        base.FmtSQLSelect(struct[u"pool_meta"])
        base.FmtSQLSelect(struct[u"pool_meta"], parameter={u"id":1})
        base.FmtSQLSelect(struct[u"pool_meta"], parameter={u"pool_type":u"data1"})
        base.FmtSQLSelect(flds, parameter={u"pool_type":u"data1"}, dataTable=u"data1")
        base.FmtSQLSelect(list(struct[u"data1"])+[u"-count(*)"], parameter={u"id":123}, dataTable=u"data1", singleTable=1)
        base.FmtSQLSelect(flds,
                          parameter={u"pool_type":u"data1"},
                          dataTable=u"data1",
                          operators={u"pool_type":u">"})
        base.FmtSQLSelect(flds,
                          parameter={u"pool_type":u"data1"},
                          dataTable=u"data1",
                          operators={u"pool_type":u"="},
                          start=3,
                          max=20,
                          ascending=1,
                          sort=u"title, pool_type")
        base.FmtSQLSelect(flds,
                          parameter={u"pool_type":u"data1",u"id":[1,2,3,4,5,6,7,8,9,0]},
                          dataTable=u"data1",
                          operators={u"pool_type":u"=", u"id":u"IN"},
                          jointype=u"LEFT",
                          logicalOperator=u"or",
                          condition=u"meta__.id > 2",
                          join=u"INNER JOIN table1 on (meta__.id=table1.id)",
                          groupby=u"pool_type",
                          start=3,
                          max=20,
                          sort=u"title, pool_type")
        base.FmtSQLSelect(flds,
                          parameter={u"pool_type":(u"data1",u"")},
                          operators={u"pool_type":u"LIKE:OR"})
        base.GetFulltextSQL(u"test",
                            flds,
                          parameter={u"pool_type":u"data1",u"id":[1,2,3,4,5,6,7,8,9,0]},
                          dataTable=u"data1",
                          operators={u"pool_type":u"=", u"id":u"IN"},
                          jointype=u"LEFT",
                          logicalOperator=u"or",
                          condition=u"meta__.id > 2",
                          join=u"INNER JOIN table1 on (meta__.id=table1.id)",
                          groupby=u"pool_type",
                          start=3,
                          max=20,
                          sort=u"title, pool_type")


