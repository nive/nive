# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
This file provides *container* functionality for :term:`objects` and :term:`roots`. The different components
are separated into classes by functionality. 

"""

from datetime import datetime

from nive.definitions import implementer
from nive.definitions import Conf, baseConf
from nive.definitions import StagContainer, StagRessource, MetaTbl
from nive.definitions import IContainer, IRoot, ICache, IObject, IConf, IObjectConf
from nive.definitions import ContainmentError, ConfigurationError, PermissionError
from nive.definitions import AllTypesAllowed
from nive.security import SetupRuntimeAcls
from nive.workflow import WorkflowNotAllowed, ObjectWorkflow, RootWorkflow
from nive.helper import ResolveName, ClassFactory, GetVirtualObj
from nive.i18n import translate

from nive.events import Events
from nive.search import Search
from nive.objects import Object


class ContainerRead(Events):
    """
    Container implementation with read access for subobjects used for objects and roots.

    Requires: ContainerFactory
    """
    defaultSort = "id"

    def obj(self, id, **kw):
        """ shortcut for GetObj """
        return self.GetObj(id, **kw)

    def __getitem__(self, id):
        o = self.GetObj(id)
        if o:
            return o
        raise KeyError(id)

    # Container functions ----------------------------------------------------

    def GetObj(self, id, **kw):
        """
        Get the subobject by id. ::

            id = object id as number
            permission = check current users permissions for the page. requires securityContext.
            securityContext = required to check the permission. the request object by default.
            **kw = load information
            returns the object or None

        Events:
        - loadObj(obj)
        """
        try:
            id = int(id)
        except:
            return None
        if not id:
            return None
        obj = self.factory.DbObj(id, **kw)
        self.Signal("loadObj", obj)
        return obj

    def GetObjs(self, parameter=None, operators=None, pool_type=None, containerOnly=False, **kw):
        """
        Search for subobjects based on parameter and operators. ::

            parameter = dict. see nive.Search
            operators = dict. see nive.Search
            kw.sort = sort objects. if None container default sort is used
            kw.batch = load subobjects as batch
            **kw = see Container.GetObj()
            returns all matching subobjects as list

        see :class:`nive.Search` for parameter/operators description

        Events
        - loadObj(obj)
        """
        if parameter is None:
            parameter = {}
        if operators is None:
            operators = {}

        if containerOnly:
            parameter["pool_stag"] = (StagContainer, StagRessource - 1)
            operators["pool_stag"] = "BETWEEN"

        parameter["pool_unitref"] = self.id
        sort = kw.get("sort", self.defaultSort)
        fields = ["id", "pool_datatbl", "pool_dataref", "pool_type"]
        root = self.root
        if kw.get("queryRestraints") != False:
            parameter, operators = root.ObjQueryRestraints(self, parameter, operators)
        objects = root.search.SelectDict(pool_type=pool_type, parameter=parameter, fields=fields, operators=operators,
                                         sort=sort)
        useBatch = kw.get("batch", True)
        if useBatch:
            ids = [c["id"] for c in objects]
            kw["meta"] = objects
            kw["sort"] = sort
            objs = self.factory.ObjBatch(ids, queryRestraint=False, **kw)
            return objs
        objs = []
        for c in objects:
            try:
                kw["pool_datatbl"] = c["pool_datatbl"]
                kw["pool_dataref"] = c["pool_dataref"]
                try:
                    obj = self.factory.DbObj(c["id"], queryRestraints=False, **kw)
                except PermissionError:
                    # ignore permission errors and continue
                    obj = None
                if obj:
                    objs.append(obj)
            except:
                pass
        self.Signal("loadObj", objs)
        return objs

    def GetObjsList(self, fields=None, parameter=None, operators=None, pool_type=None, containerOnly=False, **kw):
        """
        Search for subobjects based on parameter and operators. This function performs a sql query based on parameters and
        does not load any object. ::

            fields = list. see nive.Search
            parameter = dict. see nive.Search
            operators = dict. see nive.Search
            kw.sort = sort objects. if None container default sort is used
            kw.batch = load subobjects as batch
            returns dictionary list

        see :class:`nive.Search` for parameter/operators description
        """
        if parameter is None:
            parameter = {}
        if operators is None:
            operators = {}

        if containerOnly:
            parameter["pool_stag"] = (StagContainer, StagRessource - 1)
            operators["pool_stag"] = "BETWEEN"

        parameter["pool_unitref"] = self.id
        sort = kw.get("sort", self.defaultSort)
        if not fields:
            # lookup meta list default fields
            fields = self.app.configuration.listDefault
        root = self.root
        parameter, operators = root.ObjQueryRestraints(self, parameter, operators)
        objects = root.search.SelectDict(pool_type=pool_type, parameter=parameter, fields=fields, operators=operators,
                                         sort=sort)
        return objects

    def GetObjsBatch(self, ids, **kw):
        """
        Tries to load the objects with as few sql queries as possible. ::

            ids = list of object ids as number
            **kw = see Container.GetObj()
            returns all matching sub objects as list

        Events
        - loadObj(objs)
        """
        sort = kw.get("sort", self.defaultSort)
        fields = ["id", "pool_datatbl", "pool_dataref"]
        parameter, operators = {}, {}
        parameter["id"] = ids
        parameter["pool_unitref"] = self.id
        operators["id"] = "IN"
        root = self.root
        parameter, operators = root.ObjQueryRestraints(self, parameter, operators)
        objects = root.search.SelectDict(parameter=parameter, fields=fields, operators=operators, sort=sort)
        ids = [c["id"] for c in objects]
        kw["meta"] = objects
        objs = self.factory.ObjBatch(ids, **kw)
        self.Signal("loadObj", objs)
        return objs

    def GetSubtreeIDs(self, sort=None):
        """
        Returns the ids of all contained objects including subfolders sorted by *sort*. Default is *self.defaultSort*.

        returns list
        """
        if not sort:
            sort = self.defaultSort
        db = self.app.db
        ids = db.GetContainedIDs(sort=sort, base=self.id)
        return ids

    def IsContainer(self):
        """ """
        return IContainer.providedBy(self)



    # bw [3]

    def GetSort(self):
        return self.defaultSort

    def GetContainers(self, parameter=None, operators=None, **kw):
        if parameter is None:
            parameter = {}
        if operators is None:
            operators = {}
        parameter["pool_stag"] = (StagContainer, StagRessource - 1)
        operators["pool_stag"] = "BETWEEN"
        objs = self.GetObjs(parameter, operators, **kw)
        return objs

    def GetContainerList(self, fields=None, parameter=None, operators=None, **kw):
        if parameter is None:
            parameter = {}
        if operators is None:
            operators = {}
        parameter["pool_stag"] = (StagContainer, StagRessource - 1)
        operators["pool_stag"] = "BETWEEN"
        return self.GetObjsList(fields, parameter, operators, **kw)

    def GetContainedIDs(self, sort=None):
        return self.GetSubtreeIDs(sort)


class ContainerWrite:
    """
    Container with add and delete functionality for subobjects.

    Provides functionality to allow or disallow the creation of objects based
    on object configuration.subtypes.

    Requires: Container
    """

    def Create(self, type, data, user, **kw):
        """
        Creates a new sub object. ::
        
            type = object type id as string or object configuration
            data = dictionary containing data for the new object
            user = the currently active user
            **kw = version information
            returns the new object or None

        Keyword options:

        - nocommit: pass `nocommit=True` to skip a database commit after creation.

        Events
        
        - beforeAdd(data=data, type=type, user=user, kw) called for the container
        - create(user=user, kw) called for the new object
        - afterAdd(obj=obj, user=user, kw) called for the container after object has been committed
        
        Workflow actions
        
        - add (called in context of the container)
        - create (called in context of the new object)
        """
        app = self.app
        if not IObjectConf.providedBy(type):
            typedef = app.configurationQuery.GetObjectConf(type)
            if not typedef:
                raise ConfigurationError("Type not found (%s)" % (str(type)))
        else:
            typedef = type

        # allow subobject
        if not self.IsTypeAllowed(typedef, user):
            raise ContainmentError("Add type not allowed here (%s)" % (str(type)))

        wf = self.workflow
        if not wf.WfAllow("add", user=user):
            raise WorkflowNotAllowed("Not allowed in current workflow state (add)")

        self.Signal("beforeAdd", data=data, type=type, user=user, **kw)
        db = app.db
        try:
            dbEntry = db.CreateEntry(pool_datatbl=typedef["dbparam"], user=user, **kw)
            obj = self.factory.DbObj(dbEntry.GetID(), dbEntry = dbEntry, parentObj = self, configuration = typedef, **kw)
            if typedef.events:
                obj.SetupEventsFromConfiguration(typedef.events)
            obj.CreateSelf(data, user=user, **kw)
            wf.WfAction("add", user=user)
            obj.Signal("create", user=user, **kw)
            if not kw.get("nocommit") and app.configuration.autocommit:
                obj.CommitInternal(user=user)
        except Exception as e:
            db.Undo()
            raise 
        self.Signal("afterAdd", obj=obj, user=user, **kw)
        return obj


    def CreateWithoutEventsAndSecurity(self, typedef, data, user, **kw):
        """
        Creates a new sub object. Unlike `Create` this function does not trigger any events
        or workflow actions. Subtype configuration is not validated.
        Also commit is not called. Can be used to speed up batch creation. ::

            typedef = object type configuration
            data = dictionary containing data for the new object
            user = the currently active user
            **kw = version information
            returns the new object or None

        """
        app = self.app
        db = app.db
        dbEntry = None
        try:
            dbEntry = db.CreateEntry(pool_datatbl=typedef["dbparam"], user=user, **kw)
            obj = self.factory.DbObj(dbEntry.GetID(), dbEntry = dbEntry, parentObj = self, configuration = typedef, **kw)
            obj.UpdateInternal(data)
            obj.meta["pool_type"] = typedef.id
            obj.meta["pool_unitref"] = obj.parent.id
            obj.meta["pool_stag"] = obj.selectTag
        except Exception as e:
            db.Undo()
            raise
        return obj


    def Duplicate(self, obj, user, updateValues=None, **kw):
        """
        Duplicate the object including all data and files and store as new subobject. ::
        
            obj = the object to be duplicated
            user = the currently active user
            updateValues = dictionary containing meta, data, files
            **kw = version information
            returns new object or None
            
        Events
        
        - beforeAdd(data=data, type=type, user=user, kw) called for the container
        - duplicate(kw) called for the new object
        - afterAdd(obj=obj, user=user, kw) called for the container after obj has been committed

        Workflow action

        - add (called in context of the container)
        - create (called in context of the new object)
        """
        if updateValues is None:
            updateValues = dict()
        app = self.app
        type = obj.GetTypeID()
        # allow subobject
        if not self.IsTypeAllowed(type, user):
            raise ContainmentError("Add type not allowed here (%s)" % (str(type)))
        
        wf = ObjectWorkflow(self)
        if not wf.WfAllow("add", user=user):
            raise WorkflowNotAllowed("Workflow: Not allowed (add)")

        self.Signal("beforeAdd", data=updateValues, type=type, user=user, **kw)
        newDataEntry = None
        try:
            newDataEntry = obj.dbEntry.Duplicate()
            updateValues["pool_unitref"] = self.id
            updateValues["pool_wfa"] = ""
            data, meta, files = obj.SplitData(updateValues)
            newDataEntry.meta.update(meta)
            newDataEntry.data.update(data)
            newDataEntry.files.update(files)
            id = newDataEntry.GetID()
            typedef = obj.configuration
    
            newobj = self.factory.DbObj(id, dbEntry = newDataEntry, parentObj = self, configuration = typedef)
            newobj.CreateSelf(data, user=user)
            newobj.Signal("duplicate", **kw)
        except Exception as e:
            db = app.db
            if newDataEntry:
                try:
                    id = newDataEntry.GetID()
                    db.DeleteEntry(id)
                except:
                    pass
            db.Undo()
            raise 

        try:    
            if obj.IsContainer():
                for o in obj.GetObjs(queryRestraints=False):
                    newobj._RecursiveDuplicate(o, user, **kw)
            wf.WfAction("add", user=user)
            if app.configuration.autocommit:
                newobj.CommitInternal(user=user)
        except Exception as e:
             self._DeleteObj(newobj)
             raise 
         
        self.Signal("afterAdd", obj=newobj, user=user, **kw)
        return newobj
    
        
    def _RecursiveDuplicate(self, obj, user, **kw):
        """
        Recursively duplicate all subobjects. 
        """
        type=obj.GetTypeID()
        
        updateValues = {}
        self.Signal("beforeAdd", data=updateValues, type=type, **kw)
        newDataEntry = obj.dbEntry.Duplicate()
        updateValues["pool_unitref"] = self.id
        updateValues["pool_wfa"] = ""
        data, meta, files = obj.SplitData(updateValues)
        newDataEntry.meta.update(meta)
        newDataEntry.data.update(data)
        newDataEntry.files.update(files)
        id = newDataEntry.GetID()
        typedef = obj.configuration

        newobj = self.factory.DbObj(id, dbEntry = newDataEntry, parentObj = self, configuration = typedef)
        newobj.CreateSelf({}, user=user)
        newobj.Signal("duplicate", **kw)
        
        if obj.IsContainer():
            for o in obj.GetObjs(queryRestraints=False):
                newobj._RecursiveDuplicate(o, user, **kw)

        if self.app.configuration.autocommit:
            newobj.CommitInternal(user=user)

        self.Signal("afterAdd", obj=newobj, **kw)


    def Delete(self, id, user, obj=None, **kw):
        """
        Delete the subobject referenced by id. ::
        
            id = id of object to be deleted
            user = the currently active user
            obj = the object to be deleted. Will be loaded automatically if None
            **kw = version information
            returns True or False
        
        Events
        
        - delete(user=user) called on object to be deleted
        - afterDelete(id=id, user=user) called on container after object has been deleted

        Workflow action

        - remove (called in context of the container)
        - delete (called in context of the new object)
        """
        app = self.app
        # check if id is object
        if IObject.providedBy(id):
            obj = id
        if obj is None:
            obj = self.GetObj(id, queryRestraints=False, **kw)
            if obj is None:
                return False
        if obj.parent.id != self.id:
            raise ContainmentError("Object is not a child (%s)" % (str(id)))

        # call workflow
        wf = ObjectWorkflow(self)
        if not wf.WfAllow("remove", user=user):
            raise WorkflowNotAllowed("Workflow: Not allowed (remove)")
        if not obj.workflow.WfAllow("delete", user=user):
            raise WorkflowNotAllowed("Workflow: Not allowed (delete)")
        obj.Signal("delete", user=user)
        if hasattr(obj, "_RecursiveDelete"):
            obj._RecursiveDelete(user)

        # call workflow
        obj.workflow.WfAction("delete", user=user)
        self._DeleteObj(obj)
        if app.configuration.autocommit:
            self.db.Commit()
        wf.WfAction("remove", user=user)
        self.Signal("afterDelete", id=id, user=user)

        return True


    def DeleteInternal(self, id, user, obj=None, **kw):
        """
        Like *Delete()* but does not call any workflow action. ::
        
            id = id of object to be deleted
            user = the currently active user
            obj = the object to be deleted. Will be loaded automatically if None
            **kw = version information
            returns True or False

        Events
        
        - delete() called on object to be deleted
        - afterDelete(id=id) called on container after object has been deleted
        """
        app = self.app
        if not obj:
            obj = self.GetObj(id, queryRestraints=False, **kw)
        else:
            if not obj.parent==self:
                raise ContainmentError("Object is not a child (%s)" % (str(id)))
        obj.Signal("delete")
        if hasattr(obj, "_RecursiveDeleteInternal"):
            obj._RecursiveDeleteInternal(user)
        self._DeleteObj(obj)
        self.Signal("afterDelete", id=id)
        return 1


    def _DeleteObj(self, obj, id=0):
        """
        Deletes the object and additional data from wfdata, wflog, fulltext,
        security tables.
        """
        if obj is not None:
            id = obj.id
        obj.Close()
        if id > 0:
            self.db.DeleteEntry(id)


    def _RecursiveDelete(self, user):
        """
        Recursively deletes all subobjects
        """
        objs = self.GetObjs(queryRestraints=False)
        for o in objs:
            self.Delete(o.id, obj=o, user=user)


    def _RecursiveDeleteInternal(self, user):
        """
        Recursively deletes all subobjects
        """
        objs = self.GetObjs(queryRestraints=False)
        for o in objs:
            self.DeleteInternal(o.id, obj=o, user=user)
            
            
    def GetAllowedTypes(self, user=None, visible=1):
        """
        List types allowed to be created in this container based on
        configuration.subtypes.    ::
        
            user = the currently active user
            visible = will skip all hidden object types 
            returns list of configurations
            
        """
        subtypes = self.configuration.subtypes
        if not subtypes:
            return False
        all = self.app.configurationQuery.GetAllObjectConfs(visibleOnly=visible)
        if subtypes == AllTypesAllowed:
            return all

        # check types by interface
        allowed = []
        for conf in all:
            # create type from configuration
            type = GetVirtualObj(conf, self.app)
            if not type:
                continue
            # loop subtypes
            for iface in subtypes:
                if isinstance(iface, str):
                    iface = ResolveName(iface, raiseExcp=False)
                    if not iface:
                        continue
                try:
                # may not be interface class
                    if iface.providedBy(type):
                        allowed.append(conf)
                except:
                    pass
        return allowed


    def IsTypeAllowed(self, type, user=None):
        """
        Check if *type* is allowed to be created in this container based on
        configuration.subtypes.::
        
            type = the type to be checked
            user = the currently active user
            returns True/False
        
        *type* can be passed as
        
        - type id string
        - configuration object
        - type object instance
        """
        if type is None:
            return False
        subtypes = self.configuration.subtypes
        if subtypes == AllTypesAllowed:
            return True
        if not subtypes:
            return False

        if isinstance(type, str):
            if type in subtypes:
                return True
            # dotted python to obj configuration
            type = self.app.configurationQuery.GetObjectConf(type)
            if type is None:
                return False
            # create type from configuration
            type = GetVirtualObj(type, self.app)
            if type is None:
                return False

        if isinstance(type, baseConf):
            if type.id in subtypes:
                return True
            # create type from configuration
            type = GetVirtualObj(type, self.app)
            if type is None:
                return False

        if not IObject.providedBy(type) and not IConf.providedBy(type):
            return False
        # loop subtypes
        for iface in subtypes:
            if isinstance(iface, str):
                iface = ResolveName(iface, raiseExcp=False)
                if not iface:
                    continue
            try:
                # may not be interface class
                if iface.providedBy(type):
                    return True
            except:
                pass
        return False



@implementer(IContainer, IObject)
class Container(Object, ContainerRead, ContainerWrite):
    """
    Container implementation for objects and roots.
    """

    @property
    def factory(self):
        return ContainerFactory(self)

    @property
    def workflow(self):
        return ObjectWorkflow(self)



@implementer(IContainer, IRoot)
class Root(ContainerRead, ContainerWrite):
    """
    The root is a container for objects but does not store any data in the database itself. It
    is the entry point for object access. Roots are only handled by the application.

    Requires (Container, ContainerFactory, Event)
    """

    def __init__(self, path, app, rootDef):
        self.__name__ = str(path)
        self.__parent__ = app
        self.id = 0
        # unique root id generated from name . negative integer.
        self.idhash = abs(hash(self.__name__)) * -1
        self.path = path
        self.configuration = rootDef
        self.queryRestraints = {}, {}

        self.meta = Conf(pool_type=rootDef["id"],
                         title=translate(rootDef["name"]),
                         pool_state=1,
                         pool_filename=path,
                         pool_wfa="",
                         pool_change=datetime.now(tz=app.pytimezone),
                         pool_changedby="",
                         pool_create=datetime.now(tz=app.pytimezone),
                         pool_createdby="")
        self.data = Conf()
        self.files = Conf()

        # load security
        acl = SetupRuntimeAcls(rootDef.acl, self)
        if acl:
            # omit if empty. acls will be loaded from parent object
            self.__acl__ = acl

        self.Signal("init")

    # Properties -----------------------------------------------------------

    @property
    def root(self):
        """ this will return itself. Used for object compatibility. """
        return self

    @property
    def app(self):
        """ returns the cms application the root is used for """
        return self.__parent__

    @property
    def db(self):
        """ returns the datapool object """
        return self.app.db

    @property
    def parent(self):
        """ this will return None. Used for object compatibility. """
        return None

    @property
    def factory(self):
        return ContainerFactory(self)

    @property
    def workflow(self):
        return RootWorkflow(self)

    @property
    def search(self):
        return Search(self)

    # Object Lookup -----------------------------------------------------------

    def LookupObj(self, id, **kw):
        """
        Lookup the object referenced by id *anywhere* in the tree structure. Use obj() to
        restrain lookup to the first sublevel only. ::

            id = number
            **kw = version information

        returns the object or None
        """
        try:
            id = int(id)
        except:
            return None
        if id <= 0:
            return self
        if not id:
            return None
            # raise Exception, "NotFound"

        # proxy object
        if "proxyObj" in kw and kw["proxyObj"]:
            obj = self.factory.DbObj(id, parentObj=kw["proxyObj"], **kw)
            if not obj:
                raise ContainmentError("Proxy object not found")
            return obj

        # load tree structure
        path = self.app.db.GetParentPath(id)
        if path is None:
            return None
            # raise Exception, "NotFound"

        # check and adjust root id
        if hasattr(self, "rootID"):
            if self.rootID in path:
                path = path[path.index(self.rootID) + 1:]
        if hasattr(self.app, "rootID"):
            if self.app.rootID in path:
                path = path[path.index(self.app.rootID) + 1:]

        # reverse lookup of object tree. loads all parent objs.
        path.append(id)
        # opt
        obj = self
        for id in path:
            if id == self.id:
                continue
            obj = obj.factory.DbObj(id, **kw)
            if not obj:
                return None
                # raise Exception, "NotFound"
        return obj

    def ObjQueryRestraints(self, containerObj=None, parameter=None, operators=None):
        """
        The functions returns two dictionaries (parameter, operators) used to restraint
        object lookup in subtree. For example a restraint can be set to ignore all
        objects with meta.pool_state=0. All container get (GetObj, GetObjs, ...) functions
        use query restraints internally.

        See `nive.search` for parameter and operator usage.

        Please note: Setting the wrong values for query restraints can easily crash
        the application.

        Event:
        - loadRestraints(parameter, operators)

        returns parameter dict, operators dict
        """
        p, o = self.queryRestraints
        if parameter:
            parameter.update(p)
            if operators:
                operators.update(o)
            else:
                operators = o.copy()
        else:
            parameter = p.copy()
            operators = o.copy()
        self.Signal("loadRestraints", parameter=parameter, operators=operators)
        return parameter, operators

    # Values ------------------------------------------------------

    def GetID(self):
        """ returns 0. the root id is always zero. """
        return self.id

    def GetTypeID(self):
        """ returns the root type id from configuration """
        return self.configuration.id

    def GetTypeName(self):
        """ returns the root type name from configuration """
        return self.configuration.name

    def GetFieldConf(self, fldId):
        """
        Get the FieldConf for the field with id = fldId. Looks up data, file and meta
        fields.

        returns FieldConf or None
        """
        for f in self.configuration["data"]:
            if f["id"] == fldId:
                return f
        return self.app.configurationQuery.GetMetaFld(fldId)

    def GetTitle(self):
        """ returns the root title from configuration. """
        return self.meta.get("title", "")

    def GetPath(self):
        """ returns the url path name as string. """
        return self.__name__

    # Parents ----------------------------------------------------

    def IsRoot(self):
        """ returns always True. """
        return True

    def GetParents(self):
        """ returns empty list. Used for object compatibility. """
        return ()

    def GetParentIDs(self):
        """ returns empty list. Used for object compatibility. """
        return ()

    def GetParentTitles(self):
        """ returns empty list. Used for object compatibility. """
        return ()

    def GetParentPaths(self):
        """ returns empty list. Used for object compatibility. """
        return ()

    # tools ----------------------------------------------------

    def GetTool(self, name):
        """
        Load a tool in the roots' context. Only works for tools registered for roots or this root type. ::

            returns the tool object or None

        Event
        - loadToool(tool=toolObj)
        """
        t = self.app.GetTool(name, self)
        self.Signal("loadTool", tool=t)
        return t

    def Close(self):
        """
        Close the root and all contained objects. Currently only used in combination with caches.

        Event
        - close()
        """
        self.Signal("close")
        if ICache.providedBy(self):
            # opt
            for o in self.GetAllFromCache():
                o.Close()
        return


class ContainerFactory(object):
    """
    Container object factory. Creates objects based on type configuration.
    """

    def __init__(self, obj):
        self.obj = obj



    def DbObj(self, id, dbEntry=None, parentObj=None, configuration=None, **kw):
        """
        Loads and initializes the object. ::

            id = id of the object to be loaded
            dbEntry = the database entry. Will be loaded automatically if None
            parentObj = if a different parent than the container
            configuration = the object configuration to be loaded
            returns the object or None

        """
        obj = self.obj
        useCache = ICache.providedBy(obj)
        if useCache:
            o = obj.GetFromCache(id)
            if o:
                return o
        app = obj.app
        if not dbEntry:
            # check restraints
            qr = kw.get("queryRestraints", None)
            if qr != False:
                root = obj.root
                p, o = root.ObjQueryRestraints(obj)
                p["id"] = id
                p["pool_unitref"] = obj.id
                e = root.search.Select(parameter=p, operators=o)
                if len(e) == 0:
                    return None

            dbEntry = app.db.GetEntry(id, **kw)
            if not dbEntry:
                return None
                # raise Exception, "NotFound"

            if dbEntry.meta["pool_unitref"] != obj.id:
                raise ContainmentError("Object is not a child (%s)" % (str(id)))

        # create object for type
        if not parentObj:
            parentObj = obj
        if not configuration:
            type = dbEntry.GetMetaField("pool_type")
            if not type:
                # broken entry
                # raise ConfigurationError, "Empty type"
                return None
            configuration = app.configurationQuery.GetObjectConf(type)
            if not configuration:
                raise ConfigurationError("Type not found (%s)" % (str(type)))
        newobj = ClassFactory(configuration, app.reloadExtensions, True, base=None)
        newobj = newobj(id, dbEntry, parent=parentObj, configuration=configuration, **kw)

        # check security if context passed in keywords
        if kw.get("securityContext") is not None and kw.get("permission"):
            if not kw["securityContext"].has_permission(kw["permission"], newobj):
                raise PermissionError("Permission check failed (%s)" % (str(id)))

        if useCache:
            obj.Cache(newobj, newobj.id)
        return newobj

    def ObjBatch(self, ids, parentObj=None, **kw):
        """
        Load multiple objects at once.
        """
        if len(ids) == 0:
            return []
        obj = self.obj
        useCache = ICache.providedBy(self.obj)
        objs = []
        if useCache:
            load = []
            for id in ids:
                o = obj.GetFromCache(id)
                if o:
                    objs.append(o)
                else:
                    load.append(id)
            if len(load) == 0:
                return objs
            ids = load

        app = obj.app
        entries = app.db.GetBatch(ids, preload="all", **kw)

        # create object for type
        if not parentObj:
            parentObj = obj
        securityContext = kw.get("securityContext")
        permission = kw.get("permission")
        for dbEntry in entries:
            type = dbEntry.meta.get("pool_type")
            if not type:
                continue
            configuration = app.configurationQuery.GetObjectConf(type, skipRoot=1)
            if not configuration:
                continue
            newobj = ClassFactory(configuration, app.reloadExtensions, True, base=None)
            newobj = newobj(dbEntry.id, dbEntry, parent=parentObj, configuration=configuration, **kw)

            # check security if context passed in keywords
            if securityContext is not None and permission:
                if not securityContext.has_permission(permission, obj):
                    continue

            if useCache:
                obj.Cache(newobj, newobj.id)
            objs.append(newobj)
        return objs


    def VirtualObj(self, configuration):
        """
        This loads an object for a non existing database entry.
        """
        if configuration is None:
            raise ConfigurationError("Type not found")
        app = self.obj.app
        obj = ClassFactory(configuration, app.reloadExtensions, True, base=None)
        dbEntry = app.db.GetEntry(0, virtual=1)
        obj = obj(0, dbEntry, parent=None, configuration=configuration)
        return obj
