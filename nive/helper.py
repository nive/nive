# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import weakref
import json
import os
from datetime import datetime
from datetime import time as datetime_time

from pyramid.path import DottedNameResolver
from pyramid.path import AssetResolver
from pyramid.path import caller_package

from pyramid.renderers import JSON

from nive.definitions import (
    IAppConf, IDatabaseConf, IFieldConf, IRootConf, IObjectConf, IViewModuleConf,
    IViewConf, IToolConf, IPortalConf, IGroupConf, IModuleConf,
    IWidgetConf, IWfProcessConf, IWfStateConf, IWfTransitionConf, IConf, IFileStorage
)
from nive.definitions import Conf
from nive.definitions import baseConf
from nive.definitions import implements, ConfigurationError
from nive import File
from nive.i18n import _



def ResolveName(name, base=None, raiseExcp=True):
    """
    Lookup python object by dotted python name.
    Wraps pyramid.DottedNameResolver.
    
    returns object or None
    """
    if not name:
        return None
    if not isinstance(name, basestring):
        return name
    if not base:
        base = caller_package()
    try:
        return DottedNameResolver(base).resolve(name)
    except:
        if not raiseExcp:
            return None
        raise

def ResolveAsset(name, base=None, raiseExcp=True):
    """
    Lookup asset path (template, json or any other file) and returns asset 
    descriptor object or None.
    """
    if not name:
        return None
    if not isinstance(name, basestring):
        return name
    if not base:
        base = caller_package()
    if name.startswith("./"):
        # use relative file system path
        name = os.getcwd()+name[1:]
    try:
        return AssetResolver(base).resolve(name)
    except:
        if not raiseExcp:
            return None
        raise

    
def ResolveConfiguration(conf, base=None):
    """
    Lookup configuration object by dotted python name. Returns interface and configuration object.
    Extends pyramid.DottedNameResolver with .json file support for configuration objects.
    
    Supports the following cases:
    
    - Path and file name to .json file. requires `type` set to one of the 
      configuration types: 
      *AppConf, FieldConf, DatabaseConf, RootConf, ObjectConf, ViewModuleConf, ViewConf, ToolConf, 
      GroupConf*
    - Dotted python name for configuration object including attribute name of configuration instance.
    - Dotted python name for object. Uses the convention to load the configuration from the 
      'configuration' attribute of the referenced object.
    - Configuration instance. Will just return it.
    
    returns Interface, configuration
    """
    # string instance
    if isinstance(conf, basestring):
        if not base:
            base = caller_package()
        # json file
        if conf.find(".json")!= -1:
            path = ResolveAsset(conf, base)
            with open(path.abspath()) as f:
                s = f.read()
            conf = json.loads(s)
        # resolve attribute name
        elif conf:
            conf = ResolveName(conf, base=base)

    # dict instance
    elif isinstance(conf, dict):
        # load by interface
        if not "type" in conf:
            raise TypeError, "Configuration type not defined"
        c = ResolveName(conf["type"], base="nive")
        del conf["type"]
        conf = c(**conf)

    # module and not configuration
    if not isinstance(conf, baseConf):
        if hasattr(conf, "configuration"):
            conf = conf.configuration
        
    # object instance
    if IAppConf.providedBy(conf): return IAppConf, conf
    if IDatabaseConf.providedBy(conf): return IDatabaseConf, conf
    if IFieldConf.providedBy(conf): return IFieldConf, conf
    if IRootConf.providedBy(conf): return IRootConf, conf
    if IObjectConf.providedBy(conf): return IObjectConf, conf
    if IViewModuleConf.providedBy(conf): return IViewModuleConf, conf
    if IViewConf.providedBy(conf): return IViewConf, conf
    if IToolConf.providedBy(conf): return IToolConf, conf
    if IPortalConf.providedBy(conf): return IPortalConf, conf
    if IGroupConf.providedBy(conf): return IGroupConf, conf
    if IModuleConf.providedBy(conf): return IModuleConf, conf
    if IWidgetConf.providedBy(conf): return IWidgetConf, conf
    if IWfProcessConf.providedBy(conf): return IWfProcessConf, conf
    if IWfStateConf.providedBy(conf): return IWfStateConf, conf
    if IWfTransitionConf.providedBy(conf): return IWfTransitionConf, conf
    if IConf.providedBy(conf): return IConf, conf
    return None, conf
    #raise TypeError, "Unknown configuration object: %s" % (str(conf))
    
    
def LoadConfiguration(conf, base=None):
    """
    same as ResolveConfiguration except only the configuration object is
    returned
    """
    if not base:
        base = caller_package()
    i,c = ResolveConfiguration(conf, base)
    return c


def FormatConfTestFailure(report, fmt="text"):
    """
    Format configuration test() failure
    
    returns string
    """
    import inspect
    v=[]
    for r in report:
        v+= u"-----------------------------------------------------------------------------------\r\n"
        v+= unicode(r[0]) + " " + r[1] + "\r\n"
        v+= u"-----------------------------------------------------------------------------------\r\n"
        for d in r[2].__dict__.items():
            a = d[1]
            if a is None:
                try:
                    a = r[2].parent.get(d[0])
                except:
                    pass
            v+= unicode(d[0])+u":  "+unicode(a)+u"\r\n"
        v+= u"\r\n"
    return "".join(v)


def ReplaceInListByID(conflist, newconf, id=None):
    new = []
    id = id or newconf.id
    for conf in conflist:
        if conf.id == id:
            new.append(newconf)
        else:
            new.append(conf)
    return new
            


class JsonDataEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return str(obj)
        elif isinstance(obj, datetime_time):
            return str(obj)
        elif IFileStorage.providedBy(obj):
            file = {}
            file["filekey"] = obj.filekey
            file["filename"] = obj.filename
            file["size"] = obj.size
            return file
        return json.JSONEncoder.default(self, obj)

class ConfEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, baseConf):
            values = {}
            for k in obj:
                values[k] = obj[k]
            return values
        elif isinstance(obj, datetime):
            return str(obj)
        elif isinstance(obj, datetime_time):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

class ConfDecoder(object):
    def decode(self, jsonstring):
        def object_hook(obj):
            if isinstance(obj, dict):
                try:
                    confclass = obj["ccc"]
                except KeyError:
                    return obj
                   
                if not confclass:
                    raise ConfigurationError, "Configuration class not found (ccc)"
                conf = ResolveName(confclass, base="nive")(**obj)
                return conf
            return obj
        return json.JSONDecoder(object_hook=object_hook).decode(jsonstring) 


def SetupJSONRenderer(pyramid_config):
    """
    Extend the default pyramid json renderer with support for datetime and file storage
    objects. Call `SetupJSONRenderer` in the main function e.g. ::

        config = Configurator(root_factory = getRoot, settings = settings)
        SetupJSONRenderer(config)
        config.include('pyramid_chameleon')

    :param pyramid_config:
    :return:
    """
    json_renderer = JSON()

    def datetimeAdapter(obj, request):
        return obj.isoformat()
    json_renderer.add_adapter(datetime, datetimeAdapter)

    def fileStorageAdapter(obj, request):
        file = {}
        file["filekey"] = obj.filekey
        file["filename"] = obj.filename
        file["size"] = obj.size
        return file
    json_renderer.add_adapter(IFileStorage, fileStorageAdapter)

    def confAdapter(obj, request):
        return DumpJSONConf(obj)
    json_renderer.add_adapter(baseConf, confAdapter)

    pyramid_config.add_renderer('json', json_renderer)


def DumpJSONConf(conf):
    # dump configuration to json
    values = {}
    for k in conf:
        v = conf[k]
        if isinstance(v, baseConf):
            values[k] = DumpJSONConf(v)
        elif isinstance(v, datetime):
            values[k] = str(v)
        else:
            values[k] = v
    return json.dumps(values)

def LoadJSONConf(jsondata, default=None):
    # jsondata must be a json string or dictionary
    # load from json
    # default: the default configuration class to be used if the json values do not
    # specify the class as `ccc`
    if isinstance(jsondata, basestring):
        try:
            jsondata = json.loads(jsondata)
        except:
            return jsondata
    if not isinstance(jsondata, dict):
        return jsondata
    for k,v in jsondata.items():
        jsondata[k] = LoadJSONConf(v, default=default)
        
    confclass = jsondata.get("ccc")
    if not confclass:
        if not default:
            raise ConfigurationError, "Configuration class not found (ccc)"
        return default(**jsondata)
    conf = ResolveName(confclass, base="nive")(**jsondata)
    return conf




def ClassFactory(configuration, reloadClass=False, raiseError=True, base=None, storeConfAsStaticClassVar=False):
    """
    Creates a python class reference from configuration. Uses configuration.context as class
    and dynamically adds classes listed as configuration.extensions as base classes.
    
    configuration requires

    - configuration.context
    - configuration.extensions [optional]
    
    If reloadClass = False the class is cached as configuration._c_class.
    
    storeConfAsStaticClassVar: experimental option. If true stores the configuration as part of the 
    class.
    
    """
    if not reloadClass:
        try:
            return configuration._c_class
        except AttributeError:
            pass
    tag = configuration.context
    if "extensions" in configuration:
        bases = configuration.extensions
    else:
        bases = None
    cls = GetClassRef(tag, reloadClass, raiseError, base)
    if not cls:
        return None
    
    def cacheCls(configuration, cls):
        # store type() class
        lock = configuration.locked
        if lock:
            configuration.unlock()
        configuration._c_class = cls
        if lock:
            configuration.lock()
    
    if not bases:
        if storeConfAsStaticClassVar:
            cls = type("_factory_"+cls.__name__, (cls,), {})
            cls.configuration = configuration
        cacheCls(configuration, cls)
        return cls

    # load extensions
    b = [cls]
    #opt
    for r in bases:
        r = GetClassRef(r, reloadClass, raiseError, base)
        if not r:
            continue
        b.insert(0,r)
    if len(b)==1:
        return cls

    # create new class with name configuration.context
    cls = type("_factory_"+cls.__name__, tuple(b), {})
    if storeConfAsStaticClassVar:
        cls.configuration = configuration
    cacheCls(configuration, cls)
    return cls


def GetClassRef(tag, reloadClass=False, raiseError=True, base=None):
    """
    Resolve class reference from python dotted string.
    """
    if isinstance(tag, basestring):
        if raiseError:
            classRef = ResolveName(tag, base=base)
        else:
            try:
                classRef = ResolveName(tag, base=base)
            except ImportError, e:
                return None
        if not classRef:
            return None
        #if reloadClass:
        #    reload(classRef)
        return classRef
    # tag is class ref
    return tag


def DecorateViewClassWithViewModuleConf(viewModuleConf, cls):
    ref = weakref.ref(viewModuleConf)
    if isinstance(cls, basestring):
        cls = ResolveName(cls)
    cls = type("_factory_"+cls.__name__, (cls,), {})
    cls.__configuration__ = ref
    return cls


# Field list items ------------------------------------------

from nive.security import GetUsers
from nive.utils.language import LanguageExtension, CountryExtension

def LoadListItems(fieldconf, app=None, obj=None, pool_type=None, force=False):
    """
    Load field list items for the given fieldconf.
    If `force` is False and fieldconf already contains list items, the existing 
    `fieldconf.listItems` are returned. Set `force=True` to reload each time this
    function is called.
        
    `obj` and `pool_type` are only used for workflow lookup.
        
    returns dict list
    """
    values = []
    if not fieldconf:
        return values

    if fieldconf.listItems and not force:
        # skip loading if list filled
        if hasattr(fieldconf.listItems, '__call__'):
            return fieldconf.listItems(fieldconf, obj or app)
        return fieldconf.listItems
    
    if not app:
        if fieldconf.settings:
            # settings dyn list
            dyn = fieldconf.settings.get("codelist")
            if dyn in ("languages", "countries"):
                # the only two lists not requiring 'app'
                if dyn == "languages":
                    return LanguageExtension().Codelist()
                else:
                    return CountryExtension().Codelist()
            
        # abort here if app is not set
        return fieldconf.listItems

    # load list items from db, application or user database
    if fieldconf.settings:
        # settings dyn list
        dyn = fieldconf.settings.get("codelist")
        if not dyn:
            pass        
        elif dyn == "users":
            return GetUsers(app)
        elif dyn == "groups":
            portal = app.portal
            if portal is None:
                portal = app
            return portal.GetGroups(sort="id", visibleOnly=True)
        elif dyn == "localgroups":
            return app.GetGroups(sort="id", visibleOnly=True)
        elif dyn == "groups+auth":
            portal = app.portal
            if portal is None:
                portal = app
            return [Conf(id=u"authenticated", name=_(u"Authenticated"), visible=True)] + portal.GetGroups(sort="id", visibleOnly=True)
        elif dyn == "types":
            return app.GetAllObjectConfs()
        elif dyn == "categories":
            return app.GetAllCategories()
        elif dyn[:5] == "type:":
            type = dyn[5:]
            return app.root().GetEntriesAsCodeList(type, "title", parameter= {}, operators = {}, sort = "title")
        elif dyn == "meta":
            return app.root().GetEntriesAsCodeList2("title", parameter= {}, operators = {}, sort = "title")
        elif dyn == "languages":
            return LanguageExtension().Codelist()
        elif dyn == "countries":
            return CountryExtension().Codelist()

    fld = fieldconf.id
    if fld == "pool_type":
        values = app.GetAllObjectConfs()

    elif fld == "pool_category":
        values = app.GetAllCategories()

    elif fld == "pool_groups":
        local = fieldconf.settings.get("local")
        loader = app
        if not local:
            portal = app.portal
            if portal:
                loader = portal
        values = loader.GetGroups(sort="id", visibleOnly=True)

    elif fld == "pool_language":
        values = app.GetLanguages()

    elif fld == "pool_wfa":
        # uses type object as param
        if obj:
            try:
                aWfp = obj.meta.get("pool_wfp")
                obj = app.GetWorkflow(aWfp)
                if obj:
                    values = obj.GetActivities()
            except:
                pass
        elif pool_type:
            aWfp = app.GetObjectConf(pool_type).get("workflowID")
            try:
                obj = app.GetWorkflow(aWfp)
                values = obj.GetActivities()
            except:
                pass
        else:
            values = []

    elif fld == "pool_wfp":
        values = app.GetAllWorkflowConfs()

    return values


# test request and response --------------------------------------

class Response(object):
    headerlist = []

class Request(object):
    POST = {}
    GET = {}
    url = ""
    username = ""
    response = Response()
    environ = {}

class Event(object):
    def __init__(self, request=None):
        self.request = request or Request()

class FakeLocalizer(object):
    def translate(self, text):
        try:
            if text.mapping:
                v = unicode(text)
                for k in text.mapping:
                    v = v.replace(u"${%s}"%k, unicode(text.mapping[k]))
                return v
        except:
            pass
        return text
