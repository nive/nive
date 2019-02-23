# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#
__doc__ = """
Application.modules stores configuration objects registered by calling `RegisterComponents()`. 
"""

import uuid
from nive.utils.dataPool2.structure import PoolStructure

from nive.definitions import MetaTbl
from nive.definitions import IViewModuleConf, IViewConf, IRootConf, IObjectConf, IToolConf 
from nive.definitions import IAppConf, IDatabaseConf, IModuleConf, IWidgetConf, IFieldConf
from nive.definitions import ConfigurationError

from nive.helper import ResolveName, ResolveConfiguration, FormatConfTestFailure
from nive.helper import DecorateViewClassWithViewModuleConf
from nive.tool import _IGlobal, _GlobalObject
from nive.workflow import IWfProcessConf



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
        views = app.registry.getAllUtilitiesRegisteredFor(IViewConf)
        # single views
        for view in views:
            config.add_view(view=view.view,
                            context=view.context,
                            attr=view.attr,
                            name=view.name,
                            renderer=view.renderer,
                            permission=view.permission,
                            containment=view.containment,
                            custom_predicates=view.custom_predicates or (app.AppViewPredicate,),
                            **view.options)
        return config

    def RegisterViewModules(self, config):
        """
        Register configured views and static views with the pyramid web framework.
        """
        app = self.app
        mods = app.registry.getAllUtilitiesRegisteredFor(IViewModuleConf)
        for viewmod in mods:
            # decorate viewmod to add a pointer to the view module configuration. otherwise there is no way
            # to access the configuration from inside the view callable
            viewcls = viewmod.view
            if viewcls:
                viewcls = DecorateViewClassWithViewModuleConf(viewmod, viewcls)
            # object views
            for view in viewmod.views:
                # todo [3]
                #config.add_view_predicate

                config.add_view(attr=view.attr,
                                name=view.name,
                                view=view.view or viewcls,
                                context=view.context or viewmod.context,
                                renderer=view.renderer or viewmod.renderer,
                                permission=view.permission or viewmod.permission,
                                containment=view.containment or viewmod.containment,
                                custom_predicates=view.custom_predicates or viewmod.custom_predicates or (
                                app.AppViewPredicate,),
                                **view.options)

            # static views
            maxage = 60 * 60 * 4
            if app.debug:
                maxage = None
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

