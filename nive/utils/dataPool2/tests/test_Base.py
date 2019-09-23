# -*- coding: latin-1 -*-

import copy, time, io
import unittest

from nive.utils.dataPool2.base import *
from nive.utils.dataPool2.connection import Connection

from nive.tests import __local

conf = {}
conf["root"] = __local.ROOT
conf["log"] = __local.ROOT+"sqllog.txt"
conf["codePage"] =    "utf-8"
conf["dbCodePage"] = "utf-8"
conf["backupVersions"] = 0
conf["useTrashcan"] = 0

conf["debug"] = 0


stdMeta = ["id",
"title",
"pool_type",
"pool_state",
"pool_create",
"pool_change",
"pool_createdby",
"pool_changedby",
"pool_unitref",
"pool_wfp",
"pool_wfa",
"pool_filename",
"pool_stag",
"pool_datatbl",
"pool_dataref"]

struct = {}
struct["pool_meta"] = stdMeta
struct["data1"] = ("ftext","fnumber","fdate","flist","fmselect","funit","funitlist")
struct["data2"] = ("fstr","ftext")

ftypes = {}
ftypes["data2"] = {"fstr":"string" ,"ftext":"text"}

SystemFlds = (
{"id": "id",             "datatype": "number",    "size": 8,   "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1000, "name": "ID",},
{"id": "title",          "datatype": "string",    "size": 255, "default": "",    "required": 0,     "readonly": 0, "settings": {}, "sort":  1100, "name": "Title"},
{"id": "pool_type",      "datatype": "list",      "size": 35,  "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1200, "name": "Type"},
{"id": "pool_filename",  "datatype": "string",    "size": 255, "default": "",    "required": 0,     "readonly": 0, "settings": {}, "sort":  1400, "name": "Filename"},
{"id": "pool_create",    "datatype": "date",      "size": 0,   "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1500, "name": "Created"},
{"id": "pool_change",    "datatype": "datetime",  "size": 0,   "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  1600, "name": "Changed"},
{"id": "pool_createdby", "datatype": "string",    "size": 35,  "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1700, "name": "Created by"},
{"id": "pool_changedby", "datatype": "string",    "size": 35,  "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1800, "name": "Changed by"},
{"id": "pool_wfp",       "datatype": "list",      "size": 35,  "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  1900, "name": "Workflow Process"},
{"id": "pool_wfa",       "datatype": "list",      "size": 35,  "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  2000, "name": "Workflow Activity"},
{"id": "pool_state",     "datatype": "number",    "size": 4,   "default": 1,     "required": 0,     "readonly": 1, "settings": {}, "sort":  2100, "name": "State"},
{"id": "pool_unitref",   "datatype": "number",    "size": 8,   "default": "",    "required": 0,     "readonly": 1, "settings": {}, "sort":  5000, "name": "Reference"},
{"id": "pool_stag",      "datatype": "float",     "size": 4,   "default": 0.0,   "required": 0,     "readonly": 1, "settings": {}, "sort":  5100, "name": "Select Number"},
{"id": "pool_datatbl",   "datatype": "string",    "size": 35,  "default": "",    "required": 1,     "readonly": 1, "settings": {}, "sort":  5200, "name": "Data Table Name"},
{"id": "pool_dataref",   "datatype": "number",    "size": 8,   "default":  0,    "required": 1,     "readonly": 1, "settings": {}, "sort":  5200, "name": "Data Table Name"},
)
Fulltext = ("id","text","files")
Files = ("id","filename","path","size","extension","filekey","version")

    
# test data ----------------------------------------------------------------------
data1_1 = {"ftext": "this is text!",
             "fnumber": 123456,
             "fdate": "2008/06/23 16:55",
             "flist": "item 2",
             "fmselect": ["item 1", "item 2", "item 3"],
             "funit": 35,
             "funitlist": [34, 35, 36]}
data2_1 = {"fstr": "this is sting!",
           "ftext": "this is text!"}
meta1 = {"title":"title "}
file1_1 = b"File 1 content, text text text text."
file1_2 = b"File 2 content, text text text text."




class BaseTest(unittest.TestCase):

    def test_structure(self):
        base = Base()
        base.structure.Init(structure=struct, stdMeta=struct["pool_meta"])
        self.assertTrue(len(base.structure.stdMeta)==len(struct["pool_meta"]))

    def test_config(self):
        base = Base(**conf)
        self.assertTrue(str(base.GetRoot()).find(conf["root"])!=-1)

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
        base.structure.Init(structure=struct, stdMeta=struct["pool_meta"])
        try:
            base.SetConnection(Connection())
        except TypeError:
            pass
        #FmtSQLSelect(self, flds, parameter={}, dataTable = "", start = 0, max = 1000, **kw)
        flds = list(struct["pool_meta"])+list(struct["data1"])
        base.FmtSQLSelect(struct["pool_meta"])
        base.FmtSQLSelect(struct["pool_meta"], parameter={"id":1})
        base.FmtSQLSelect(struct["pool_meta"], parameter={"pool_type":"data1"})
        base.FmtSQLSelect(flds, parameter={"pool_type":"data1"}, dataTable="data1")
        base.FmtSQLSelect(list(struct["data1"])+["-count(*)"], parameter={"id":123}, dataTable="data1", singleTable=1)
        base.FmtSQLSelect(flds,
                          parameter={"pool_type":"data1"},
                          dataTable="data1",
                          operators={"pool_type":">"})
        base.FmtSQLSelect(flds,
                          parameter={"pool_type":"data1"},
                          dataTable="data1",
                          operators={"pool_type":"="},
                          start=3,
                          max=20,
                          ascending=1,
                          sort="title, pool_type")
        base.FmtSQLSelect(flds,
                          parameter={"pool_type":"data1","id":[1,2,3,4,5,6,7,8,9,0]},
                          dataTable="data1",
                          operators={"pool_type":"=", "id":"IN"},
                          jointype="LEFT",
                          logicalOperator="or",
                          condition="meta__.id > 2",
                          join="INNER JOIN table1 on (meta__.id=table1.id)",
                          groupby="pool_type",
                          start=3,
                          max=20,
                          sort="title, pool_type")
        base.FmtSQLSelect(flds,
                          parameter={"pool_type":("data1","")},
                          operators={"pool_type":"LIKE:OR"})
        base.GetFulltextSQL("test",
                            flds,
                          parameter={"pool_type":"data1","id":[1,2,3,4,5,6,7,8,9,0]},
                          dataTable="data1",
                          operators={"pool_type":"=", "id":"IN"},
                          jointype="LEFT",
                          logicalOperator="or",
                          condition="meta__.id > 2",
                          join="INNER JOIN table1 on (meta__.id=table1.id)",
                          groupby="pool_type",
                          start=3,
                          max=20,
                          sort="title, pool_type")


