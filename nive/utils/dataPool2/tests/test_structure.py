

import copy, time, io
import unittest
from datetime import datetime
from datetime import date

from nive.utils.dataPool2.structure import *

from nive.tests import __local

from nive.utils.dataPool2.tests import test_Base


ftypes = {}
ftypes[u"data2"] = {u"fstr":"string",
                    u"ftext":"text", 
                    u"ftime":"timestamp", 
                    u"fmultilist":"multilist",
                    u"fcheckbox":"checkbox",
                    u"furllist":"urllist", 
                    u"funitlist":"unitlist",
                    u"fbool":"bool",
                    u"fjson":"json"}

ftypes[u"pool_meta"] = {}
for i in test_Base.SystemFlds:
    ftypes[u"pool_meta"][i["id"]] = i

class StructureTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_set1(self):
        structure = PoolStructure(structure=test_Base.struct, 
                                  fieldtypes=ftypes, 
                                  stdMeta=[u"id",u"pool_type"])
        self.assertTrue(structure.get(u"pool_meta"))
        self.assertTrue(len(structure.get(u"pool_meta")) == len(test_Base.struct[u"pool_meta"]))
        self.assertTrue(len(structure.get(u"data1"))==len(test_Base.struct[u"data1"]))
        self.assertTrue(len(structure.get(u"data2"))==len(test_Base.struct[u"data2"]))
        self.assertTrue(len(structure.stdMeta)==2)
        self.assertTrue(structure.fieldtypes[u"data2"][u"fstr"]=="string")
        self.assertTrue(structure.codepage==u"utf-8")

    def test_set2(self):
        structure = PoolStructure()
        structure.Init(structure=test_Base.struct, 
                       fieldtypes=ftypes, 
                       codepage="latin-1")
        self.assertTrue(structure.get(u"pool_meta"))
        self.assertTrue(len(structure.get(u"pool_meta")) == len(test_Base.struct[u"pool_meta"]))
        self.assertTrue(len(structure.get(u"data1"))==len(test_Base.struct[u"data1"]))
        self.assertTrue(len(structure.get(u"data2"))==len(test_Base.struct[u"data2"]))
        self.assertTrue(len(structure.stdMeta)==0)
        self.assertTrue(structure.fieldtypes[u"data2"][u"fstr"]=="string")
        self.assertTrue(structure.codepage==u"latin-1")
        
    def test_set3(self):
        structure = PoolStructure()
        structure.Init(structure={u"pool_meta": [], u"data1": [], u"data2": []}, 
                       fieldtypes=ftypes, 
                       codepage="latin-1")
        self.assertTrue(structure.get(u"pool_meta"))
        self.assertTrue(len(structure.get(u"pool_meta"))==2)
        self.assertTrue(len(structure.get(u"data1"))==0)
        self.assertTrue(len(structure.get(u"data2"))==0)
        


    def test_empty(self):
        structure = PoolStructure()
        self.assertTrue(structure.IsEmpty())


    def test_func(self):
        structure = PoolStructure(structure=test_Base.struct, 
                                  fieldtypes=ftypes, 
                                  stdMeta=[u"id",u"pool_type"])
        self.assertFalse(structure.IsEmpty())
        
        self.assertTrue(structure.get("pool_meta"))
        self.assertTrue(structure.get("none","aaa")=="aaa")
        self.assertTrue(structure["pool_meta"])
        self.assertTrue(structure["data1"])
        self.assertTrue(structure["data2"])
        self.assertTrue("data2" in structure)
        self.assertTrue(len(list(structure.keys()))==3)
        
        

        
class ConversionTest(unittest.TestCase):

    def setUp(self):
        self.structure = PoolStructure(structure=test_Base.struct, 
                                       fieldtypes=ftypes, 
                                       stdMeta=[u"id",u"pool_type"])

    def tearDown(self):
        pass


    def test_serialize_notype(self):
        self.assertTrue(self.structure.serialize(u"pool_meta", u"somevalue", 123)==123)
        self.assertTrue(isinstance(self.structure.serialize(u"pool_meta", u"somevalue", "123"), unicode))
        value = datetime.now()
        self.assertTrue(self.structure.serialize(u"pool_meta", u"somevalue", value)==value.strftime("%Y-%m-%d %H:%M:%S"))
        value = ("aaa","bbb")
        self.assertTrue(self.structure.serialize(u"pool_meta", u"somevalue", value).startswith(u"_json_"))
        value = (u"aaa",u"bbb")
        self.assertTrue(self.structure.serialize(u"pool_meta", u"somevalue", value).startswith(u"_json_"))
        value = [1,2,3]
        self.assertTrue(self.structure.serialize(u"pool_meta", u"somevalue", value).startswith(u"_json_"))
        
    def test_se_multilist(self):
        v = {u"id":u"123", u"pool_stag":u"123.12", u"pool_wfa":["value"], u"somevalue": "test"}
        values = self.structure.serialize(u"pool_meta", None, v)
        self.assertTrue(values[u"id"]==123)
        self.assertTrue(values[u"pool_stag"]==123.12)
        self.assertTrue(values[u"pool_wfa"]==u"value")        

    def test_se_number(self):
        self.assertTrue(self.structure.serialize(u"pool_meta", u"id", 123)==123)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"id", u"123")==123)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"id", "123")==123)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"id", 123.12)==123)

    def test_se_float(self):
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_stag", 123)==123.0)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_stag", u"123.12")==123.12)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_stag", "123.0")==123.0)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_stag", 123.12)==123.12)

    def test_se_date(self):
        value = datetime.now()
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_change", value)==unicode(value))
        value = date.today()
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_create", value)==unicode(value))
        value = time.time()
        self.assertTrue(self.structure.serialize(u"data2", u"ftime", value)==unicode(value))

    def test_se_list(self):
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_wfa", u"value")==u"value")
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_wfa", ["value"])=="value")
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_wfa", ())=="")

    def test_se_mlist(self):
        self.assertTrue(self.structure.serialize(u"data2", u"fmultilist", u"value"))
        self.assertTrue(self.structure.serialize(u"data2", u"fmultilist", [u"value"]))
        self.assertTrue(self.structure.serialize(u"data2", u"fmultilist", ("value",)))
        self.assertFalse(self.structure.serialize(u"data2", u"fmultilist", u""))
        
        self.assertTrue(self.structure.serialize(u"data2", u"checkbox", u"value"))
        self.assertTrue(self.structure.serialize(u"data2", u"furllist", u"value"))
        self.assertTrue(self.structure.serialize(u"data2", u"funitlist", u"value"))

    def test_se_bool(self):
        self.assertTrue(self.structure.serialize(u"data2", u"fbool", u"true")==1)
        self.assertTrue(self.structure.serialize(u"data2", u"fbool", u"false")==0)
        self.assertTrue(self.structure.serialize(u"data2", u"fbool", True)==1)
        self.assertTrue(self.structure.serialize(u"data2", u"fbool", False)==0)
        self.assertTrue(self.structure.serialize(u"data2", u"fbool", u"True")==1)
        self.assertTrue(self.structure.serialize(u"data2", u"fbool", u"False")==0)
        self.assertTrue(self.structure.serialize(u"data2", u"fbool", ("???",))==0)

    def test_se_json(self):
        self.assertTrue(self.structure.serialize(u"data2", u"fjson", {"a":123,"b":"aaa"}))
        self.assertTrue(json.loads(self.structure.serialize(u"data2", u"fjson", {"a":123,"b":"aaa"}))["a"]==123)
        self.assertTrue(json.loads(self.structure.serialize(u"data2", u"fjson", {"a":123,"b":"aaa"}))["b"]==u"aaa")
    
    
    def test_deserialize_notype(self):
        value = u"_json_"+json.dumps(("aaa","bbb"))
        self.assertTrue(self.structure.deserialize(u"pool_meta", u"somevalue", value)[0]==u"aaa")
        self.assertTrue(self.structure.deserialize(u"pool_meta", u"somevalue", "somevalue")==u"somevalue")
        
    def test_ds_multilist(self):
        v = {u"fmultilist": json.dumps(["aaa","bbb"]),u"furllist":json.dumps(["aaa","bbb"]), u"somevalue": "test"}
        values = self.structure.deserialize(u"data2", None, v)
        self.assertTrue(values[u"fmultilist"][0]=="aaa")
        self.assertTrue(values[u"furllist"][0]=="aaa")

    def test_ds_date(self):
        value = datetime.now()
        x=self.structure.deserialize(u"pool_meta", u"pool_change", unicode(value))
        self.assertTrue(x.strftime("%Y-%m-%d %H:%M:%S")==value.strftime("%Y-%m-%d %H:%M:%S"))
        value = date.today()
        x=self.structure.deserialize(u"pool_meta", u"pool_create", unicode(value))
        self.assertTrue(x.strftime("%Y-%m-%d")==value.strftime("%Y-%m-%d"))
        value = time.time()
        self.assertTrue(self.structure.deserialize(u"data2", u"ftime", value))

    def test_ds_multilist(self):
        self.assertTrue(self.structure.deserialize(u"data2", u"fmultilist", json.dumps(["aaa","bbb"]))[0]=="aaa")
        self.assertTrue(self.structure.deserialize(u"data2", u"fcheckbox", json.dumps(["aaa","bbb"]))[0]=="aaa")
        self.assertTrue(self.structure.deserialize(u"data2", u"furllist", json.dumps(["aaa","bbb"]))[0]=="aaa")
        self.assertTrue(self.structure.deserialize(u"data2", u"funitlist", json.dumps(["123","123"]))[0]==123)
        self.assertRaises(ValueError, self.structure.deserialize, u"data2", u"funitlist", json.dumps(["aaa","bbb"]))
        self.assertTrue(self.structure.deserialize(u"data2", u"fcheckbox", "aaa")[0]=="aaa")
        self.assertTrue(self.structure.deserialize(u"data2", u"fcheckbox", ["aaa","bbb"])[0]=="aaa")
        
    def test_ds_json(self):
        self.assertTrue(self.structure.deserialize(u"data2", u"fjson", json.dumps(["aaa","bbb"]))[0]=="aaa")



def seCallback(value, field):
    return value.swapcase()

def deCallback(value, field):
    return value.capitalize()



class CallbackTest(unittest.TestCase):

    def setUp(self):
        self.structure = PoolStructure(structure=test_Base.struct, 
                                       fieldtypes=ftypes, 
                                       stdMeta=[u"id",u"pool_type"])
        self.structure.serializeCallbacks = {"string": seCallback}
        self.structure.deserializeCallbacks = {"string": deCallback}


    def tearDown(self):
        pass


    def test_serialize_callback(self):
        self.assertTrue(self.structure.serialize(u"pool_meta", u"title", u"somevalue")==u"SOMEVALUE")
        self.assertTrue(self.structure.deserialize(u"pool_meta", u"title", u"somevalue")==u"Somevalue")

        
    def test_se_multilist(self):
        v = {u"id":u"123", u"pool_stag":u"123.12", u"pool_wfa":["value"], u"somevalue": "test"}
        values = self.structure.serialize(u"pool_meta", None, v)
        self.assertTrue(values[u"id"]==123)
        self.assertTrue(values[u"pool_stag"]==123.12)
        self.assertTrue(values[u"pool_wfa"]==u"value")        

    def test_se_number(self):
        self.assertTrue(self.structure.serialize(u"pool_meta", u"id", 123)==123)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"id", u"123")==123)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"id", "123")==123)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"id", 123.12)==123)

    def test_se_float(self):
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_stag", 123)==123.0)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_stag", u"123.12")==123.12)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_stag", "123.0")==123.0)
        self.assertTrue(self.structure.serialize(u"pool_meta", u"pool_stag", 123.12)==123.12)

        