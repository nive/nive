# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#
__doc__ = """
This file contains the main application functionality. The application handles configuration
registration, roots and the database. Also it provides convenient functions to lookup all
different kinds of configurations. 

Application.modules stores configuration objects registered by calling `Register()`. 

See Application.Startup() for the main entry point and connected events. 

Not to be mixed up with pyramid applications or projects. It is possible to use multiple nive
applications in a single pyramid app.
"""
from nive import __version__

import logging
import uuid
import pytz

from time import time

from zope.interface.registry import Components
from zope.interface import providedBy

from nive.utils.dataPool2.structure import PoolStructure

from nive.definitions import MetaTbl, ReadonlySystemFlds
from nive.definitions import IRootConf, IObjectConf, IToolConf, IFieldConf, IAppConf
from nive.definitions import ConfigurationError

from nive.registration import Registration
from nive.events import Events
from nive.helper import ResolveName, ResolveConfiguration, GetClassRef, ClassFactory
from nive.tool import _IGlobal, _GlobalObject
from nive.workflow import IWfProcessConf
from nive.utils.utils import SortConfigurationList


from nive.definitions import implementer
from nive.definitions import IApplication



class Configuration(object):
    """
    Read access functions for root, type, type field, meta field and category configurations.

    Requires:
    - nive.nive
    """

    def QueryConf(self, queryFor, context=None):
        """
        Returns a list of configurations or empty list
        """
        if isinstance(queryFor, str):
            queryFor = ResolveName(queryFor, raiseExcp=False)
            if not queryFor:
                return ()
        if context:
            return self.registry.getAdapters((context,), queryFor)
        return self.registry.getAllUtilitiesRegisteredFor(queryFor)

    def QueryConfByName(self, queryFor, name, context=None):
        """
        Returns configuration or None
        """
        if isinstance(queryFor, str):
            queryFor = ResolveName(queryFor, raiseExcp=False)
            if not queryFor:
                return None
        if context:
            v = self.registry.queryAdapter(context, queryFor, name=name)
            if v:
                return v[0]
            return None
        return self.registry.queryUtility(queryFor, name=name)
    
    def Factory(self, queryFor, name, context=None):
        """
        Query for configuration and lookup class reference. Does not call __init__ for
        the new class.
        
        returns class or None
        """
        c = self.QueryConfByName(queryFor, name, context=context)
        if not c:
            return None
        return ClassFactory(c)


    # Roots -------------------------------------------------------------

    def GetRootConf(self, name=""):
        """
        Get the root object configuration. If name is empty, the default name is used.
        
        returns dict or None
        """
        if name == "":
            name = self._defaultRoot
        return self.registry.queryUtility(IRootConf, name=name)


    def GetAllRootConfs(self):
        """
        Get all root object configurations as list.
        
        returns list
        """
        return self.registry.getAllUtilitiesRegisteredFor(IRootConf)


    def GetRootIds(self):
        """
        Get all root object ids.
        
        returns list
        """
        return [r["id"] for r in self.GetAllRootConfs()]


    def GetDefaultRootName(self):
        """
        Returns the name of the default root.
        
        returns string
        """
        return self._defaultRoot


    # Types -------------------------------------------------------------

    def GetObjectConf(self, typeID, skipRoot=False):
        """
        Get the type configuration for typeID. If type is not found root definitions are
        searched as well.
        
        returns configuration or none
        """
        c = self.registry.queryUtility(IObjectConf, name=typeID)
        if c or skipRoot:
            return c
        return self.GetRootConf(typeID)


    def GetAllObjectConfs(self, visibleOnly = False):
        """
        Get all type configurations.
        
        returns list
        """
        c = self.registry.getAllUtilitiesRegisteredFor(IObjectConf)
        if not visibleOnly:
            return c
        return [t for t in c if t.get("hidden") != True]


    def GetTypeName(self, typeID):
        """
        Get the object type name for the id.
        
        returns string
        """
        t = self.GetObjectConf(typeID)
        if t:
            return t.name
        return ""


    # General Fields -------------------------------------------------------------

    def GetFld(self, fldID, typeID = None):
        """
        Get type or meta field definition. Type fields have the priority if typeID is not None.

        returns configuration or None
        """
        if typeID is not None:
            f = self.GetObjectFld(fldID, typeID)
            if f:
                return f
        return self.GetMetaFld(fldID)


    def GetFldName(self, fldID, typeID = None):
        """
        Get type or meta field name. Type fields have the priority if typeID is not None.
        
        returns string
        """
        if typeID:
            f = self.GetObjectFld(fldID, typeID)
            if f:
                return f["name"]
        return self.GetMetaFldName(fldID)


    # Type Data Fields -------------------------------------------------------------

    def GetObjectFld(self, fldID, typeID):
        """
        Returns object field configuration.
        
        returns configuration or None
        """
        fields = self.GetAllObjectFlds(typeID)
        if not fields:
            return None
        if IFieldConf.providedBy(fldID):
            f = [d for d in fields if d["id"]==fldID.id]
            if f:
                return fldID
        else:
            f = [d for d in fields if d["id"]==fldID]
            if f:
                return f[0]
        return None


    def GetAllObjectFlds(self, typeID):
        """
        Get all object field configurations.
        
        returns list or None
        """
        t = self.GetObjectConf(typeID)
        if not t:
            return None
        return t.data


    # Meta Fields -------------------------------------------------------------

    def GetMetaFld(self, fldID):
        """
        Get meta field configuration
        
        returns configuration or None
        """
        if IFieldConf.providedBy(fldID):
            f = [d for d in self.configuration.meta if d["id"]==fldID.id]
            if f:
                return fldID
        else:
            f = [d for d in self.configuration.meta if d["id"]==fldID]
            if f:
                return f[0]
        return None


    def GetAllMetaFlds(self, ignoreSystem=True):
        """
        Get all meta field configurations.
        
        returns list
        """
        if not ignoreSystem:
            return self.configuration.meta
        return [m for m in self.configuration.meta if m["id"] not in ReadonlySystemFlds]


    def GetMetaFldName(self, fldID):
        """
        Get meta field name for id.
        
        returns string
        """
        m = [d for d in self.configuration.meta if d["id"]==fldID]
        if not m:
            return u""
        return m[0]["name"]


    # Tool -------------------------------------------------------------

    def GetToolConf(self, toolID, contextObject=None):
        """
        Get the tool configuration.
        
        returns configuration or None
        """
        if not contextObject:
            contextObject = _GlobalObject()
        v = self.registry.queryAdapter(contextObject, IToolConf, name=toolID)
        if v:
            return v[0]
        return None

    def GetAllToolConfs(self, contextObject=None):
        """
        Get all tool configurations.
        
        returns list
        """
        tools = []
        for a in self.registry.registeredAdapters():
            if a.provided==IToolConf:
                if contextObject:
                    if not a.required[0] in providedBy(contextObject):
                        continue
                tools.append(a.factory)
        return tools


    # Categories -------------------------------------------------------------------------------------------------------

    def GetCategory(self, categoryID=""):
        """
        Get category configuration.
        
        returns configuration or None
        """
        c = [d for d in self.configuration.categories if d["id"]==categoryID]
        if not c:
            return None
        return c[0]


    def GetAllCategories(self, sort=u"name", visibleOnly=False):
        """
        Get all category configurations.
        
        returns list
        """
        if not visibleOnly:
            return SortConfigurationList(self.configuration.categories, sort)
        c = [a for a in self.configuration.categories if not a.get("hidden")]
        return SortConfigurationList(c, sort)


    def GetCategoryName(self, categoryID):
        """
        Get category name for id.
        
        returns string
        """
        c = [d for d in self.configuration.categories if d["id"]==categoryID]
        if not c:
            return u""
        return c[0]["name"]


    # Groups -------------------------------------------------------------

    def GetGroups(self, sort=u"name", visibleOnly=False):
        """
        Get a list of configured groups.
        
        returns list
        """
        if not self.configuration.groups:
            return []
        if not visibleOnly:
            return SortConfigurationList(self.configuration.groups, sort)
        c = [a for a in self.configuration.groups if not a.get("hidden")]
        return SortConfigurationList(c, sort)


    def GetGroupName(self, groupID):
        """
        Get group name for id.
        
        returns string
        """
        g = [d for d in self.configuration.groups if d["id"]==groupID]
        if not g:
            return u""
        return g[0]["name"]


    # Workflow -------------------------------------------------------------

    def GetWorkflowConf(self, processID, contextObject=None):
        """
        Get the workflow process configuration.
        
        returns configuration or None
        """
        v = self.registry.queryAdapter(contextObject or _GlobalObject(), IWfProcessConf, name=processID)
        if v:
            return v[0]
        return None


    def GetAllWorkflowConfs(self, contextObject=None):
        """
        Get all workflow configurations.
        
        returns list
        """
        w = []
        adpts = self.registry.registeredAdapters()
        for a in adpts:
            if a.provided==IWfProcessConf:
                if contextObject:
                    if not a.required[0] in providedBy(contextObject):
                        continue
                w.append(a.factory)
        return w




class AppFactory(object):
    """
    Internal class for dynamic object creation and caching.

    Requires:
    - Application
    """

    def _GetDataPoolObj(self, cachedDbConnection=None):
        """
        creates the database object
        """
        if not self.dbConfiguration:
            raise ConfigurationError("Database configuration empty. application.dbConfiguration is None.")
        poolTag = self.dbConfiguration.context
        if not poolTag:
            raise TypeError("Database type not set. application.dbConfiguration.context is empty. Use Sqlite or Mysql!")
        elif poolTag.lower() in ("sqlite","sqlite3"):
            poolTag = "nive.utils.dataPool2.sqlite.sqlite3Pool.Sqlite3"
        elif poolTag.lower() == "mysql":
            poolTag = "nive.utils.dataPool2.mysql.mySqlPool.MySql"
        elif poolTag.lower() in ("postgres","postgresql"):
            poolTag = "nive.utils.dataPool2.postgres.postgreSqlPool.PostgreSql"

        # if a database connection other than the default is configured
        if cachedDbConnection is not None:
            connObj = cachedDbConnection
        elif self.dbConfiguration.connection:
            connObj = GetClassRef(self.dbConfiguration.connection, self.reloadExtensions, True, None)
            connObj = connObj(config=self.dbConfiguration, connectNow=False)
        else:
            connObj = None

        dbObj = GetClassRef(poolTag, self.reloadExtensions, True, None)
        conn = self.dbConfiguration
        dbObj = dbObj(connection=connObj,
                      connParam=conn,      # use the default connection defined in db if connection is none
                      structure=self._structure, 
                      root=conn.fileRoot, 
                      useTrashcan=conn.useTrashcan, 
                      dbCodePage=conn.dbCodePage,
                      timezone=self.pytimezone,
                      debug=conn.querylog[0],
                      log=conn.querylog[1])
        return dbObj

    
    def _GetConnection(self):
        """
        Creates a new database connection. Works before startup and application setup.
        """
        if self._dbpool:
            try:
                return self._dbpool.usedconnection
            except:
                pass
                
        cTag = self.dbConfiguration.connection
        poolTag = self.dbConfiguration.context
        if cTag:
            connObj = GetClassRef(cTag, self.reloadExtensions, True, None)
            connObj = connObj(config=self.dbConfiguration, connectNow=False)
            return connObj
        if self._dbpool:
            return self._dbpool.CreateConnection(self.dbConfiguration)
        if not cTag and not poolTag:
            raise TypeError("Database connection type not set. application.dbConfiguration.connection and application.dbConfiguration.context is empty. Use Sqlite or Mysql!")
        poolTag = self.dbConfiguration.context
        if not poolTag:
            raise TypeError("Database type not set. application.dbConfiguration.context is empty. Use Sqlite or Mysql!")
        elif poolTag.lower() in ("sqlite","sqlite3"):
            poolTag = "nive.utils.dataPool2.sqlite.sqlite3Pool.Sqlite3"
        elif poolTag.lower() == "mysql":
            poolTag = "nive.utils.dataPool2.mysql.mySqlPool.MySql"
        elif poolTag.lower() in ("postgres","postgresql"):
            poolTag = "nive.utils.dataPool2.postgres.postgreSqlPool.PostgreSql"
        dbObj = GetClassRef(poolTag, self.reloadExtensions, True, None)
        return dbObj._DefaultConnection(config=self.dbConfiguration, connectNow=False)


    def _GetDBApi(self):
        """
        Creates a new and raw database connection. Works before startup and application setup.
        """
        conn = self._GetConnection()
        if conn:
            return conn.PrivateConnection()
        return None


    def _GetRootObj(self, name):
        """
        creates the root object
        """
        if not name:
            name = self.GetDefaultRootName()
        useCache = self.configuration.useCache
        if isinstance(name, str):
            cachename = "_c_root"+name
            if useCache and hasattr(self, cachename) and getattr(self, cachename):
                rootObj = getattr(self, cachename)
                rootObj.Signal("loadFromCache")
                return rootObj
            rootConf = self.GetRootConf(name)
        else:
            rootConf = name

        if not rootConf:
            return None

        name = rootConf.id
        cachename = "_c_root"+name
        if useCache and hasattr(self, cachename) and getattr(self, cachename):
            rootObj = getattr(self, cachename)
            rootObj.Signal("loadFromCache")
        else:
            rootObj = ClassFactory(rootConf, self.reloadExtensions, True, base=None)
            rootObj = rootObj(name, self, rootConf)
            if rootObj and useCache:
                setattr(self, cachename, rootObj)
        self.Signal("loadRoot", rootObj)
        return rootObj


    def _CloseRootObj(self, name=None):
        """
        close root objects. if name = none, all are closed.
        """
        if not name:
            if self.registry is None:
                return
            n = self.GetRootIds()
        else:
            n = (name,)
        for name in n:
            cachename = "_c_root"+name
            try:
                o = getattr(self, cachename)
                o.Close()
                setattr(self, cachename, None)
            except:
                pass


    def _GetToolObj(self, name, contextObject):
        """
        creates the tool object
        """
        if isinstance(name, str):
            conf = self.GetToolConf(name, contextObject)
            if isinstance(conf, (list, tuple)):
                conf = conf[0]
        else:
            conf = name
        if not conf:
            iface, conf = ResolveConfiguration(name)
            if not conf:
                raise ImportError("Tool not found. Please load the tool by referencing the tool id. (%s)" % (str(name)))
        tag = conf.context
        toolObj = GetClassRef(tag, self.reloadExtensions, True, None)
        toolObj = toolObj(conf, self)
        if not _IGlobal.providedBy(contextObject):
            toolObj.__parent__ = contextObject
        return toolObj


    def _GetWfObj(self, name, contextObject):
        """
        creates the root object
        """
        wfConf = None
        if isinstance(name, str):
            wfConf = self.GetWorkflowConf(name, contextObject)
            if isinstance(wfConf, (list, tuple)):
                wfConf = wfConf[0]
        if not wfConf:
            iface, wfConf = ResolveConfiguration(name)
            if not wfConf:
                raise ImportError("Workflow process not found. Please load the workflow by referencing the process id. (%s)" % (str(name)))

        wfTag = wfConf.context
        wfObj = GetClassRef(wfTag, self.reloadExtensions, True, None)
        wfObj = wfObj(wfConf, self)
        if not _IGlobal.providedBy(contextObject):
            wfObj.__parent__ = contextObject
        return wfObj


@implementer(IApplication)
class Application(AppFactory, Configuration, Events):
    """
    nive Application implementaion.

    SQLite example:
    ::

        appConf = AppConf(id="website",
                          title="nive app")
        dbConf = DatabaseConf(context="Sqlite3",
                              fileRoot="data",
                              dbName="data/ewp.db")
        appConf.modules.append(dbConf)

    MySql example:
    ::

        appConf = AppConf(id="website",
                          title="nive app")
        dbConf = DatabaseConf(context="MySql",
                              fileRoot="data",
                              dbName="nive",
                              host="localhost",
                              user="user",
                              password="password")
        appConf.modules.append(dbConf)

    Requires (Configuration, AppFactory, Events.Events)

    The startup process is handled by nive.portal.portal on application startup.
    During startup the system fires four events in the following order:

    - startup(app)
    - startRegistration(app, pyramidConfig)
    - finishRegistration(app, pyramidConfig)
    - run(app)

    All acl definitions are mapped to self.__acl__.

    ViewModuleConf.acl values are added first, AppConf.acl are appended to the end of the list.
    This might make it hard to replace single permissions defined by view modules because pyramid
    uses the first matching definition in the list.

    To disable any view module acl definitions or replace single permissions use the `FinishRegistration`
    event and post process acls as needed.
    """

    def __init__(self, configuration=None):
        """
        Use configuration and dbConfiguration objects to setup your application.

        Events:
        - init(configuration)
        """
        self.registry = Components()
        self.configuration = configuration
        self.dbConfiguration = None
        self.pytimezone = None
        # set id for logging
        if configuration:
            self.id = configuration.id
        else:
            self.id = __name__

        self.__name__ = u""
        self.__parent__ = None
        self.__acl__ = []

        # development
        self.debug = False
        self.reloadExtensions = False

        # v0.9.12: moved _meta to configuration.meta
        # meta fields are now handled by the application configuration
        # self._meta = copy.deepcopy(SystemFlds)

        # default root name if multiple
        self._defaultRoot = ""
        # cache database structure
        self._structure = PoolStructure()
        self._dbpool = None

        self.log = logging.getLogger(self.id)
        self.log.debug("Initialize %s", repr(configuration))
        self.Signal("init", configuration=configuration)

        self.starttime = 0

    def __del__(self):
        self.Close()

    def __getitem__(self, name):
        """
        This function is called by url traversal and looks up root objects for the corresponding
        name.
        """
        name = name.split(".")[0]
        o = self.root(name)
        if o and o.configuration.urlTraversal:
            return o
        raise KeyError(name)

    def Startup(self, pyramidConfig, debug=False, cachedDbConnection=None):
        self.Setup(debug=debug)
        self.StartRegistration(pyramidConfig)
        self.FinishRegistration(pyramidConfig, cachedDbConnection=cachedDbConnection)
        self.Run()

    def Setup(self, debug=False):
        """
        Called by nive.portal.portal on application startup.
        Sets up the registry.

        Events:

        - startup(app)
        """
        self.starttime = time()
        self.log.debug("Startup with debug=%s", str(debug))
        self.debug = debug
        self.Signal("startup", app=self)
        self.SetupApplication()

    def SetupApplication(self):
        """
        Loads self.configuration, includes modules and updates meta fields.
        """
        if not self.configuration:
            raise ConfigurationError("Configuration is empty")
        c = self.configuration
        # special values
        if c.get("id") and not self.__name__:
            self.__name__ = c.id
        if c.get("acl"):
            self.__acl__ = tuple(c.acl)
        if c.get("dbConfiguration"):
            self.dbConfiguration = c.dbConfiguration
        tz = self.configuration.get("timezone")
        if tz is not None:
            self.pytimezone = pytz.timezone(tz)

    def StartRegistration(self, pyramidConfig):
        """
        Processes all registered components and commits view definitions to
        the pyramid application configuration.

        Events:

        - startRegistration(app, pyramidConfig)
        """
        # register modules `configuration.modules`
        reg = Registration(self)
        reg.RegisterComponents(self.configuration)
        # signal before committing views
        self.Signal("startRegistration", app=self, pyramidConfig=pyramidConfig)
        # register pyramid views and translations
        if pyramidConfig:
            reg.RegisterViewModules(pyramidConfig)
            pyramidConfig.commit()
            reg.RegisterViews(pyramidConfig)
            pyramidConfig.commit()
            reg.RegisterTranslations(pyramidConfig)
            pyramidConfig.commit()

        # register groups
        portal = self.portal
        if portal and hasattr(portal, "RegisterGroups"):
            portal.RegisterGroups(self)

    def FinishRegistration(self, pyramidConfig, cachedDbConnection=None):
        """
        Finishes the registration process and cashes the database structure.
        Configurations will have a write lock after the registration is finished.

        `cachedDbConnection` is a nive.utils.dataPool2.connection instance to
        avoid reconnects on application startup. The connection can be accessed
        during runtime through ``self.db.usedconnection``.

        Events:

        - finishRegistration(app, pyramidConfig)
        """
        self.Signal("finishRegistration", app=self, pyramidConfig=pyramidConfig)
        self.log.debug('Finished registration.')

        # reload database structure
        self._LoadStructure(forceReload=True)
        self._dbpool = self._GetDataPoolObj(cachedDbConnection)

        # test and create database fields
        if self.debug:
            self.GetTool("nive.tools.dbStructureUpdater", self).Run()
            result, report = self.TestDB()
            if result:
                self.log.info('Database test result: %s %s', str(result), report)
            else:
                self.log.error('Database test result: %s %s', str(result), report)

        self._Lock()

    def Run(self):
        """
        Signals the application is up and running.

        Events:

        - run(app)
        """
        # start
        self.Signal("run", app=self)
        self.log.info('Application %s running. Startup time: %.05f.', self.__class__.__name__, time() - self.starttime)
        self.id = self.configuration.id
        self.log = logging.getLogger(self.id)

    def Close(self):
        """
        Close database and roots.

        Events:

        - close()
        """
        self.Signal("close")
        self._CloseRootObj()
        if self._dbpool:
            self._dbpool.Close()

    def Shutdown(self):
        """
        Free registry and cached database structure.
        """
        self.registry = None
        self._structure = None
        self.configuration = None
        self.dbConfiguration = None
        self.__parent__ = None

    # Properties -----------------------------------------------------------

    def root(self, name=""):
        """
        Events:
        - loadRoot(root)
        - loadFromCache() called for the root

        returns root object
        """
        return self._GetRootObj(name)

    def obj(self, id, rootname="", **kw):
        """ returns object    """
        root = self._GetRootObj(rootname)
        if not root:
            return None
        return root.obj(id, **kw)

    @property
    def db(self):
        """ returns datapool object    """
        return self._dbpool

    @property
    def portal(self):
        """ returns the portal    """
        return self.__parent__

    @property
    def app(self):
        """ returns itself. for compatibility.    """
        return self

    # Content and root objects -----------------------------------------------------------

    def GetRoot(self, name=""):
        """
        Returns the data root object. If name is empty the default root is returned.

        Events:
        - loadRoot(root)
        - loadFromCache() called for the root

        returns root object
        """
        return self._GetRootObj(name)

    def GetRoots(self):
        """
        Returns all root objects.

        returns list
        """
        return [self.GetRoot(r.id) for r in self.GetAllRootConfs()]

    def GetTool(self, toolID, contextObject=None):
        """
        Load tool object. *toolID* must be the tool.id or dotted python name.

        returns the tool object.
        """
        return self._GetToolObj(toolID, contextObject or _GlobalObject())

    def GetWorkflow(self, wfProcID, contextObject=None):
        """
        Load workflow process. *wfProcID* must be the wf.id or dotted python name.

        returns the workflow object
        """
        if not self.configuration.workflowEnabled:
            return None
        return self._GetWfObj(wfProcID, contextObject or _GlobalObject())

    # Data Pool and database connections -------------------------------------------------------------------

    def GetDB(self):
        """
        Create data pool object and database connection.

        returns the datapool object
        """
        return self._dbpool

    def Query(self, sql, values=()):
        """
        Start a sql query on the database.

        returns tuple or none
        """
        db = self.db
        r = db.Query(sql, values)
        return r

    def TestDB(self):
        """
        Test database connection for errors. Returns state and error message.

        returns bool, message
        """
        try:
            db = self.db
            if not db.connection.IsConnected():
                db.connection.connect()
                if not db.connection.IsConnected():
                    return False, "No connection"
            self.Query("select id from pool_meta where id =1")
            return True, "OK"

        except Exception as err:
            return False, str(err)

    def NewConnection(self):
        """
        Creates a new database connection. Works before startup and application setup.
        """
        return self._GetConnection()

    def NewDBApi(self):
        """
        Creates a raw database connection (dbapi). Works before startup and application setup.
        """
        return self._GetDBApi()


    # System value storage -------------------------------------------------------------

    def StoreSysValue(self, key, value):
        """
        Stores a value in `pool_sys` table. Value must be a string of any size.
        """
        db = self.db
        db.UpdateFields(u"pool_sys", key, {u"id": key, u"value":value, u"ts":time()}, autoinsert=True)
        db.Commit()

    def LoadSysValue(self, key):
        """
        Loads the value stored as `key` from `pool_sys` table.
        """
        db = self.db
        sql, values = db.FmtSQLSelect([u"value", u"ts"], parameter={"id":key}, dataTable=u"pool_sys", singleTable=1)
        r = db.Query(sql, values)
        if not r:
            return None
        return r[0][0]

    def DeleteSysValue(self, key):
        """
        Deletes a single system value
        """
        db = self.db
        db.DeleteRecords(u"pool_sys", {u"id": key})
        db.Commit()


    def AppViewPredicate(self, context, request):
        """
        Check if context of view is this application. For multisite support.
        """
        app = context.app
        return app == self

    AppViewPredicate.__text__ = "nive.AppViewPredicate"


    def _Lock(self):
        # lock all configurations
        # adapters
        for a in self.app.registry.registeredAdapters():
            try:
                a.factory.lock()
            except:
                pass
        for a in self.app.registry.registeredUtilities():
            try:
                a.component.lock()
            except:
                pass


    def _LoadStructure(self, forceReload=False):
        """
        returns dictionary containing database tables and columns
        """
        app = self.app
        if forceReload:
            app._structure = PoolStructure()
        if not app._structure.IsEmpty():
            return app._structure

        structure = {}
        fieldtypes = {}
        meta = app.GetAllMetaFlds(ignoreSystem=False)
        m = []
        f = {}
        for fld in meta:
            f[fld.id] = fld.datatype
            if fld.datatype == "file":
                continue
            m.append(fld.id)
        structure[MetaTbl] = m
        fieldtypes[MetaTbl] = f

        types = app.GetAllObjectConfs()
        for ty in types:
            t = []
            f = {}
            for fld in app.GetAllObjectFlds(ty.id):
                f[fld.id] = fld.datatype
                if fld.datatype == "file":
                    continue
                t.append(fld.id)
            structure[ty.dbparam] = t
            fieldtypes[ty.dbparam] = f

        app._structure.Init(structure, fieldtypes, m, app.configuration.frontendCodepage)
        # reset cached db
        if app._dbpool is not None:
            app._dbpool.Close()
        return structure


    # bw tests
    def Register(self, conf, **kw):
        iface, conf = ResolveConfiguration(conf)
        if iface == IAppConf:
            self.configuration = conf
        Registration(self).RegisterComponents(conf, **kw)

