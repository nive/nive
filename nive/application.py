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

import logging
import pytz
import uuid

from time import time

from zope.interface.registry import Components

from nive.utils.dataPool2.structure import PoolStructure

from nive.definitions import MetaTbl
from nive.definitions import IAppConf
from nive.definitions import ConfigurationError

from nive.registration import Registration, AppConfigurationQuery
from nive.events import Events
from nive.helper import ResolveConfiguration, GetClassRef, ClassFactory
from nive.utils.utils import SortConfigurationList
from nive.tool import _IGlobal, _GlobalObject
from nive.search import Search


from nive.definitions import implementer
from nive.definitions import IApplication



@implementer(IApplication)
class Application(Events):
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
        self.uid = str(uuid.uuid4())

        self.__name__ = ""
        self.__parent__ = None
        self.__acl__ = []

        # development
        self.debug = False
        self.reloadExtensions = False

        # default root name (root.configuration.id)
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
        o = self.GetRoot(name)
        if o is not None and o.configuration.urlTraversal:
            return o
        raise KeyError(name)

    # Properties -----------------------------------------------------------

    @property
    def root(self):
        """
        Get default root object. Use `GetRoot(rootname)` if multiple roots used.

        Events:
        - loadRoot(root)
        - loadFromCache() called for the root

        returns root object
        """
        return self.factory.GetRootObj(self._defaultRoot)

    @property
    def db(self):
        """ returns datapool object    """
        return self._dbpool

    @property
    def portal(self):
        """ returns the portal """
        return self.__parent__

    @property
    def factory(self):
        """ returns the obj factory instance. """
        return AppFactory(self)

    @property
    def configurationQuery(self):
        """ returns the app configuration/registry query instance """
        return AppConfigurationQuery(self)

    @property
    def app(self):
        """ returns itself. for compatibility. """
        return self

    @property
    def search(self):
        return Search(self.root)

    @property
    def rootname(self):
        """ returns the name of the default root. """
        return self._defaultRoot

    def obj(self, id, rootname="", **kw):
        """ returns object    """
        root = self.factory.GetRootObj(rootname)
        if root is None:
            return None
        return root.obj(id, **kw)


    # Events and Setup ------------------------------------------------------------------

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
        self._dbpool = self.factory.GetDataPoolObj(cachedDbConnection)

        # test and create database fields
        if self.debug:
            self.GetTool("nive.tools.dbStructureUpdater", self).Run()
            result, report = self.TestDB()
            if result:
                self.log.info('Database test result: %s %s', str(result), report)
            else:
                self.log.error('Database test failure: (%s) %s', str(result), report)

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
        self.factory.CloseRootObj()
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

    # Content and root objects -----------------------------------------------------------

    def GetRoot(self, name=""):
        """
        Returns the data root object. If name is empty the default root is returned.

        Events:
        - loadRoot(root)
        - loadFromCache() called for the root

        returns root object
        """
        return self.factory.GetRootObj(name)

    def GetRoots(self):
        """
        Returns all root objects.

        returns list
        """
        return [self.GetRoot(r.id) for r in self.configurationQuery.GetAllRootConfs()]

    def GetRootNames(self):
        """
        Get all root object names (root.configuration.id).

        returns list
        """
        return [r["id"] for r in self.configurationQuery.GetAllRootConfs()]

    def GetTool(self, toolID, contextObject=None):
        """
        Load tool object. *toolID* must be the tool.id or dotted python name.

        returns the tool object.
        """
        return self.factory.GetToolObj(toolID, contextObject or _GlobalObject())

    def GetWorkflow(self, wfProcID, contextObject=None):
        """
        Load workflow process. *wfProcID* must be the wf.id or dotted python name.

        returns the workflow object
        """
        if not self.configuration.workflowEnabled:
            return None
        return self.factory.GetWfObj(wfProcID, contextObject or _GlobalObject())

    # Groups -------------------------------------------------------------

    def GetGroups(self, sort="name", visibleOnly=False):
        """
        Get a list of configured groups.

        returns list
        """
        configuration = self.configuration
        if not configuration.groups:
            return []
        if not visibleOnly:
            return SortConfigurationList(configuration.groups, sort)
        c = [a for a in configuration.groups if not a.get("hidden")]
        return SortConfigurationList(c, sort)

    def GetGroupName(self, groupID):
        """
        Get group name for id.

        returns string
        """
        g = [d for d in self.app.configuration.groups if d["id"] == groupID]
        if not g:
            return ""
        return g[0]["name"]

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
            #self.Query("select id from pool_meta where id =1")
            return True, "OK"

        except Exception as err:
            return False, str(err)

    def NewConnection(self):
        """
        Creates a new database connection. Works before startup and application setup.
        """
        return self.factory.GetConnection()

    def NewDBApi(self):
        """
        Creates a raw database connection (dbapi). Works before startup and application setup.
        """
        return self.factory.GetDBApi()

    def NewModule(self, queryFor, name, context=None):
        """
        Query for configuration and lookup class reference. Does not call __init__ for
        the new class.

        returns class or None
        """
        c = self.configurationQuery.QueryConfByName(queryFor, name, context=context)
        if c is None:
            return None
        return ClassFactory(c)



    # System value storage -------------------------------------------------------------

    def StoreSysValue(self, key, value):
        """
        Stores a value in `pool_sys` table. Value must be a string of any size.
        """
        db = self.db
        db.UpdateFields("pool_sys", key, {"id": key, "value":value, "ts":time()}, autoinsert=True)
        db.Commit()

    def LoadSysValue(self, key):
        """
        Loads the value stored as `key` from `pool_sys` table.
        """
        db = self.db
        sql, values = db.FmtSQLSelect(["value", "ts"], parameter={"id":key}, dataTable="pool_sys", singleTable=1)
        r = db.Query(sql, values)
        if not r:
            return None
        return r[0][0]

    def DeleteSysValue(self, key):
        """
        Deletes a single system value
        """
        db = self.db
        db.DeleteRecords("pool_sys", {"id": key})
        db.Commit()


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
        meta = app.configurationQuery.GetAllMetaFlds(ignoreSystem=False)
        m = []
        f = {}
        for fld in meta:
            f[fld.id] = fld.datatype
            if fld.datatype == "file":
                continue
            m.append(fld.id)
        structure[MetaTbl] = m
        fieldtypes[MetaTbl] = f

        types = app.configurationQuery.GetAllObjectConfs()
        for ty in types:
            t = []
            f = {}
            for fld in app.configurationQuery.GetAllObjectFlds(ty.id):
                f[fld.id] = fld.datatype
                if fld.datatype == "file":
                    continue
                t.append(fld.id)
            structure[ty.dbparam] = t
            fieldtypes[ty.dbparam] = f

        app._structure.Init(structure, fieldtypes, m, app.configuration.frontendCodepage, self.pytimezone)
        # reset cached db
        if app._dbpool is not None:
            app._dbpool.Close()
        return structure


    # bw [3] tests
    def Register(self, conf, **kw):
        iface, conf = ResolveConfiguration(conf)
        if iface == IAppConf:
            self.configuration = conf
        Registration(self).RegisterComponents(conf, **kw)


class AppFactory(object):
    """
    Internal class for dynamic object creation and caching.

    Requires:
    - Application
    """

    def __init__(self, app):
        self.app = app

    def GetDataPoolObj(self, cachedDbConnection=None):
        """
        creates the database object
        """
        app = self.app
        if not app.dbConfiguration:
            raise ConfigurationError("Database configuration empty. application.dbConfiguration is None.")
        poolTag = app.dbConfiguration.context
        if not poolTag:
            raise TypeError("Database type not set. application.dbConfiguration.context is empty. Use Sqlite or Mysql!")
        elif poolTag.lower() in ("sqlite", "sqlite3"):
            poolTag = "nive.utils.dataPool2.sqlite.sqlite3Pool.Sqlite3"
        elif poolTag.lower() == "mysql":
            poolTag = "nive.utils.dataPool2.mysql.mySqlPool.MySql"
        elif poolTag.lower() in ("postgres", "postgresql"):
            poolTag = "nive.utils.dataPool2.postgres.postgreSqlPool.PostgreSql"

        # if a database connection other than the default is configured
        if cachedDbConnection is not None:
            connObj = cachedDbConnection
        elif app.dbConfiguration.connection:
            connObj = GetClassRef(app.dbConfiguration.connection, app.reloadExtensions, True, None)
            connObj = connObj(config=app.dbConfiguration, connectNow=False)
        else:
            connObj = None

        dbObj = GetClassRef(poolTag, app.reloadExtensions, True, None)
        conn = app.dbConfiguration
        dbObj = dbObj(connection=connObj,
                      connParam=conn,  # use the default connection defined in db if connection is none
                      structure=app._structure,
                      root=conn.fileRoot,
                      useTrashcan=conn.useTrashcan,
                      dbCodePage=conn.dbCodePage,
                      timezone=app.pytimezone,
                      debug=conn.querylog[0],
                      log=conn.querylog[1])
        return dbObj

    def GetConnection(self):
        """
        Creates a new database connection. Works before startup and application setup.
        """
        app = self.app
        if app._dbpool is not None:
            try:
                return app._dbpool.usedconnection
            except AttributeError:
                pass

        cTag = app.dbConfiguration.connection
        poolTag = app.dbConfiguration.context
        if cTag:
            connObj = GetClassRef(cTag, app.reloadExtensions, True, None)
            connObj = connObj(config=app.dbConfiguration, connectNow=False)
            return connObj
        if app._dbpool is not None:
            return app._dbpool.CreateConnection(app.dbConfiguration)
        if not cTag and not poolTag:
            raise TypeError(
                "Database connection type not set. application.dbConfiguration.connection and application.dbConfiguration.context is empty. Use Sqlite or Mysql!")
        poolTag = app.dbConfiguration.context
        if not poolTag:
            raise TypeError("Database type not set. application.dbConfiguration.context is empty. Use Sqlite or Mysql!")
        elif poolTag.lower() in ("sqlite", "sqlite3"):
            poolTag = "nive.utils.dataPool2.sqlite.sqlite3Pool.Sqlite3"
        elif poolTag.lower() == "mysql":
            poolTag = "nive.utils.dataPool2.mysql.mySqlPool.MySql"
        elif poolTag.lower() in ("postgres", "postgresql"):
            poolTag = "nive.utils.dataPool2.postgres.postgreSqlPool.PostgreSql"
        dbObj = GetClassRef(poolTag, app.reloadExtensions, True, None)
        return dbObj._DefaultConnection(config=app.dbConfiguration, connectNow=False)

    def GetDBApi(self):
        """
        Creates a new and raw database connection. Works before startup and application setup.
        """
        conn = self.GetConnection()
        if conn:
            return conn.PrivateConnection()
        return None

    def GetRootObj(self, name):
        """
        creates the root object
        """
        app = self.app
        if not name:
            name = app.rootname
        useCache = app.configuration.useCache
        if isinstance(name, str):
            cachename = "_c_root" + name
            if useCache and hasattr(app, cachename) and getattr(app, cachename) is not None:
                rootObj = getattr(app, cachename)
                rootObj.Signal("loadFromCache")
                return rootObj
            rootConf = app.configurationQuery.GetRootConf(name)
        else:
            rootConf = name

        if rootConf is None:
            return None

        name = rootConf.id
        cachename = "_c_root" + name
        if useCache and hasattr(app, cachename) and getattr(app, cachename) is not None:
            rootObj = getattr(app, cachename)
            rootObj.Signal("loadFromCache")
        else:
            rootObj = ClassFactory(rootConf, app.reloadExtensions, True, base=None)
            rootObj = rootObj(name, app, rootConf)
            if rootObj and useCache:
                setattr(app, cachename, rootObj)
        app.Signal("loadRoot", rootObj)
        return rootObj

    def CloseRootObj(self, name=None):
        """
        close root objects. if name = none, all are closed.
        """
        app = self.app
        if not name:
            if app.registry is None:
                return
            n = app.GetRootNames()
        else:
            n = (name,)
        for name in n:
            cachename = "_c_root" + name
            try:
                o = getattr(app, cachename)
                o.Close()
                setattr(app, cachename, None)
            except AttributeError:
                pass

    def GetToolObj(self, name, contextObject):
        """
        creates the tool object
        """
        app = self.app
        if isinstance(name, str):
            conf = app.configurationQuery.GetToolConf(name, contextObject)
            if isinstance(conf, (list, tuple)):
                conf = conf[0]
        else:
            conf = name
        if not conf:
            iface, conf = ResolveConfiguration(name)
            if not conf:
                raise ImportError("Tool not found. Please load the tool by referencing the tool id. (%s)" % (str(name)))
        tag = conf.context
        toolObj = GetClassRef(tag, app.reloadExtensions, True, None)
        toolObj = toolObj(conf, app)
        if not _IGlobal.providedBy(contextObject):
            toolObj.__parent__ = contextObject
        return toolObj

    def GetWfObj(self, name, contextObject):
        """
        creates the root object
        """
        app = self.app
        wfConf = None
        if isinstance(name, str):
            wfConf = app.configurationQuery.GetWorkflowConf(name, contextObject)
            if isinstance(wfConf, (list, tuple)):
                wfConf = wfConf[0]
        if not wfConf:
            iface, wfConf = ResolveConfiguration(name)
            if not wfConf:
                raise ImportError(
                    "Workflow process not found. Please load the workflow by referencing the process id. (%s)" % (
                        str(name)))

        wfTag = wfConf.context
        wfObj = GetClassRef(wfTag, app.reloadExtensions, True, None)
        wfObj = wfObj(wfConf, app)
        if not _IGlobal.providedBy(contextObject):
            wfObj.__parent__ = contextObject
        return wfObj

