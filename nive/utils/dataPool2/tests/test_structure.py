

import unittest
import time
from datetime import date

from nive.utils.dataPool2.structure import *

from nive.utils.dataPool2.tests import test_Base


ftypes = {}
ftypes["data2"] = {"fstr":"string",
                    "ftext":"text", 
                    "ftime":"timestamp", 
                    "fmultilist":"multilist",
                    "fcheckbox":"checkbox",
                    "furllist":"urllist", 
                    "funitlist":"unitlist",
                    "fbool":"bool",
                    "fjson":"json"}

ftypes["pool_meta"] = {}
for i in test_Base.SystemFlds:
    ftypes["pool_meta"][i["id"]] = i

class StructureTest(unittest.TestCase):

    def test_set1(self):
        structure = PoolStructure(structure=test_Base.struct, 
                                  fieldtypes=ftypes, 
                                  stdMeta=["id","pool_type"])
        self.assertTrue(structure.get("pool_meta"))
        self.assertTrue(len(structure.get("pool_meta")) == len(test_Base.struct["pool_meta"]))
        self.assertTrue(len(structure.get("data1"))==len(test_Base.struct["data1"]))
        self.assertTrue(len(structure.get("data2"))==len(test_Base.struct["data2"]))
        self.assertTrue(len(structure.stdMeta)==2)
        self.assertTrue(structure.fieldtypes["data2"]["fstr"]=="string")
        self.assertTrue(structure.codepage=="utf-8")

    def test_set2(self):
        structure = PoolStructure()
        structure.Init(structure=test_Base.struct, 
                       fieldtypes=ftypes, 
                       codepage="latin-1")
        self.assertTrue(structure.get("pool_meta"))
        self.assertTrue(len(structure.get("pool_meta")) == len(test_Base.struct["pool_meta"]))
        self.assertTrue(len(structure.get("data1"))==len(test_Base.struct["data1"]))
        self.assertTrue(len(structure.get("data2"))==len(test_Base.struct["data2"]))
        self.assertTrue(len(structure.stdMeta)==0)
        self.assertTrue(structure.fieldtypes["data2"]["fstr"]=="string")
        self.assertTrue(structure.codepage=="latin-1")
        
    def test_set3(self):
        structure = PoolStructure()
        structure.Init(structure={"pool_meta": [], "data1": [], "data2": []}, 
                       fieldtypes=ftypes, 
                       codepage="latin-1")
        self.assertTrue(structure.get("pool_meta"))
        self.assertTrue(len(structure.get("pool_meta"))==2)
        self.assertTrue(len(structure.get("data1"))==0)
        self.assertTrue(len(structure.get("data2"))==0)
        


    def test_empty(self):
        structure = PoolStructure()
        self.assertTrue(structure.IsEmpty())


    def test_func(self):
        structure = PoolStructure(structure=test_Base.struct, 
                                  fieldtypes=ftypes, 
                                  stdMeta=["id","pool_type"])
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
                                       stdMeta=["id","pool_type"])


    def test_serialize_notype(self):
        self.assertTrue(self.structure.serialize("pool_meta", "somevalue", 123)==123)
        self.assertTrue(isinstance(self.structure.serialize("pool_meta", "somevalue", "123"), str))
        value = datetime.now()
        self.assertTrue(self.structure.serialize("pool_meta", "somevalue", value)==value.strftime("%Y-%m-%d %H:%M:%S"))
        value = ("aaa","bbb")
        self.assertTrue(self.structure.serialize("pool_meta", "somevalue", value).startswith("_json_"))
        value = ("aaa","bbb")
        self.assertTrue(self.structure.serialize("pool_meta", "somevalue", value).startswith("_json_"))
        value = [1,2,3]
        self.assertTrue(self.structure.serialize("pool_meta", "somevalue", value).startswith("_json_"))
        
    def test_se_multilist(self):
        v = {"id":"123", "pool_stag":"123.12", "pool_wfa":["value"], "somevalue": "test"}
        values = self.structure.serialize("pool_meta", None, v)
        self.assertTrue(values["id"]==123)
        self.assertTrue(values["pool_stag"]==123.12)
        self.assertTrue(values["pool_wfa"]=="value")        

    def test_se_number(self):
        self.assertTrue(self.structure.serialize("pool_meta", "id", 123)==123)
        self.assertTrue(self.structure.serialize("pool_meta", "id", "123")==123)
        self.assertTrue(self.structure.serialize("pool_meta", "id", "123")==123)
        self.assertTrue(self.structure.serialize("pool_meta", "id", 123.12)==123)

    def test_se_float(self):
        self.assertTrue(self.structure.serialize("pool_meta", "pool_stag", 123)==123.0)
        self.assertTrue(self.structure.serialize("pool_meta", "pool_stag", "123.12")==123.12)
        self.assertTrue(self.structure.serialize("pool_meta", "pool_stag", "123.0")==123.0)
        self.assertTrue(self.structure.serialize("pool_meta", "pool_stag", 123.12)==123.12)

    def test_se_date(self):
        value = datetime.now()
        self.assertTrue(self.structure.serialize("pool_meta", "pool_change", value)) # compare with timezone
        value = date.today()
        self.assertTrue(self.structure.serialize("pool_meta", "pool_create", value)) # compare with timezone
        value = time.time()
        self.assertEqual(self.structure.serialize("data2", "ftime", value), value)

    def test_se_list(self):
        self.assertTrue(self.structure.serialize("pool_meta", "pool_wfa", "value")=="value")
        self.assertTrue(self.structure.serialize("pool_meta", "pool_wfa", ["value"])=="value")
        self.assertTrue(self.structure.serialize("pool_meta", "pool_wfa", ())=="")

    def test_se_mlist(self):
        self.assertTrue(self.structure.serialize("data2", "fmultilist", "value"))
        self.assertTrue(self.structure.serialize("data2", "fmultilist", ["value"]))
        self.assertTrue(self.structure.serialize("data2", "fmultilist", ("value",)))
        self.assertFalse(self.structure.serialize("data2", "fmultilist", ""))
        
        self.assertTrue(self.structure.serialize("data2", "checkbox", "value"))
        self.assertTrue(self.structure.serialize("data2", "furllist", "value"))
        self.assertTrue(self.structure.serialize("data2", "funitlist", "value"))

    def test_se_bool(self):
        self.assertTrue(self.structure.serialize("data2", "fbool", "true")==1)
        self.assertTrue(self.structure.serialize("data2", "fbool", "false")==0)
        self.assertTrue(self.structure.serialize("data2", "fbool", True)==1)
        self.assertTrue(self.structure.serialize("data2", "fbool", False)==0)
        self.assertTrue(self.structure.serialize("data2", "fbool", "True")==1)
        self.assertTrue(self.structure.serialize("data2", "fbool", "False")==0)
        self.assertTrue(self.structure.serialize("data2", "fbool", ("???",))==0)

    def test_se_json(self):
        self.assertTrue(self.structure.serialize("data2", "fjson", {"a":123,"b":"aaa"}))
        self.assertTrue(json.loads(self.structure.serialize("data2", "fjson", {"a":123,"b":"aaa"}))["a"]==123)
        self.assertTrue(json.loads(self.structure.serialize("data2", "fjson", {"a":123,"b":"aaa"}))["b"]=="aaa")
    
    
    def test_deserialize_notype(self):
        value = "_json_"+json.dumps(("aaa","bbb"))
        self.assertTrue(self.structure.deserialize("pool_meta", "somevalue", value)[0]=="aaa")
        self.assertTrue(self.structure.deserialize("pool_meta", "somevalue", "somevalue")=="somevalue")
        
    def test_ds_multilist(self):
        v = {"fmultilist": json.dumps(["aaa","bbb"]),"furllist":json.dumps(["aaa","bbb"]), "somevalue": "test"}
        values = self.structure.deserialize("data2", None, v)
        self.assertTrue(values["fmultilist"][0]=="aaa")
        self.assertTrue(values["furllist"][0]=="aaa")

    def test_ds_date(self):
        value = datetime.now()
        x=self.structure.deserialize("pool_meta", "pool_change", str(value))
        self.assertTrue(x.strftime("%Y-%m-%d %H:%M:%S")==value.strftime("%Y-%m-%d %H:%M:%S"))
        value = date.today()
        x=self.structure.deserialize("pool_meta", "pool_create", str(value))
        self.assertTrue(x.strftime("%Y-%m-%d")==value.strftime("%Y-%m-%d"))
        value = time.time()
        self.assertTrue(self.structure.deserialize("data2", "ftime", value))

    def test_ds_multilist2(self):
        self.assertTrue(self.structure.deserialize("data2", "fmultilist", json.dumps(["aaa","bbb"]))[0]=="aaa")
        self.assertTrue(self.structure.deserialize("data2", "fcheckbox", json.dumps(["aaa","bbb"]))[0]=="aaa")
        self.assertTrue(self.structure.deserialize("data2", "furllist", json.dumps(["aaa","bbb"]))[0]=="aaa")
        self.assertTrue(self.structure.deserialize("data2", "funitlist", json.dumps(["123","123"]))[0]=="123")
        self.assertTrue(self.structure.deserialize("data2", "fcheckbox", "aaa")[0]=="aaa")
        self.assertTrue(self.structure.deserialize("data2", "fcheckbox", ["aaa","bbb"])[0]=="aaa")
        
    def test_ds_json(self):
        self.assertTrue(self.structure.deserialize("data2", "fjson", json.dumps(["aaa","bbb"]))[0]=="aaa")



def seCallback(value, field):
    return value.swapcase()

def deCallback(value, field):
    return value.capitalize()



class CallbackTest(unittest.TestCase):

    def setUp(self):
        self.structure = PoolStructure(structure=test_Base.struct, 
                                       fieldtypes=ftypes, 
                                       stdMeta=["id","pool_type"])
        self.structure.serializeCallbacks = {"string": seCallback}
        self.structure.deserializeCallbacks = {"string": deCallback}


    def test_serialize_callback(self):
        self.assertTrue(self.structure.serialize("pool_meta", "title", "somevalue")=="SOMEVALUE")
        self.assertTrue(self.structure.deserialize("pool_meta", "title", "somevalue")=="Somevalue")

        
    def test_se_multilist(self):
        v = {"id":"123", "pool_stag":"123.12", "pool_wfa":["value"], "somevalue": "test"}
        values = self.structure.serialize("pool_meta", None, v)
        self.assertTrue(values["id"]==123)
        self.assertTrue(values["pool_stag"]==123.12)
        self.assertTrue(values["pool_wfa"]=="value")        

    def test_se_number(self):
        self.assertTrue(self.structure.serialize("pool_meta", "id", 123)==123)
        self.assertTrue(self.structure.serialize("pool_meta", "id", "123")==123)
        self.assertTrue(self.structure.serialize("pool_meta", "id", "123")==123)
        self.assertTrue(self.structure.serialize("pool_meta", "id", 123.12)==123)

    def test_se_float(self):
        self.assertTrue(self.structure.serialize("pool_meta", "pool_stag", 123)==123.0)
        self.assertTrue(self.structure.serialize("pool_meta", "pool_stag", "123.12")==123.12)
        self.assertTrue(self.structure.serialize("pool_meta", "pool_stag", "123.0")==123.0)
        self.assertTrue(self.structure.serialize("pool_meta", "pool_stag", 123.12)==123.12)

        