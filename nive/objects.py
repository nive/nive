# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
This file provides *object* functionality for objects_. The different components
are separated into classes. However these classes are not meant to be used as standalone. 

object.files values ::
        
    tag = file fldname
    filename = filename
    file = readable file object
    fileid = unique file id as number
    uid = fileid as string
    size = file size in bytes
    path = absolute local path
    mime = file mime type
    extension = file extension
    tempfile = True/False. If True file is not committed, yet.

"""

import weakref

from nive.definitions import implementer
from nive.definitions import StagContainer, ReadonlySystemFlds
from nive.definitions import IFieldConf, ICache, IContainer, INonContainer, IObject
from nive.definitions import ConfigurationError
from nive.workflow import WorkflowNotAllowed, ObjectWorkflow
from nive.security import SetupRuntimeAcls

from nive.events import Events



class ObjectRead(Events):
    """
    Object implementation with read access.
    """

    def __init__(self, id, dbEntry, parent, configuration, **kw):
        self.__name__ = str(id)
        self.__parent__ = parent
        self.id = id
        self.idhash = id
        self.path = str(id)  # ? unused
        self.dbEntry = dbEntry
        self.configuration = configuration
        self.selectTag = configuration.get("selectTag", StagContainer)

        # load security
        acl = SetupRuntimeAcls(configuration.acl, self)
        if acl:
            # omit if empty. acls will be loaded from parent object
            self.__acl__ = acl

        self.Signal("init")

    # Shortcuts -----------------------------------------------------------

    @property
    def meta(self):
        """ meta values """
        return self.dbEntry.meta

    @property
    def data(self):
        """ data values """
        return self.dbEntry.data

    @property
    def files(self):
        """ files """
        return self.dbEntry.files

    @property
    def root(self):
        """ returns the current root object in parent chain """
        return self.parent.root

    @property
    def app(self):
        """ returns the cms application itself """
        return self.root.app

    @property
    def parent(self):
        """ returns the parent object """
        return self.__parent__

    @property
    def db(self):
        """ returns the database object """
        return self.app.db

    @property
    def relpath(self):
        """ returns relative excluding root"""
        path = self.GetParentPaths()
        path.reverse()
        path.append(self.GetPath())
        return "/".join(path[1:])

    # Values ------------------------------------------------------

    def GetFld(self, fldname):
        """
        Get the meta/data value and convert to type.

        returns value or None
        """
        # data
        for f in self.configuration["data"]:
            if f["id"] == fldname:
                if f["datatype"] == "file":
                    return self.GetFile(fldname)
                return self.data.get(fldname)

        # meta
        f = self.app.configurationQuery.GetMetaFld(fldname)
        if f:
            return self.meta.get(fldname)
        return None

    def GetFile(self, fldname, loadFileData=False):
        """
        Get the file as `File` object with meta information. The included file
        pointer is opened on read.
        This functions directly accesses the database and ignores files cached in
        object.files.

        returns File object or None
        """
        return self.dbEntry.GetFile(fldname, loadFileData=loadFileData)

    def GetFileByName(self, filename):
        """
        Get a file by filename. See GetFile() for details.
        This functions directly accesses the database and ignores files cached in
        object.files.

        returns File object or None
        """
        file = self.dbEntry.Files(parameter={"filename": filename})
        if not len(file):
            return None
        return file[0]

    def GetFileByUID(self, uid):
        """
        Get a file by uid. Only for files contained in this object. See GetFile() for details.
        This functions directly accesses the database and ignores files cached in
        object.files.

        returns File object or none
        """
        file = self.dbEntry.Files(parameter={"fileid": uid})
        if not len(file):
            return None
        return file[0]

    def GetID(self):
        """
        Get the object id as number.

        returns number
        """
        return self.id

    def GetTypeID(self):
        """ returns the object type as string """
        return self.configuration["id"]

    def GetTypeName(self):
        """ returns the the object type name as string """
        return self.configuration["name"]

    def GetFieldConf(self, fldId):
        """
        Get the FieldConf for the field with id = fldId. Looks up data, file and meta
        fields.

        If `fldId` is a Field Configuration (``nive.definitions.FieldConf``) the functions
        checks if the field id is defined for the object.

        returns FieldConf or None
        """
        if IFieldConf.providedBy(fldId):
            f = [d for d in self.configuration.data if d["id"] == fldId.id]
            if f:
                return fldId
        else:
            f = [d for d in self.configuration.data if d["id"] == fldId]
            if f:
                return f[0]
        return self.app.configurationQuery.GetMetaFld(fldId)

    def GetTitle(self):
        """ returns the objects meta.title as string """
        return self.meta.get("title", "")

    def GetPath(self):
        """ returns the url path name of the object as string """
        return self.__name__

    # parents ----------------------------------------------------

    def IsRoot(self):
        """ returns bool """
        return False

    def GetParents(self):
        """ returns all parent objects as list """
        p = []
        o = self
        while o:
            o = o.parent
            if o:
                p.append(o)
        return p

    def GetParentIDs(self):
        """ returns all parent ids as list """
        p = []
        o = self
        while o:
            o = o.parent
            if o:
                p.append(o.id)
        return p

    def GetParentTitles(self):
        """ returns all parent titles as list """
        p = []
        o = self
        while o:
            o = o.parent
            if o:
                p.append(o.GetTitle())
        return p

    def GetParentPaths(self):
        """ returns all parent paths as list """
        p = []
        o = self
        while o:
            o = o.parent
            if o:
                p.append(o.GetPath())
        return p

    def IsContainer(self):
        """ returns if this object is a container """
        return IContainer.providedBy(self)

    # tools ----------------------------------------------------

    def GetTool(self, name):
        """
        Load a tool for execution in the objects context. Only works for tools applied
        to this objects type. ::

            returns the tool or None

        Event
        - loadToool(tool=toolObj)
        """
        t = self.app.GetTool(name, self)
        self.Signal("loadTool", tool=t)
        return t

    def Close(self):
        """
        Close the object and all contained objects. Currently only used in combination with caches.

        Event
        - close()
        """
        self.Signal("close")
        if ICache.providedBy(self):
            # opt
            for o in self.GetAllFromCache():
                o.Close()
            p = self.parent
            if ICache.providedBy(p):
                p.RemoveCache(self.id)
        self.dbEntry.Close()




class ObjectWrite:
    """
    Provides *edit* functionality for objects.

    Requires (Object, ObjectWorkflow)
    """

    @property
    def workflow(self):
        return  ObjectWorkflow(self)

    def SplitData(self, sourceData):
        """
        Split sourceData dictionary in data, meta and file based on this objects
        configuration. Unused fields in source data are ignored.
        
        returns data, meta, files (each as dictionary)
        """
        data = {}
        meta = {}
        files = {}
        for f in self.configuration["data"]:
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


    def Commit(self, user):
        """
        Commit changes made to data, meta and file attributes and
        calls workflow "edit" action.
        
        Event: 
        - commit()
        
        Workflow action: edit
        """
        wf = self.workflow
        # check workflow
        if not wf.WfAllow("edit", user=user):
            raise WorkflowNotAllowed("Workflow: Not allowed (edit)")
        self.CommitInternal(user=user)
        # call wf
        try:
            wf.WfAction("edit", user=user)
        except Exception as e:
            self.Undo()
            raise 
        return True


    def Undo(self):
        """
        Undo changes made to data, meta and file attributes
        
        Event: 
        - undo()
        """
        self.Signal("undo")
        self.dbEntry.Undo()


    def Update(self, data, user):
        """
        Updates data, commits and calls workflow "edit" action.
        *data* can contain data, meta and files. ::
        
            data = dictionary containing data, meta and files
            user = the current user
            returns bool 
        
        Events:
         
        - update(data)
        - commit()
        
        Workflow action: edit
        """
        app = self.app
        wf = self.workflow
        # check workflow
        if not wf.WfAllow("edit", user=user):
            raise WorkflowNotAllowed("Workflow: Not allowed (edit)")
        self.Signal("update", data=data)
        self.UpdateInternal(data)
        # call wf
        try:
            wf.WfAction("edit", user=user)
        except Exception as e:
            self.Undo()
            raise 

        if app.configuration.autocommit:
            self.CommitInternal(user=user)
        return True


    def StoreFile(self, fldname, file, user):
        """
        Store a file under fldname. Existing files will be replaced. ::
        
            fldname = field name to store the file
            file = the file to store as FileObject
            user = the current user
            returns bool
        
        Events: 
        
        - storeFile(filename, fldname)
        
        Workflow action: edit
        """
        app = self.app
        wf = self.workflow
        # check workflow
        if not wf.WfAllow("edit", user=user):
            raise WorkflowNotAllowed("Workflow: Not allowed (edit)")
        self.Signal("storeFile", file=file, fldname=fldname)
        self.dbEntry.CommitFile(fldname, file)
        # call wf
        try:
            wf.WfAction("edit", user=user)
        except Exception as e:
            self.Undo()
            raise 

        if app.configuration.autocommit:
            self.db.Commit()
        return True


    def DeleteFile(self, fldname, user):
        """
        Delete a file from this object. ::

            fldname = field name to store the file
            user = the current user
            returns bool

        Event: 
        - deleteFile(fldname)
        
        Workflow action: edit
        """
        if not fldname:
            return False
        app = self.app
        wf = self.workflow
        # check workflow
        if not wf.WfAllow("edit", user=user):
            raise WorkflowNotAllowed("Workflow: Not allowed (edit)")
        self.Signal("deleteFile", fldname=fldname)
        result = self.dbEntry.DeleteFile(fldname)
        if not result:
            return False
        # call wf
        try:
            wf.WfAction("edit", user=user)
        except Exception as e:
            self.Undo()
            raise 

        if app.configuration.autocommit:
            self.CommitInternal(user=user)
        return True


    def RenameFile(self, filekey, filename, user):
        """
        Changes the filename field of the file `filekey`. ::

            filekey = file to set the new filename for
            filename = new filename
            user = the current user
            returns bool

        -
        """
        if self.dbEntry.RenameFile(filekey, filename):
            self.dbEntry.Touch()
            self.Commit(user)
            return True
        return False
    
    
    # Edit functions without workflow ------------------------------------------

    def UpdateInternal(self, data):
        """
        Update this objects data without calling workflow actions or events
        
        returns bool
        """
        data, meta, files = self.SplitData(data)
        # delete system fields
        system = ReadonlySystemFlds
        #opt
        if meta:
            for f in system:
                if f in meta:
                    del meta[f]
        # store data
        self.meta.update(meta)
        self.data.update(data)
        self.files.update(files)
        return True


    def CommitInternal(self, user):
        """
        Commit changes made to data, meta and files attributes without calling wf 
        
        Event: 
        - commit(user)
        """
        self.Signal("commit", user=user)
        self.dbEntry.Commit(user=user)


    def CreateSelf(self, data, user, **kw):
        """
        Called after the new object is created.
        
        Event: 
        - wfInit(processID)

        Workflow action: create
        """
        # initialize workflow
        wf = self.workflow
        wf.WfInit(user)

        # split data for pool
        self.UpdateInternal(data)
        self.meta["pool_type"] = self.configuration.id
        self.meta["pool_unitref"] = self.parent.id
        self.meta["pool_stag"] = self.selectTag

        # call wf
        try:
            wf.WfAction("create", user=user)
        except Exception as e:
            self.Undo()
            raise 

        return



@implementer(INonContainer, IObject)
class Object(ObjectRead, ObjectWrite):
    """
    Object implementation with read and write access.
    """

    pass