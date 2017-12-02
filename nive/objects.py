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

See :py:mod:`nive.components.objects.base` for subclassing base classes
"""

import weakref

from nive.definitions import StagContainer, ReadonlySystemFlds
from nive.definitions import IFieldConf, ICache, IContainer
from nive.definitions import ConfigurationError
from nive.workflow import WorkflowNotAllowed
from nive.security import SetupRuntimeAcls


class Object(object):
    """    
    Object implementation with read access.
    """

    def __init__(self, id, dbEntry, parent, configuration, **kw):
        self.__name__ = str(id)
        self.__parent__ = parent
        self.id = id
        self.idhash = id
        self.path = str(id)
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
    def dataroot(self):
        """ returns the current root object in parent chain """
        return self.parent.dataroot

    @property
    def app(self):
        """ returns the cms application itself """
        return self.dataroot.app

    @property
    def parent(self):
        """ returns the parent object """
        return self.__parent__
    
    @property
    def db(self):
        """ returns the database object """
        return self.app.db


    # Values ------------------------------------------------------

    def GetFld(self, fldname):
        """
        Get the meta/data value and convert to type.
        
        returns value or None
        """
        #data
        for f in self.configuration["data"]:
            if f["id"] == fldname:
                if f["datatype"] == "file":
                    return self.GetFile(fldname)
                return self.data.get(fldname)

        # meta
        f = self.app.GetMetaFld(fldname)
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
        file = self.dbEntry.Files(parameter={u"filename":filename})
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
        file = self.dbEntry.Files(parameter={u"fileid":uid})
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
            f = filter(lambda d: d["id"]==fldId.id, self.configuration.data)
            if f:
                return fldId
        else:
            f = filter(lambda d: d["id"]==fldId, self.configuration.data)
            if f:
                return f[0]
        return self.app.GetMetaFld(fldId)

    def GetTitle(self):
        """ returns the objects meta.title as string """
        return self.meta.get("title","")

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
                p.append(o.GetID())
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
            #opt
            for o in self.GetAllFromCache():
                o.Close()
            p = self.parent
            if ICache.providedBy(p):
                p.RemoveCache(self.id)
        self.dbEntry.Close()


    # to be removed in future versions ------------------------------------------------------------

    def root(self):
        """ 
        bw 0.9.12: use `dataroot` property instead! 
        returns the current root object in parent chain 
        """
        return self.parent.root()

    def GetRoot(self):
        """bw 0.9.12: to be removed. returns the current root object """
        return self.dataroot

    def GetApp(self):
        """bw 0.9.12: to be removed. returns the cms main application object """
        return self.dataroot.app

    def GetParent(self):
        """bw 0.9.12: to be removed. returns the parent object in the hierarchy """
        return self.__parent__



class ObjectEdit:
    """
    Provides *edit* functionality for objects.

    Requires (Object, ObjectWorkflow)
    """

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
            if sourceData.has_key(id):
                if f["datatype"]=="file":
                    files[id] = sourceData[id]
                else:
                    data[id] = sourceData[id]
        for f in self.app.GetAllMetaFlds(False):
            id = f["id"]
            if sourceData.has_key(id):
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
        app = self.app
        # check workflow
        if not self.WfAllow("edit", user=user):
            raise WorkflowNotAllowed, "Workflow: Not allowed (edit)"
        self.CommitInternal(user=user)
        # call wf
        try:
            self.WfAction("edit", user=user)
        except Exception, e:
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
        # check workflow
        if not self.WfAllow("edit", user=user):
            raise WorkflowNotAllowed, "Workflow: Not allowed (edit)"
        self.Signal("update", data=data)
        self.UpdateInternal(data)
        # call wf
        try:
            self.WfAction("edit", user=user)
        except Exception, e:
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
        # check workflow
        if not self.WfAllow("edit", user=user):
            raise WorkflowNotAllowed, "Workflow: Not allowed (edit)"
        self.Signal("storeFile", file=file, fldname=fldname)
        self.dbEntry.CommitFile(fldname, file)
        # call wf
        try:
            self.WfAction("edit", user=user)
        except Exception, e:
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
        # check workflow
        if not self.WfAllow("edit", user=user):
            raise WorkflowNotAllowed, "Workflow: Not allowed (edit)"
        self.Signal("deleteFile", fldname=fldname)
        result = self.dbEntry.DeleteFile(fldname)
        if not result:
            return False
        # call wf
        try:
            self.WfAction("edit", user=user)
        except Exception, e:
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
        self.WfInit(user)

        # split data for pool
        self.UpdateInternal(data)
        self.meta["pool_type"] = self.configuration.id
        self.meta["pool_unitref"] = self.parent.id
        self.meta["pool_stag"] = self.selectTag

        # call wf
        try:
            self.WfAction("create", user=user)
        except Exception, e:
            self.Undo()
            raise 

        return



class ObjectWorkflow:
    """
    Provides workflow functionality for objects. 
    Workflow process objects are handled and loaded by the application. Meta layer fields `pool_wfp` stores the 
    process id and `pool_wfa` the current state.
    """

    def WfAllow(self, action, user, transition = None):
        """
        Check if action is allowed in current state in workflow. This functions returns True or False
        and unlike WFAction() will not raise a WorkflowNotAllowed Exception.
        
        Event: 
        - wfAllow(name)

        returns bool
        """
        wf = self.GetWf()
        if wf is None:
            return True
        self.Signal("wfAllow", name=action)
        return wf.Allow(action, self, user=user, transition=transition)


    def WfAction(self, action, user, transition = None):
        """
        Trigger workflow action. If several transitions are possible for the action in the current state
        the first is used. In this case the transition id can be passed as parameter.
        
        Event: 
        - wfAction(name)

        raises WorkflowNotAllowed 
        """
        wf = self.GetWf()
        if wf is None:
            return 
        wf.Action(action, self, user=user, transition=transition)
        self.Signal("wfAction", name=action)


    def WfInit(self, user):
        """
        Called after object was created
        """
        # check for workflow process to use
        wfProc = self.GetNewWf()
        if wfProc:
            self.meta["pool_wfp"] = wfProc.id
            self.Signal("wfInit", processID=wfProc.id)
            if not self.WfAllow("create", user, transition=None):
                raise WorkflowNotAllowed, "Workflow: Not allowed (create)"
            

    def GetWf(self):
        """
        Returns the workflow process for the object.

        Event: 
        - wfLoad(workflow) 
        
        returns object
        """
        app = self.app
        if not app.configuration.workflowEnabled:
            return None
        wfTag = self.meta["pool_wfp"]
        if not wfTag:
            return None
        # load workflow
        wf = app.GetWorkflow(wfTag, contextObject=self)
        # enable strict workflow checking
        if wf is None:
            raise ConfigurationError, "Workflow process not found (%s)" %(wfTag)
        self.Signal("wfLoad", workflow=wf)
        return wf


    def GetNewWf(self):
        """
        Returns the new workflow process configuration for the object based on settings:
        
        1) uses configuration.workflowID if defined
        2) query application modules for workflow 

        returns conf object
        """
        app = self.app
        if not app.configuration.workflowEnabled:
            return None
        if not self.configuration.workflowEnabled:
            return None
        wfID = self.configuration.workflowID
        if wfID:
            wf = app.GetWorkflowConf(wfID)
            return wf
        wf = app.GetAllWorkflowConfs(contextObject=self)
        if wf is None:
            return None
        if len(wf)>1:
            raise ConfigurationError, "Workflow: More than one process for type found (%s)" % (self.configuration.id)
        return wf[0]


    def GetWfInfo(self, user):
        """
        returns the current workflow state as dictionary
        """
        wf = self.GetWf()
        if wf is None:
            return {}
        return wf.GetObjInfo(self, user)


    def GetWfState(self):
        """
        """
        return self.meta.pool_wfa


    # Manual Workflow changes ---------------------------------------------------------------

    def SetWfState(self, stateID):
        """
        Sets the workflow state for the object. The new is state is set
        regardless of transitions or calling any workflow actions.
        """
        self.meta["pool_wfa"] = stateID

    
    def SetWfProcess(self, processID, user, force=False):
        """
        Sets or changes the workflow process for the object. If force is false
        either 
        
        1) no wfp must be set for the object or 
        2) the current workflow with action *change_wfprocess* is called
        
        Workflow action: change_wfprocess
        """
        app = self.app
        wf = self.meta.pool_wfp
        if not wf or force:
            self.meta["pool_wfp"] = processID
            if app.configuration.autocommit:
                self.Commit(user)
            return True
        if not self.WfAllow("change_wfprocess", user=user):
            return False
        self.WfAction("change_wfprocess",user=user)
        self.meta["pool_wfp"] = processID
        if app.configuration.autocommit:
            self.Commit(user)
        return True




