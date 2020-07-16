# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#
__doc__ = """
Application.modules stores configuration objects registered by calling `RegisterComponents()`. 
"""

import uuid
from zope.interface import providedBy

from nive.definitions import IViewModuleConf, IViewConf, IRootConf, IObjectConf, IToolConf
from nive.definitions import IAppConf, IDatabaseConf, IModuleConf, IWidgetConf, IFieldConf
from nive.definitions import ReadonlySystemFlds
from nive.definitions import ConfigurationError

from nive.utils.utils import SortConfigurationList
from nive.helper import ResolveName, ResolveConfiguration, FormatConfTestFailure
from nive.helper import DecorateViewClassWithViewModuleConf
from nive.tool import _IGlobal, _GlobalObject
from nive.workflow import IWfProcessConf


class AppConfigurationQuery(object):
    """
    Read access functions for root, type, type field, meta field and category configurations.

    Requires:
    - nive.nive
    """
    def __init__(self, app):
        self.app = app

    def QueryConf(self, queryFor, context=None):
        """
        Returns a list of configurations or empty list
        """
        if isinstance(queryFor, str):
            queryFor = ResolveName(queryFor, raiseExcp=False)
            if not queryFor:
                return ()
        if context:
            return self.app.registry.getAdapters((context,), queryFor)
        return self.app.registry.getAllUtilitiesRegisteredFor(queryFor)

    def QueryConfByName(self, queryFor, name, context=None):
        """
        Returns configuration or None
        """
        if isinstance(queryFor, str):
            queryFor = ResolveName(queryFor, raiseExcp=False)
            if not queryFor:
                return None
        if context:
            v = self.app.registry.queryAdapter(context, queryFor, name=name)
            if v:
                return v[0]
            return None
        return self.app.registry.queryUtility(queryFor, name=name)

    # Roots -------------------------------------------------------------

    def GetRootConf(self, name=""):
        """
        Get the root object configuration. If name is empty, the default name is used.

        returns dict or None
        """
        if name == "":
            name = self.app.rootname
        return self.app.registry.queryUtility(IRootConf, name=name)

    def GetAllRootConfs(self):
        """
        Get all root object configurations as list.

        returns list
        """
        return self.app.registry.getAllUtilitiesRegisteredFor(IRootConf)


    # Types -------------------------------------------------------------

    def GetObjectConf(self, typeID, skipRoot=False):
        """
        Get the type configuration for typeID. If type is not found root definitions are
        searched as well.

        returns configuration or none
        """
        c = self.app.registry.queryUtility(IObjectConf, name=typeID)
        if c or skipRoot:
            return c
        return self.GetRootConf(typeID)

    def GetAllObjectConfs(self, visibleOnly=False):
        """
        Get all type configurations.

        returns list
        """
        c = self.app.registry.getAllUtilitiesRegisteredFor(IObjectConf)
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

    def GetFld(self, fldID, typeID=None):
        """
        Get type or meta field definition. Type fields have the priority if typeID is not None.

        returns configuration or None
        """
        if typeID is not None:
            f = self.GetObjectFld(fldID, typeID)
            if f is not None:
                return f
        return self.GetMetaFld(fldID)

    def GetFldName(self, fldID, typeID=None):
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
            f = [d for d in fields if d["id"] == fldID.id]
            if f:
                return fldID
        else:
            f = [d for d in fields if d["id"] == fldID]
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
            f = [d for d in self.app.configuration.meta if d["id"] == fldID.id]
            if f:
                return fldID
        else:
            f = [d for d in self.app.configuration.meta if d["id"] == fldID]
            if f:
                return f[0]
        return None

    def GetAllMetaFlds(self, ignoreSystem=True):
        """
        Get all meta field configurations.

        returns list
        """
        if not ignoreSystem:
            return self.app.configuration.meta
        return [m for m in self.app.configuration.meta if m["id"] not in ReadonlySystemFlds]

    def GetMetaFldName(self, fldID):
        """
        Get meta field name for id.

        returns string
        """
        m = [d for d in self.app.configuration.meta if d["id"] == fldID]
        if not m:
            return ""
        return m[0]["name"]

    # Tool -------------------------------------------------------------

    def GetToolConf(self, toolID, contextObject=None):
        """
        Get the tool configuration.

        returns configuration or None
        """
        if not contextObject:
            contextObject = _GlobalObject()
        v = self.app.registry.queryAdapter(contextObject, IToolConf, name=toolID)
        if v:
            return v[0]
        return None

    def GetAllToolConfs(self, contextObject=None):
        """
        Get all tool configurations.

        returns list
        """
        tools = []
        for a in self.app.registry.registeredAdapters():
            if a.provided == IToolConf:
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
        c = [d for d in self.app.configuration.categories if d["id"] == categoryID]
        if not c:
            return None
        return c[0]

    def GetAllCategories(self, sort="name", visibleOnly=False):
        """
        Get all category configurations.

        returns list
        """
        if not visibleOnly:
            return SortConfigurationList(self.app.configuration.categories, sort)
        c = [a for a in self.app.configuration.categories if not a.get("hidden")]
        return SortConfigurationList(c, sort)

    def GetCategoryName(self, categoryID):
        """
        Get category name for id.

        returns string
        """
        c = [d for d in self.app.configuration.categories if d["id"] == categoryID]
        if not c:
            return ""
        return c[0]["name"]

    # Workflow -------------------------------------------------------------

    def GetWorkflowConf(self, processID, contextObject=None):
        """
        Get the workflow process configuration.

        returns configuration or None
        """
        v = self.app.registry.queryAdapter(contextObject or _GlobalObject(), IWfProcessConf, name=processID)
        if v:
            return v[0]
        return None

    def GetAllWorkflowConfs(self, contextObject=None):
        """
        Get all workflow configurations.

        returns list
        """
        w = []
        adpts = self.app.registry.registeredAdapters()
        for a in adpts:
            if a.provided == IWfProcessConf:
                if contextObject:
                    if not a.required[0] in providedBy(contextObject):
                        continue
                w.append(a.factory)
        return w


class Registration(object):

    def __init__(self, app):
        self.app = app
        self.log = app.log
        

    def RegisterComponents(self, module, **kw):
        """
        Include a module or configuration to store in the registry.

        Handles configuration objects with the following interfaces:

        - IAppConf
        - IRootConf
        - IObjectConf
        - IViewModuleConf
        - IViewConf 
        - IToolConf
        - IModuleConf
        - IWidgetConf
        - IWfProcessConf

        Other modules are registered as utility with **kws as parameters.

        raises TypeError, ConfigurationError, ImportError
        """
        app = self.app
        log = self.log
        iface, conf = ResolveConfiguration(module)
        if not conf:
            log.debug('Register python module: %s', str(module))
            return app.registry.registerUtility(module, **kw)

        # test conf
        if app.debug:
            r = conf.test()
            if r:
                v = FormatConfTestFailure(r)
                log.warning('Configuration test failed:\r\n%s', v)
                # return False

        log.debug('Register module: %s %s', str(conf), str(iface))
        # register module views
        if iface not in (IViewModuleConf, IViewConf):
            self._RegisterConfViews(conf)

        # reset cached class value. makes testing easier
        try:
            del conf._c_class
        except:
            pass

        # register module itself
        if hasattr(conf, "unlock"):
            conf.unlock()

        # events
        if conf.get("events"):
            for e in conf.events:
                log.debug('Register Event: %s for %s', str(e.event), str(e.callback))
                app.ListenEvent(e.event, e.callback)

        if iface == IRootConf:
            app.registry.registerUtility(conf, provided=IRootConf, name=conf.id)
            if conf.default or not app._defaultRoot:
                app._defaultRoot = conf.id
            return True
        elif iface == IObjectConf:
            app.registry.registerUtility(conf, provided=IObjectConf, name=conf.id)
            return True

        elif iface == IViewConf:
            app.registry.registerUtility(conf, provided=IViewConf, name=conf.id or str(uuid.uuid4()))
            return True
        elif iface == IViewModuleConf:
            app.registry.registerUtility(conf, provided=IViewModuleConf, name=conf.id)
            if conf.widgets:
                for w in conf.widgets:
                    self.RegisterComponents(w)
            return True

        elif iface == IToolConf:
            if conf.apply:
                for i in conf.apply:
                    if i is None:
                        app.registry.registerAdapter(conf, (_IGlobal,), IToolConf, name=conf.id)
                    else:
                        app.registry.registerAdapter(conf, (i,), IToolConf, name=conf.id)
            else:
                app.registry.registerAdapter(conf, (_IGlobal,), IToolConf, name=conf.id)
            if conf.modules:
                for m in conf.modules:
                    self.RegisterComponents(m, **kw)
            return True

        elif iface == IAppConf:
            app.registry.registerUtility(conf, provided=IAppConf, name="IApp")
            if conf.modules:
                for m in conf.modules:
                    self.RegisterComponents(m)
            return True

        elif iface == IDatabaseConf:
            app.registry.registerUtility(conf, provided=IDatabaseConf, name="IDatabase")
            app.dbConfiguration = conf
            return True

        elif iface == IModuleConf:
            # modules
            if conf.modules:
                for m in conf.modules:
                    self.RegisterComponents(m, **kw)
            app.registry.registerUtility(conf, provided=IModuleConf, name=conf.id)
            return True

        elif iface == IWidgetConf:
            for i in conf.apply:
                app.registry.registerAdapter(conf, (i,), conf.widgetType, name=conf.id)
            return True

        elif iface == IWfProcessConf:
            if conf.apply:
                for i in conf.apply:
                    app.registry.registerAdapter(conf, (i,), IWfProcessConf, name=conf.id)
            else:
                app.registry.registerAdapter(conf, (_IGlobal,), IWfProcessConf, name=conf.id)
            return True

        raise TypeError("Unknown configuration interface type (%s)" % (str(conf)))

    def RegisterViews(self, config):
        """
        Register configured views and static views with the pyramid web framework.
        """
        app = self.app
        ref = str(app.configuration.context)
        predicatename = ref+"_AppContainmentPredicate"
        config.add_view_predicate(predicatename, AppContainmentPredicate)

        views = app.registry.getAllUtilitiesRegisteredFor(IViewConf)
        # single views
        for view in views:
            opts = {predicatename: ref}
            if view.options:
                opts.update(view.options)

            config.add_view(view=view.view,
                            context=view.context,
                            attr=view.attr,
                            name=view.name,
                            renderer=view.renderer,
                            permission=view.permission,
                            containment=view.containment,
                            **opts)
        return config

    def RegisterViewModules(self, config):
        """
        Register configured views and static views with the pyramid web framework.
        """
        app = self.app
        ref = str(app.configuration.context)
        predicatename = ref+"_AppContainmentPredicate"
        config.add_view_predicate(predicatename, AppContainmentPredicate)

        mods = app.registry.getAllUtilitiesRegisteredFor(IViewModuleConf)
        for viewmod in mods:
            # decorate viewmod to add a pointer to the view module configuration. otherwise there is no way
            # to access the configuration from inside the view callable
            viewcls = viewmod.view
            if viewcls:
                viewcls = DecorateViewClassWithViewModuleConf(viewmod, viewcls)
            # object views
            for view in viewmod.views:
                opts = {predicatename: ref}
                if view.options:
                    opts.update(view.options)

                config.add_view(attr=view.attr,
                                name=view.name,
                                view=view.view or viewcls,
                                context=view.context or viewmod.context,
                                renderer=view.renderer or viewmod.renderer,
                                permission=view.permission or viewmod.permission,
                                containment=view.containment or viewmod.containment,
                                **opts)

            # static views
            maxage = 60 * 60 * 4
            if app.debug:
                maxage = None
            if isinstance(viewmod.static, (list,tuple)):
                for static in viewmod.static:
                    if isinstance(static, dict):
                        config.add_static_view(name=static["name"], path=static["path"], cache_max_age=static.get("maxage", maxage))
                    else:
                        config.add_static_view(name=static[0], path=static[1], cache_max_age=viewmod.get("maxage", maxage))

            elif isinstance(viewmod.static, dict):
                config.add_static_view(name=static["name"], path=static["path"], cache_max_age=static.get("maxage", maxage))

            elif viewmod.static:
                # bw update
                config.add_static_view(name=viewmod.staticName or viewmod.id, path=viewmod.static, cache_max_age=maxage)

            # acls
            if viewmod.get("acl"):
                app.__acl__ = tuple(list(viewmod.get("acl")) + list(app.__acl__))

        return config

    def RegisterTranslations(self, config):
        """
        Register translation directories contained in configurations.
        Translations can be specified as `configuraion.translations` for 
        IAppConf, IViewModuleConf, IObjectConf, IRootConf, IToolConf, IModuleConf, IWidgetConf
        """
        for confType in (IAppConf, IViewModuleConf, IObjectConf, IRootConf, IToolConf, IModuleConf, IWidgetConf):
            mods = self.app.registry.getAllUtilitiesRegisteredFor(confType)
            for modconf in mods:
                path = modconf.translations
                # translations
                if isinstance(path, str):
                    config.add_translation_dirs(path)
                elif isinstance(path, (list, tuple)):
                    config.add_translation_dirs(*path)

    def _RegisterConfViews(self, conf):
        """
        Register view configurations included as ``configuration.views`` in other
        configuration classes like ObjectConf, RootConf and so on.
        """
        views = None
        try:
            views = conf.views
        except:
            pass
        if not views:
            return
        for v in views:

            if isinstance(v, str):
                iface, conf = ResolveConfiguration(v)
                if not conf:
                    raise ConfigurationError(str(v))
                v = conf

            self.RegisterComponents(v)


class AppContainmentPredicate(object):
    """
    Check if context of view is this application. For multisite support.
    """
    def __init__(self, val, config):
        self.ref = val

    def __call__(self, context, request):
        return str(context.app.configuration.context) == self.ref

    def text(self):
        return self.ref+"_AppContainmentPredicate"
    phash = text

