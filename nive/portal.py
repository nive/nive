# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
The *portal* manages applications and is the pyramid_ or wsgi_ root. There is only one
portal in each instance.

The portal handles the cms applications and global components like the user database. 
Applications have to be registered by calling ``Register(application)`` on initialization.

- Routes url names to applications
- Calls ``Startup()`` for each registered application on server startup
- Provides connection start and finish events
- Collects all registered security groups from applications 

Allows by default all permissions for admins ::

    __acl__ = (Allow, "group:admin", ALL_PERMISSIONS)

Also redirects for login, forbidden, logout and default url are configured here ::

        portalDefaultUrl = "/website/"
        loginUrl = "/userdb/udb/login"
        loginSuccessUrl = "/website/"
        forbiddenUrl = "/userdb/udb/login"
        logoutUrl = "/userdb/udb/logout"
        logoutSuccessUrl = "/website/"
        accountUrl = "/userdb/udb/update"

Interface: IPortal
"""

import copy
import time
import logging
import ConfigParser

from nive.definitions import PortalConf, Conf, baseConf
from nive.definitions import implements
from nive.definitions import ConfigurationError
from nive.definitions import IModuleConf, IAppConf
from nive.definitions import IPortal, IApplication
from nive.helper import ResolveConfiguration, ResolveName
from nive.helper import ClassFactory
from nive.security import User, authenticated_userid, Allow, ALL_PERMISSIONS
from nive.events import Events
from nive.utils.utils import SortConfigurationList



class Portal(Events):
    """ """
    implements(IPortal)

    __name__ = u""
    __parent__ = None
    host = None
    port = None
    
    def __init__(self, configuration = None):
        """
        Events:
        - init(configuration)
        """
        self.components = []
        self.groups = []
        self.__acl__ = [(Allow, "group:admin", ALL_PERMISSIONS)]
        
        self.configuration = configuration or PortalConf()
        if self.configuration.groups:
            self.groups = self.configuration.groups
        
        self.Signal("init", configuration=self.configuration)

    def __del__(self):
        self.Close()
        
    def __getitem__(self, name):
        """
        Called by traversal machinery
        
        event: getitem(obj) called with the traversed object
        """
        try:
            if not name in self.components:
                raise KeyError, name
            obj = getattr(self, name)
            self.Signal("getitem", obj=obj)
            return obj
        except AttributeError:
            raise KeyError, name
        
    def Register(self, comp, name=None):
        """
        Register an application or component. This is usually done in the pyramid
        app file. The registered component is automatically loaded and set up to work
        with url traversal.
        
        *comp* can be one of the following cases

        - AppConf object
        - AppConf string as python dotted name
        - python object. Requires *name* parameter or *comp.id* attribute
        
        *name* is used as the url path name to lookup the component.

        """
        log = logging.getLogger("portal")
        iface, conf = ResolveConfiguration(comp)
        if not conf and isinstance(comp, basestring):
            raise ConfigurationError, "Portal registration failure. No name given (%s)" % (str(comp))
        if isinstance(comp, basestring) or isinstance(comp, baseConf):
            # factory methods
            if IAppConf.providedBy(conf):
                comp = ClassFactory(conf)(conf)
            elif IModuleConf.providedBy(conf):
                comp = ClassFactory(conf)(conf)
            elif iface and iface.providedBy(comp):
                comp = ResolveName(conf.context)(conf)
            elif isinstance(comp, basestring):
                comp = ResolveName(conf.context)(conf)

        try:
            name = name or conf.id
        except AttributeError:
            pass
        if not name:
            raise ConfigurationError, "Portal registration failure. No name given (%s)" % (str(comp))

        log.debug("Portal.Register: %s %s", name, repr(conf))
        self.__dict__[name] = comp
        comp.__parent__ = self
        comp.__name__ = name
        self.components.append(name)


    def Startup(self, pyramidConfig, debug=False, **kw):
        """
        *Startup* is called once by the *main* function of the pyramid wsgi app on 
        server startup. All configuration, registration and setup is handled during
        the startup call. 
        
        Calls *Setup()*, *StartRegistration()*, *FinishRegistration()*, *Run()* for each 
        registered application.
        
        *pyramidConfig* is the pyramid registration configuration object for views and other 
        system components. 
        
        *debug* signals whether running in debug mode or not.

        Event:
        - run(event, app=self)
        """
        log = logging.getLogger("portal")
        log.debug("Startup with debug=%s for config %s", str(debug), str(pyramidConfig))
        
        # extract host and port from global config if set
        if "global_config" in kw:
            # get host and port from default pyramid ini file
            ini=ConfigParser.ConfigParser()
            try:
                ini.read(kw["global_config"]["__file__"])
                self.host = ini.get("server:main","host")
                self.port = int(ini.get("server:main","port"))
            except (KeyError, ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                pass

        if pyramidConfig:
            self.SetupPortalViews(pyramidConfig)
            #pyramidConfig.add_subscriber(self.StartConnection, iface=NewRequest)
        
        # Setup
        for c in self.components:
            component = getattr(self, c)
            if IApplication.providedBy(component):
                component.Setup(debug)
        # StartRegistration
        for c in self.components:
            component = getattr(self, c)
            if IApplication.providedBy(component):
                component.StartRegistration(pyramidConfig)
        # FinishRegistration
        for c in self.components:
            component = getattr(self, c)
            if IApplication.providedBy(component):
                component.FinishRegistration(pyramidConfig)
        # Run
        for c in self.components:
            component = getattr(self, c)
            if IApplication.providedBy(component):
                component.Run()
        self.Signal("run", app=self)


    def GetApps(self, interface=None):
        """
        Returns registered components and apps as list.
        """
        if isinstance(interface, basestring):
            interface = ResolveName(interface)
        apps=[]
        for name in self.components:
            a = getattr(self, name)
            if interface:
                if not interface.providedBy(a):
                    continue
            apps.append(a)
        return apps


    def StartConnection(self, event):
        """
        Called by pyramid for each new connection with event as parameter. The
        current request stored as *event.request*. Stores the authenticated user 
        *event.request.environ["REMOTE_USER"]*.
        
        Event:
        - start(event)
        """
        uid = authenticated_userid(event.request)
        event.request.environ["REMOTE_USER"] = uid
        event.request.environ["START_TIME"] = time.time()
        self.Signal("start", event=event)
        #event.request.add_finished_callback(self.FinishConnection)


    def FinishConnection(self, request):
        """
        Called by pyramid on termination for each connection with request as parameter.

        Event:
        - finish(request)
        """
        self.Signal("finish", request)
        

    def GetGroups(self, sort=u"id", visibleOnly=False):
        """
        returns all groups registered by components as list
        """
        if not visibleOnly:
            return SortConfigurationList(self.groups, sort)
        c = filter(lambda a: not a.get("hidden"), self.groups)
        return SortConfigurationList(c, sort)


    @property
    def portal(self):
        return self
    

    def RegisterGroups(self, component):
        """
        Callback to collect groups from all registered component. `RegisterGroups` is called at the
        end of `StartRegistration` by each component.
        """
        try:
            gr = component.configuration.groups
        except AttributeError:
            return
        for g in gr:
            add = 1
            for g2 in self.groups:
                if g["id"] == g2["id"]:
                    add = 0
                    break
            if add:
                self.groups.append(g)


    def SetupPortalViews(self, config):
        # redirects
        #config.add_view(error_view, context=HTTPError)
        config.add_view(forbidden_view, context=Forbidden)
        config.add_view(portal_view, name="", context="nive.portal.Portal")
        config.add_view(robots_view, name="robots.txt", context="nive.portal.Portal")
        config.add_view(sitemap_view, name="sitemap.xml", context="nive.portal.Portal")
        config.add_view(logout_view, name="logout", context="nive.portal.Portal")
        config.add_view(login_view,  name="login", context="nive.portal.Portal")
        config.add_view(account_view,name="account", context="nive.portal.Portal")
        #config.add_view(favicon_view, name=u"favicon.txt", context=u"nive.portal.Portal", view=PortalViews)
    
        # translations
        config.add_translation_dirs('nive:locale/')
        
        config.commit()

    
    def Close(self):
        for name in self.components:
            a = getattr(self, name)
            try:
                a.Close()
            except:
                pass
            #setattr(self, name, None)
            





from views import Redirect
from pyramid.exceptions import Forbidden
from pyramid.response import Response
from pyramid.httpexceptions import HTTPError, HTTPNotFound, HTTPServerError


def forbidden_view(forbiddenResponse, request):
    portal = request.context.app.portal
    def status():
        headers = [("X-Result", "false")]
        if hasattr(forbiddenResponse, "headerlist"):
            headers += list(forbiddenResponse.headerlist)
        forbiddenResponse.headerlist = headers    
        return forbiddenResponse
    if request.environ.get("HTTP_X_REQUESTED_WITH")=="XMLHttpRequest":
        # return plain 403
        return status()
    if not portal.configuration.forbiddenUrl:
        # return plain 403
        return status()
    # login form
    url = request.referrer
    return Redirect(portal.configuration.forbiddenUrl+"?msg=forbidden&redirect="+request.url, request, raiseException=False)
       
def login_view(context, request):
    # login form
    portal = context
    return Redirect(portal.configuration.loginUrl+"?redirect="+request.GET.get("redirect",""), request, raiseException=False)
    
def logout_view(context, request):
    # logout to login form
    portal = context
    return Redirect(portal.configuration.logoutUrl+"?redirect="+request.GET.get("redirect",""), request, raiseException=False)
    
def portal_view(context, request):
    # website root / domain root redirect
    portal = context
    return Redirect(portal.configuration.portalDefaultUrl, request, raiseException=False)
    
def account_view(context, request):
    # account page
    portal = context
    return Redirect(portal.configuration.accountUrl, request, raiseException=False)
    
def robots_view(context, request):
    portal = request.context
    # website root / domain root redirect
    r = Response(content_type="text/plain", conditional_response=False)
    r.unicode_body = portal.configuration.robots
    return r

def sitemap_view(context, request):
    portal = request.context
    # portal google sitemap link
    r = Response(content_type="text/xml", conditional_response=False)
    r.unicode_body = portal.configuration.sitemap
    return r

def error_view(context, request):
    #context.body = str(context)
    return context





    
