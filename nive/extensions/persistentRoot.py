
from datetime import datetime

from nive.definitions import Conf, IConf 
from nive.definitions import Interface, implementer
from nive.helper import DumpJSONConf, LoadJSONConf

        
class IPersistentRoot(Interface):
    """
    """
    
@implementer(IPersistentRoot)
class Persistent(object):
    """
    Extension for nive root objects to store values
    
    Persistent values are can be accessed via `root.data` and `root.meta`.
    Use `Update()` or `Commit()` to store values. 
    Functions are compatible to nive objects.
    
    Meta and data values are stored as a single dict `root values` in 
    pool_sys table.
    
    Root configuration needs a list of data field definitions configuration.data.
    
    Requires: Events
    """
    defaultKey = ".root.storage"
    storagekey = ""
    notifyAllRoots = True

    def Init(self):
        self.storagekey = self.configuration.id+self.defaultKey
        self.LoadStoredValues()

    
    def LoadStoredValues(self):
        """
        Load values
        
        Event: - dataloaded()
        """
        values = self.app.LoadSysValue(self.storagekey)
        if values:
            values = LoadJSONConf(values, default=Conf)
            if isinstance(values, dict) or IConf.providedBy(values):
                data, meta, files = self.SplitData(values)
                self.data.update(data)
                self.meta.update(meta)
                if not hasattr(self, "files"):
                    self.files = {}
                self.files.update(files)
        self.Signal("dataloaded")
    
    def Commit(self, user):
        """
        Commit data values

        Event: - commit()
        """
        self.CommitInternal(user)
           
    def CommitInternal(self, user):
        """
        Commit data values

        Event: - commit()
        """
        values = {}
        if hasattr(self, "files"):
            values.update(self.files)
        values.update(self.data)
        values.update(self.meta)
        values["pool_change"] = datetime.now(self.app.pytimezone)
        values["pool_changedby"] = str(user)
        vstr = DumpJSONConf(values)
        self.app.StoreSysValue(self.storagekey, vstr)
        if self.notifyAllRoots:
            # call Init for other persistent roots to update values
            for root in self.app.GetRoots():
                if root.idhash == self.idhash:
                    continue
                if IPersistentRoot.providedBy(root):
                    root.LoadStoredValues()
        self.Signal("commit")

    def Update(self, values, user):
        """
        Update and store data values
        """
        data, meta, files = self.SplitData(values)
        self.data.update(data)
        self.meta.update(meta)
        self.files.update(files)
        self.Commit(user)
        return True
        
    def SplitData(self, sourceData):
        """
        Split sourceData dictionary in data, meta and file based on this objects
        configuration. Unused fields in source data are ignored.
        
        returns data, meta, files (each as dictionary)
        """
        data = {}
        meta = {}
        files = {}
        if self.configuration.get("data"):
            for f in self.configuration.get("data"):
                id = f["id"]
                if id in sourceData:
                    if f["datatype"]=="file":
                        files[id] = sourceData[id]
                    else:
                        data[id] = sourceData[id]
        for f in self.app.configurationQuery.GetAllMetaFlds(False):
            id = f["id"]
            if id in sourceData:
                meta[id] = sourceData[id]
        return data, meta, files
        
        
