# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import json
import time
from datetime import datetime
from datetime import time as datetime_time

from nive.utils.utils import ConvertToDateTime
from nive.utils.dataPool2.files import File


# Database records wrapper ---------------------------------------------------------------------------

class Wrapper(object):
    """
    Wrappers are mapping objects for data, files and meta. Content can be accessed as
    dictionary field.
    Changes are stored temporarily in memory.
    """

    __wrapper__ = 1
    meta = False
    
    def __init__(self, entry, content=None):
        self._entry_ = entry
        self._temp_ = {}
        self._content_ = None
        
    def __repr__(self):
        return str(type(self)) 
    
    def __dir__(self):
        return ["_temp_", "_content_", "_entry_"]
    
    def __setitem__(self, key, value):
        if key in (u"id", u"pool_datatbl", u"pool_dataref"):
            return
        self._temp_[key] = self._entry_().DeserializeValue(key, value, self.meta)

    def __getitem__(self, key):
        if self._temp_.has_key(key):
            return self._temp_[key]
        if not self._content_:
            self._Load()
        return self._content_.get(key)


    def __getattr__(self, key):
        if key in self.__dict__.keys():
            return self.__dict__[key]
        if self._temp_.has_key(key):
            return self._temp_[key]
        if not self._content_:
            self._Load()
        return self._content_.get(key)


    def close(self):
        self._entry_ = None
        self._temp_.clear()
        self._content_ = None


    def clear(self):
        """
        Reset contents, temp data and entry obj
        """
        self._temp_.clear()


    def copy(self):
        """
        Returns a copy of current content
        """
        if not self._content_:
            self._Load()
        c = self._content_.copy()
        c.update(self._temp_)
        return c


    def has_key(self, key):
        if self.HasTempKey(key):
            return True
        return key in self.keys()


    def get(self, key, default=None):
        try:
            data = self[key]
            if data is None:
                return default
            return data
        except AttributeError:
            return default


    def set(self, key, data):
        self[key] = data


    def update(self, dict, force = False):
        dict = self._entry_().DeserializeValue(None, dict, self.meta)
        if force:
            for k in dict.keys():
                data = dict[k]
                if isinstance(data, bytes):
                    dict[k] = self._entry_().pool.DecodeText(data)
            self._temp_.update(dict)
            return
        for k in dict.keys():
            self[k] = dict[k]


    def keys(self):
        if not self._content_:
            self._Load()
        t = self._content_.keys()
        t += self._temp_.keys()
        return t



    def IsEmpty(self):                return self._content_ is None
    def GetTemp(self):                return self._temp_
    def HasTemp(self):                return self._temp_ != {}
    def GetTempKey(self, key):        return self._temp_.get(key)
    def HasTempKey(self, key):        return self._temp_.has_key(key)

    def GetEntry(self):                return self._entry_()

    def SetContent(self, content):
        if not self._content_:
            self._content_ = content
        else:
            self._content_.update(content)

    def EmptyTemp(self):
        self._temp_.clear()

    def _Load(self):
        self._content_ = {}
        pass


class MetaWrapper(Wrapper):
    """
    wrapper class for meta content
    """
    meta = True
    
    def _Load(self):
        self._content_ = {}
        self._entry_()._PreloadMeta()



class DataWrapper(Wrapper):
    """
    wrapper class for data content
    """

    def _Load(self):
        self._content_ = {}
        self._entry_()._PreloadData()


class FileWrapper(Wrapper):
    """
    wrapperclass for files. contains only filemta and returns file streams on read.
    update and __setitem__ take File object with o.file and o.filename attr as parameter
    entry = {"filename": "", "path": <absolute path for temp files>, "file": <file stream>}
    """

    def __setitem__(self, key, filedata):
        """
        filedata can be a dictionary, File object or file path
        """
        if not filedata:
            if key in self._temp_:
                del self._temp_[key]
            elif self._content_ and key in self._content_:
                del self._content_[key]
            return
        if isinstance(filedata, dict):
            file = File(key, filedict=filedata, fileentry=self._entry_())
            filedata = file
        elif isinstance(filedata, bytes):
            # load from temp path
            file = File(key, fileentry=self._entry_())
            file.fromPath(filedata)
            filedata = file
        filedata.tempfile = True
        self._temp_[key] = filedata


    def set(self, key, filedata):
        self[key] = filedata


    def SetContent(self, files):
        self._content_ = {}
        if isinstance(files, dict):
            for f in files:
                self._content_[f] = files[f]
            return
        for f in files:
            self._content_[f["filekey"]] = f


    def _Load(self):
        files = self._entry_().Files()
        self._content_ = {}
        for f in files:
            self._content_[f["filekey"]] = f
        return self._content_.keys()


#  Pool Structure ---------------------------------------------------------------------------


class PoolStructure(object):
    """
    Data Pool 2 Structure handling. Defines a table field mapping. If field types are available serializing 
    and deserializing is performed on database reads and writes.

    ::
    
        structure =
            {
             meta:   (field1, field2, ...),
             type1_table: (field5, field6, ...),
             type2_table: (field8, field9, ...),
            }

        fieldtypes = 
            {
             meta: {field1: string, field2: number},
             type1_table: {field5: DateTime, field6: text},
             type2_table: {field8: DateTime, field9: text},
            }
            
        stdMeta = (field1, field2)

    Deserialization datatypes ::
    
        string, htext, text, list, code, radio, email, password, url -> unicode
        number, float, unit -> number 
        bool -> 0/1
        file -> bytes
        timestamp -> float
        date, datetime -> datetime
        multilist, checkbox, urllist -> unicode tuple
        unitlist -> number tuple
        json -> python type list, tuple or dict

    Serialization datatypes ::
    
        string, htext, text, list, code, radio, email, password, url -> unicode
        number, float, unit -> number 
        bool -> 0/1
        file -> bytes
        timestamp -> float
        date, datetime -> datetime
        multilist, checkbox, urllist -> json
        unitlist -> json
        json -> json
        
    If fieldtype (`fieldtypes`) information is not given json data is stored with `_json_`
    prefix.

    """
    MetaTable = u"pool_meta"
    
    def __init__(self, structure=None, fieldtypes=None, stdMeta=None, codepage="utf-8", **kw):
        #
        self.stdMeta = ()
        self.structure = {}
        self.fieldtypes = {}
        self.serializeCallbacks = {}
        self.deserializeCallbacks = {}
        if structure:
            self.Init(structure, fieldtypes, stdMeta, codepage, **kw)
        

    def Init(self, structure, fieldtypes=None, stdMeta=None, codepage="utf-8", **kw):
        s = structure.copy()
        self.codepage = codepage
        meta = list(s[self.MetaTable])
        # add default fields
        if not u"pool_dataref" in s[self.MetaTable]:
            meta.append(u"pool_dataref")
        if not u"pool_datatbl" in s[self.MetaTable]:
            meta.append(u"pool_datatbl")
        s[self.MetaTable] = tuple(meta)
        for k in s:
            s[k] = tuple(s[k])
        self.structure = s
        
        if fieldtypes:
            self.fieldtypes = fieldtypes
        
        if stdMeta:
            self.stdMeta = tuple(stdMeta)


    def IsEmpty(self):
        return self.structure=={}

    
    def __getitem__(self, key, version=None):
        return self.structure[key]

    def get(self, key, default=None, version=None):
        return self.structure.get(key, default)

    def has_key(self, key, version=None):
        return self.structure.has_key(key)

    def keys(self, version=None):
        return self.structure.keys()
    
    
    def serialize(self, table, field, value):
        # if field==None and value is a dictionary multiple values are serialized
        if field==None and isinstance(value, dict):
            newdict = {}
            for field, v in value.items():
                try:        t = self.fieldtypes[table][field]
                except:     t = None
                newdict[field] = self._se(v, t, field)
            return newdict
        else:
            try:        t = self.fieldtypes[table][field]
            except:     t = None
            value = self._se(value, t, field)
        return value
        

    def deserialize(self, table, field, value):
        # if field==None and value is a dictionary multiple values are deserialized
        if field is None and isinstance(value, dict):
            newdict = {}
            for field, v in value.items():
                try:        t = self.fieldtypes[table][field]
                except:     t = None
                newdict[field] = self._de(v, t, field)
            return newdict
        else:
            try:        t = self.fieldtypes[table][field]
            except:     t = None
            value = self._de(value, t, field)
        return value


    def _se(self, value, fieldtype, field):
        if not fieldtype:
            # no datatype information set
            if isinstance(value, datetime):
                return value.strftime(u"%Y-%m-%d %H:%M:%S")
            elif isinstance(value, (list, tuple)):
                if isinstance(value[0], bytes):
                    # list of strings:
                    value = [unicode(v, self.codepage) for v in value]
                value = u"_json_"+json.dumps(value)
            elif isinstance(value, bytes):
                value = unicode(value, self.codepage)
            return value
        
        if isinstance(fieldtype, dict):
            fieldtype = fieldtype[u"datatype"]
            
        # call serialize callback function
        if fieldtype in self.serializeCallbacks:
            return self.serializeCallbacks[fieldtype](value, field)
            
        if fieldtype == "number":
            if isinstance(value, basestring):
                value = long(value)
            elif isinstance(value, float):
                value = long(value)
        
        elif fieldtype == "float":
            if isinstance(value, basestring):
                value = float(value)

        elif fieldtype in ("date", "datetime"):
            if isinstance(value, (float,int,long)):
                value = unicode(datetime.fromtimestamp(value))
            elif value is None:
                pass
            elif not isinstance(value, unicode):
                value = unicode(value)
        
        elif fieldtype == "time":
            if isinstance(value, (float,int,long)):
                value = unicode(datetime.fromtimestamp(value).strftime(u"HH:MM:SS.%f"))
            elif value is None:
                pass
            elif not isinstance(value, unicode):
                value = unicode(value)

        elif fieldtype == "timestamp":
            if value is None:
                pass
            elif not isinstance(value, basestring):
                value = unicode(value)
        
        elif fieldtype in ("list","radio"):
            # to single item string
            if isinstance(value, (list, tuple)):
                if value:
                    value = value[0]
                else:
                    value = u""

        elif fieldtype in ("multilist", "checkbox", "mselection", "mcheckboxes", "urllist", "unitlist"):
            # to json formatted list
            if not value:
                value = u""
            elif isinstance(value, basestring):
                value = [value]
            if isinstance(value, (list, tuple)):
                if isinstance(value[0], bytes):
                    # list of strings:
                    value = [unicode(v, self.codepage) for v in value]
                value = json.dumps(value)

        elif fieldtype in ("bool"):
            if isinstance(value, basestring):
                if value.lower()==u"true":
                    value = 1
                elif value.lower()==u"false":
                    value = 0
            else:
                try:
                    value = int(value)
                except:
                    value = 0

        elif fieldtype == "json":
            if not value:
                value = u""
            elif not isinstance(value, basestring):
                value = json.dumps(value)
            
        # assure unicode except filedata
        if isinstance(value, bytes) and fieldtype!="file":
            value = unicode(value, self.codepage)
        
        return value


    def _de(self, value, fieldtype, field):
        if not fieldtype:
            # no datatype information set
            if isinstance(value, basestring) and value.startswith(u"_json_"):
                value = json.loads(value[len(u"_json_"):])
            if isinstance(value, bytes):
                value = unicode(value, self.codepage)
            return value

        if isinstance(fieldtype, dict):
            fieldtype = fieldtype[u"datatype"]

        # call serialize callback function
        if fieldtype in self.deserializeCallbacks:
            return self.deserializeCallbacks[fieldtype](value, field)

        if fieldtype in ("date", "datetime"):
            # -> to datetime
            if isinstance(value, basestring):
                value = ConvertToDateTime(value)
            elif isinstance(value, (float,int,long)):
                value = datetime.fromtimestamp(value)
                    
        elif fieldtype == "time":
            # -> to datetime.time
            if isinstance(value, basestring):
                # misuse datetime parser
                value2 = ConvertToDateTime(u"2015-01-01 "+unicode(value))
                if value2:
                    value = datetime_time(value2.hour,value2.minute,value2.second,value2.microsecond)
            elif isinstance(value, (float,int,long)):
                value = datetime.fromtimestamp(value)
                value = datetime_time(value.hour,value.minute,value.second,value.microsecond)

        elif fieldtype == "timestamp":
            if isinstance(value, basestring):
                value = float(value)
                    
        elif fieldtype in ("multilist", "checkbox", "mselection", "mcheckboxes", "urllist", "unitlist"):
            # -> to string tuple
            # unitlist -> to number tuple
            if not value:
                value = u""
            elif isinstance(value, basestring):
                if value.startswith(u"_json_"):
                    value = json.loads(value[len(u"_json_"):])
                else:
                    try:
                        value = tuple(json.loads(value))
                    except ValueError:
                        # bw 0.9.12 convert line based values
                        if "\r\n" in value:
                            value = value.split("\r\n")
                        else:
                            value = (value,)
            elif isinstance(value, list):
                value = tuple(value)
            if fieldtype == "unitlist":
                value = tuple([long(v) for v in value])
            
        elif fieldtype == "json":
            # -> to python type
            if not value:
                value = None
            elif isinstance(value, basestring):
                value = json.loads(value)
            
        return value
    
    