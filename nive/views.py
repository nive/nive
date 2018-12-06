# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Basic view class for nive object views. 

Use this class as base for custom view definitions for file download support,
data rendering, url generation, http headers and user lookup. 
"""


import os
import time
try:
    import simplejson
except:
    import json
from datetime import datetime
from email.utils import formatdate

from pyramid.response import Response
from pyramid.renderers import render_to_response, get_renderer, render
from pyramid.url import static_url, resource_url
from pyramid.view import render_view
from pyramid.security import authenticated_userid
from pyramid.security import has_permission
from pyramid.i18n import get_localizer

from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPOk, HTTPForbidden, HTTPException
from pyramid.exceptions import NotFound

from nive.i18n import _
from nive import helper
from nive.utils.utils import ConvertToStr, ConvertListToStr, ConvertToDateTime
from nive.utils.utils import FmtSeconds, FormatBytesForDisplay, CutText, GetMimeTypeExtension
from nive import FileNotFound
from nive.definitions import ViewConf
from nive.definitions import IPage, IObject, IViewModuleConf
from nive.definitions import ConfigurationError



class Unauthorized(Exception):
    """
    Raised by failed logins or insufficient permissions
    """
    


class BaseView(object):
    """    """
    __configuration__ = None
    # bw 0.9.13
    viewModuleID = None

    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.appRequestKeys = []
        self.fileExpires = 3600
        self._t = time.time()
        # bw 0.9.13
        self._c_vm = None     # caches the view module configuration

    @property
    def configuration(self):
        """
        View module configuration

        If views are registered by using `ViewModuleConf.views` the ViewModuleConf is automatically
        available as class attribute of the view instance. Any specific configuration values are
        avalilable directly through the configuration. E.g.

            index = self.viewModule.template

        returns ViewModuleConf
        """
        if self.__configuration__ is not None:
            return self.__configuration__()
        return None

    # url handling ----------------------------------------------------------------

    def Url(self, resource=None):
        """
        Generates the default url for the resource. Includes the file extension if one specified 
        for the object.
        
        If resource is None the current context object is used as resource.

        returns url
        """
        resource=resource or self.context
        url = resource_url(resource, self.request)
        if not hasattr(resource, "extension") or not resource.extension:
            return url
        # add extension if it is not the virtual root
        if self.request.virtual_root == resource:
            return url
        return u"%s.%s" % (url[:-1], resource.extension)

    def FolderUrl(self, resource=None):
        """
        Generates the default url for the resource without extension and trailing '/'. 
        
        If resource is None the current context object is used as resource.

        returns url
        """
        return resource_url(resource or self.context, self.request)

    def StaticUrl(self, file):
        """
        Generates the url for a static file.
        *file* is the filename to look the url up for. E.g. for the default static directory use ::
        
            <link tal:attributes="href view.StaticUrl('layout2.css')" 
                  rel="stylesheet" type="text/css" media="all" >
                  
         to reference a file in a different directory you must include the python module like ::

            <link tal:attributes="href view.StaticUrl('my_app.design:static/layout2.css')" 
                  rel="stylesheet" type="text/css" media="all" >
                  
         absolute http urls can also be used based on the url prefix http, https and / ::

            <link tal:attributes="href view.StaticUrl('/assets/layout2.css')" 
                  rel="stylesheet" type="text/css" media="all" >
            <link tal:attributes="href view.StaticUrl('http://myserver.com/assets/layout2.css')" 
                  rel="stylesheet" type="text/css" media="all" >
            <link tal:attributes="href view.StaticUrl('https://myserver.com/assets/layout2.css')" 
                  rel="stylesheet" type="text/css" media="all" >
                  
        returns url
        """
        if file is None:
            return u""
        if file.startswith((u"http://",u"https://",u"/")):
            return file
        if not u":" in file and self.viewModule and self.viewModule.static:
            if self.viewModule.static.endswith((u"/",u":")):
                file = self.viewModule.static + file
            else:
                file = u"%s/%s" % (self.viewModule.static, file)
            if file.startswith((u"http://",u"https://",u"/")):
                return file
        return static_url(file, self.request)

    def FileUrl(self, fieldID, resource=None):
        """
        Generates the file url for the file contained in resource. The resource must have the 'file'
        view included (IFile). If the url is called the download is mapped to ``View.file``. 
        
        If resource is None the current context object is used as resource.

        returns url
        """
        if not resource:
            resource=self.context
        file = resource.files.get(fieldID)
        if not file:
            return u""
        return u"%sfile/%s" % (self.Url(resource), file.filename)

    def PageUrl(self, resource=None, usePageLink=0, addAnchor=True):
        """
        Generates the default page url for the resource with extension. If resource is a page element
        the page containing this element is used for the url. 
        
        If `resource` is None the current context object is used as resource.

        If `addAnchor` is true and resource is not the actula page the url is generated for, the function 
        will append a anchor for the resource to the url based on the id.
        
        returns url
        """
        resource = resource or self.context
        try:
            page = resource.GetPage()
        except AttributeError:
            page = self.context
        link = page.data.get("pagelink")
        if usePageLink and link:
            return self.ResolveUrl(link, resource)

        url = resource_url(page, self.request)
        if hasattr(page, "extension") and page.extension:
            # add extension if it is not the virtual root
            if self.request.virtual_root != page:
                url = u"%s.%s" % (url[:-1], page.extension)

        if not addAnchor or resource == page:
            return url
        # add anchor if resource is a element
        return "%s#nive-element%d"%(url, resource.id)

    def CurrentUrl(self, retainUrlParams=False, preserveHost=1):
        """
        Returns the current url that triggered this request. Url parameter are removed by
        default.
        
        returns url
        """
        if retainUrlParams:
            url = self.request.url
        else:
            url = self.request.url.split(u"?")[0]
        if preserveHost:
            return url
        return "/"+"/".join(url.split("/")[3:])


    def ResolveUrl(self, url, context=None):
        """
        Resolve a string to url for object or the current context.

        Url placeholders to be used as url

        - obj_url
        - obj_folder_url
        - root_url
        - root_folder_url
        - app_url
        - app_folder_url
        - parent_url
        - page_url
        - page_url_anchor

        The url can also be a callable. It is called with two parameters
        `context` and `view class instance`. E.g. ::

            def makeUrl(context, view):
                return view.GetUrl(context) + "?query=" + view.GetFormValue('query')

        The placeholder can be used as the root and be followed by a path e.g. ``obj_folder_url/edit``.
        The remaining path after the slash will be preserved.

        returns url
        """
        if url is None:
            return u""
        if not context:
            context = self.context

        if callable(url):
            return url(context, self)

        parts = url.split(u"/")
        url = parts[0]
        if url == u"page_url":
            url = self.PageUrl(context)
        elif url == u"page_url_anchor":
            url = self.PageUrl(context, addAnchor=True)
        elif url == u"obj_url":
            url = self.Url(context)
        elif url == u"obj_folder_url":
            url = self.FolderUrl(context)
        elif url == u"parent_url":
            url = self.Url(context.parent)
        elif url == u"root_url":
            url = self.Url(context.root())
        elif url == u"root_folder_url":
            url = self.FolderUrl(context.root())
        elif url == u"app_url":
            url = self.Url(context.app)
        elif url == u"app_folder_url":
            url = self.FolderUrl(context.app)
        if len(parts)>1:
            parts[0] = url[:-1]
            return u"/".join(parts)
        return url
    
    
    def ResolveLink(self, link):
        """
        Resolve the link to a valid (page) URL. If the link is an existing object.id the url to the 
        page containing this object is returned.
        
        returns url
        """
        try:
            i = int(link)
            o = self.context.dataroot.LookupObj(i)
            if not o:
                return link
            try:
                return self.PageUrl(o)
            except:
                return self.Url(o)
        except:
            return link

    
    # Response and headers (defined on module level below -------------------------------------------

    def SendResponse(self, data, mime="text/html", filename=None, raiseException=True, status=None, headers=None):
        """
        Creates a response with data as body. If ``raiseException`` is true the function
        will raise a HTTPOk Exception with data as body. A custom response status can only be passed
        if `raiseException` is False.
        
        If filename is not none the response will extended with a ``attachment; filename=filename``
        header.
        """
        return SendResponse(data, mime=mime, filename=filename, raiseException=raiseException, status=status, headers=headers)
        
        
    def Redirect(self, url, messages=None, slot="", raiseException=True, refresh=True, force=False):
        """
        Redirect to the given URL. Messages are stored in session and can be accessed
        by calling ``request.session.pop_flash()``. Messages are added by calling
        ``request.session.flash(m, slot)``.

        `Redirect` automatically detects ajax requests and calls `Relocate` in such a case to prevent a page refresh.
        Set `force=True` to force redirects even for ajax requests.
        """
        return Redirect(url, self.request, messages=messages, slot=slot, raiseException=raiseException, refresh=refresh, force=force)
    

    def Relocate(self, url, messages=None, slot="", raiseException=True, refresh=True):
        """
        Returns messages and X-Relocate header in response.
        If raiseException is True HTTPOk is raised with empty body.
        """
        return Relocate(url, self.request, messages=messages, slot=slot, raiseException=raiseException, refresh=refresh)


    def ResetFlashMessages(self, slot=""):
        """
        Removes all messages stored in session.
        """
        ResetFlashMessages(self.request, slot)
        
    
    def AddHeader(self, name, value, append=False):
        """
        Add a additional response header value.
        """
        AddHeader(self.request, name, value, append)

    
    # render other elements and objects ---------------------------------------------
    
    def index_tmpl(self, path=None):
        #if path:
        #    return get_renderer(path).implementation()
        if not path:
            conf = self.viewModule
            if not conf or not conf.template:
                return None
            path = conf.template
        tmpl = self._LookupTemplate(path)
        return get_renderer(tmpl).implementation()
        

    def DefaultTemplateRenderer(self, values, templatename = None):
        """
        Renders the default template configured in context.configuration.template 
        with the given dictionary `values`. Calls `CacheHeader` to set the default 
        cache headers.
        
        Adds the following values if not set ::
            
            {u"context": self.context, u"view": self} 
        
        Template lookup first searches the current view module and if not found
        the parent or extended view module. 
        """
        if not templatename:
            templatename = self.context.configuration.template
            if not templatename:
                templatename = self.context.configuration.id
        tmpl = self._LookupTemplate(templatename)
        if not tmpl:
            raise ConfigurationError, "Template not found: %(name)s %(type)s." % {"name": templatename, "type": self.context.configuration.id}
        if not "context" in values: values[u"context"] = self.context
        if not "view" in values: values[u"view"] = self
        response = render_to_response(tmpl, values, request=self.request)
        self.CacheHeader(response, user=self.User())
        return response

    def _LookupTemplate(self, tmplfile):
        conf = self.viewModule
        if not tmplfile:
            raise TypeError, "'tmplfile' is None. Need a template name to lookup the path."
        if not conf or u":" in tmplfile:
            return tmplfile
        path = conf.templates
        if not path.endswith((u":",u"/")):
            path += u"/"
        fn = path + tmplfile
        try:
            if get_renderer(fn):
                return fn
        except ValueError:
            pass
        if not conf.parent:
            return tmplfile
        path = conf.parent.templates
        if not path.endswith((u":",u"/")):
            path += u"/"
        fn = path + tmplfile
        return fn


    def RenderView(self, obj, name="", secure=True, raiseUnauthorized=False, codepage="utf-8"):
        """
        Render a view for the object.
        
        *name* is the name of the view to be looked up.
        
        If *secure* is true permissions of the current user are checked against the view. If the
        user lacks the necessary permissions and empty string is returned or if *raiseUnauthorized*
        is True HTTPForbidden is raised. 
        
        returns rendered result
        """
        # store original context to reset after calling render_view
        orgctx = self.request.context
        orgresp = self.request.response
        orgname = self.request.view_name

        self.request.context = obj
        self.request.response = Response()
        self.request.view_name = name
        try:
            value = render_view(obj, self.request, name, secure)
            if value is None:
                value = ""
        except HTTPNotFound:
            value = "Not found!"
        except HTTPForbidden:
            value = ""
        finally:
            self.request.context = orgctx
            self.request.response = orgresp
            self.request.view_name = orgname

        return unicode(value, codepage)

    
    def Assets(self, assets=None, ignore=None, viewModuleConfID=None, types=None):  
        """
        Renders a list of static ressources as html <script> and <link>.
        If assets is None the list of assets is looked up in the view module-configuration.
        Asset definitions use a identifier and an asset path like: ::
        
            assets = (
              ('jquery.js', 'nive_cms.cmsview:static/mods/jquery.min.js'),
              ('toolbox.css', 'nive_cms.cmsview:static/toolbox/toolbox.css'),
              ('jquery-ui.js', 'http://example.com/static/mods/jquery.min.js')
            )
                
        If for example jquery is already included in the main page Assets() can be told to ignore certain
        entries: ::
        
            cmsview.Assets(ignore=["jquery.js"])  
            
        The list of assets is configured as part of the view module settings. If the view module 
        configuration is not stored as class attribute (`self.viewModule`) the configuration can be accessed 
        by id in the applications registry. In this case the id can be passed in like 
        `Assets(viewModuleConfID='editor')` to lookup the the configuration in the registry. 
        
        By default `Assets` renders both css and js links. You can use the parameter types e.g *types="js"*
        to get js file links only. Set *types="css"* to get all css links.
        """
        if viewModuleConfID:
            app = self.context.app
            conf = app.QueryConfByName(IViewModuleConf, viewModuleConfID)
            if not conf:
                return u""
            assets = conf.assets
        if assets==None and self.viewModule:
            assets = self.viewModule.assets
        if not assets:
            return u""
        
        if ignore==None:
            ignore = []
        
        js_tags = css_tags = []
        if types in (None, "js"):
            js_links = [self.StaticUrl(r[1]) for r in filter(lambda v: v[0] not in ignore and v[1].endswith(u".js"), assets)]
            js_tags = [u'<script src="%s" type="text/javascript"></script>' % link for link in js_links]
        if types in (None, "css"):
            css_links = [self.StaticUrl(r[1]) for r in filter(lambda v: v[0] not in ignore and v[1].endswith(u".css"), assets)]
            css_tags = [u'<link href="%s" rel="stylesheet" type="text/css" media="all">' % link for link in css_links]
        return (u"\r\n").join(js_tags + css_tags)
        

    def tmpl(self):
        """
        Default function for template rendering.
        """
        return {}
    
    
    # file handling ------------------------------------------------------------------
    
    def file(self):
        return self.File()

    def File(self):
        """
        Used by "file" view for the current context. 
        
        Calls SendFile() for the file matching the filename of the current url.
        """
        if not len(self.request.subpath):
            raise NotFound
        path = self.request.subpath[0]
        if self.context.files.has_key(path):
            file = self.context.GetFile(path)
        else:
            file = self.context.GetFileByName(path)
        if not file:
            raise NotFound
        try:
            return self.SendFile(file)
        except FileNotFound:
            raise NotFound

    def SendFile(self, file):
        """
        Creates the response and sends the file back. Uses the FileIterator.
        
        #!date format
        """
        if not file:
            return HTTPNotFound()
        last_mod = file.mtime
        if not last_mod:
            last_mod = self.context.meta.pool_change
        r = Response(content_type=str(GetMimeTypeExtension(file.extension)), conditional_response=True)
        iterator = file.iterator()
        if iterator:
            r.app_iter = iterator
        else:
            try:
                r.body = file.read()
            except FileNotFound:
                raise NotFound
        r.content_length = file.size
        r.last_modified = last_mod
        r.etag = '%s-%s' % (last_mod, hash(file.path))
        r.cache_expires(self.fileExpires)
        return r    


    # http caching ----------------------------------------------------------------

    def CacheHeader(self, response, user=None):
        """
        Adds a http cache header to the response. If user is not None *NoCache()* is called, otherwise
        *Modified()*.
        
        returns response
        """
        if user is not None:
            return self.NoCache(response)
        return self.Modified(response, user)

    def NoCache(self, response, user=None):
        """
        Adds a no-cache header to the response.
        
        returns response
        """
        response.cache_control = u"no-cache"
        response.etag = '%s-%s' % (response.content_length, str(self.context.id))
        return response

    def Modified(self, response, user=None):
        """
        Adds a last modified header to the response. meta.pool_change is used as date.

        returns response
        """
        if user:
            response.last_modified = formatdate(timeval=None, localtime=True, usegmt=True)
        else:
            t = self.context.meta.get("pool_change")
            if t and isinstance(t, basestring):
                t = ConvertToDateTime(t).timetuple()
                t = time.mktime(t)
            elif t:
                t = time.mktime(t.timetuple())
            else:
                t = None
            response.last_modified = formatdate(timeval=t, localtime=True, usegmt=True)
        response.etag = '%s-%s-%s' % (response.last_modified, response.content_length, str(self.context.id))
        return response


    # configuration -------------------------------------------------

    def GetViewConf(self, view_name=None):
        """
        Looks up the current view configuration `nive.definitions.ViewConf`.
        Please note: Unique view names on view module level are required for this
        function!

        view_name: If None the current view_name is used.
        returns `nive.definitions.ViewConf` or None
        """
        c = self.configuration
        if c is None:
            return None
        name = view_name or self.request.view_name
        found = []
        for v in c.views:
            if v.name==name:
                found.append(v)
        if len(found)==1:
            return found[0]
        elif len(found)==0:
            return None
        # try to find the right one if multiple names match
        for v in found:
            if v.custom_predicates:
                for c in v.custom_predicates:
                    # match the first one
                    if apply(c, (self.context, self.request)):
                        return v
        return None


    # user and security -------------------------------------------------
    
    @property
    def user(self):
        return self.User()
    
    def User(self, sessionuser=True):
        """
        Get the currently signed in user. If sessionuser=False the function will return
        the uncached write enabled user from database.
        
        returns the *Authenticated User Object* or None
        """
        return User(self.context, self.request, sessionuser)

    def UserName(self):
        """
        returns the *Authenticated User Name* or None
        """
        return authenticated_userid(self.request)    

    def Allowed(self, permission, context=None):
        """
        Check if the current user has the *permission* for the *context*.
        If context is none the current context is used
        
        returns True / False
        """
        return has_permission(permission, context or self.context, self.request)
    
    def InGroups(self, groups):
        """
        Check if current user is in one of the groups.
        """
        user = self.User()
        if not user:
            return False
        return user.InGroups(groups)
    

    # render helper ---------------------------------------------------------
    
    def GetLocale(self):
        if hasattr(self, "_c_locale"):
            return self._c_locale
        l = u"en"
        self._c_locale = l
        return l
    
    def GetTimezone(self):
        if hasattr(self, "_c_tz"):
            return self._c_tz
        l = u"GMT"
        self._c_tz = l
        return l
    
    def RenderField(self, fld, data=None, context=None):
        """
        Render the data field for html display. Rendering depends on the datatype defined
        in the field configuration.
        
        If data is None the current context is used.
        
        returns string
        """
        if context is None:
            context = self.context
        if isinstance(fld, basestring):
            fld = context.GetFieldConf(fld)
        if not fld:
            return _(u"<em>Unknown field</em>")
        if data is None:
            data = context.data.get(fld['id'], context.meta.get(fld['id']))
        if fld['datatype']=='file':
            url = self.FileUrl(fld['id'])
            if not url:
                return u""
            url2 = url.lower()
            if url2.find(u".jpg")!=-1 or url2.find(u".jpeg")!=-1 or url2.find(u".png")!=-1 or url2.find(u".gif")!=-1:
                return u"""<img src="%s">""" % (url)
            return u"""<a href="%s">download</a>""" % (url)
        return FieldRenderer(context).Render(fld, data, context=context)
    
    def HtmlTitle(self):
        t = self.request.environ.get(u"htmltitle")
        if t:
            return t
        return self.context.GetTitle()
    
    
    def Translate(self, text):
        """
        Tranlate a translation string. Extracts language from request.
        """
        localizer = get_localizer(self.request)
        return localizer.translate(text)
        

    @property
    def utilities(self):
        """
        You can easily make utility functions like renderers and format functions
        accessible in templates by adding the functions to your view module
        configuration. e.g. ::

            def renderTime(value):
                return value.strftime("%H:%M")

            view_configuration = ViewModuleConf(
                id = "views",
                name = u"Views",
                # utilities
                utilities = Conf(renderTime=renderTime)
                ...
            )

        You can call `renderTime` in your template by accessing the view class instance ::

            view.utilities.renderTime(value)


        :return: utilities mapping object
        """
        return self.configuration.get("utilities")

    # parameter handling ------------------------------------------------------------

    def GetFormValue(self, key, default=None, request=None, method=None):
        """
        Extract a form field from request. 
        Works with webob requests and simple dictionaries.
        
        returns the value or *default*
        """
        if not request:
            request = self.request
        if method is None and hasattr(request, "method"):
            method = request.method
        try:
            if method == "POST":
                if request.content_type=="application/json":
                    value = request.json_body.get(key)
                else:
                    value = request.POST.getall(key)
            elif method == "GET":
                value = request.GET.getall(key)
            else:
                if request.content_type=="application/json":
                    value = request.json_body.get(key)
                else:
                    value = request.POST.getall(key)
                if not value:
                    value = request.GET.getall(key)
            if isinstance(value, bytes):
                value = unicode(value, self.context.app.configuration.frontendCodepage)
        except (AttributeError,KeyError):
            if method == "POST":
                if request.content_type=="application/json":
                    try:
                        value = request.json_body.get(key)
                    except AttributeError:
                        value = None
                else:
                    value = request.POST.get(key)
            elif method == "GET":
                value = request.GET.get(key)
            else:
                if request.content_type=="application/json":
                    value = request.json_body.get(key)
                else:
                    value = request.POST.get(key)
                if not value:
                    value = request.GET.get(key)
            if isinstance(value, bytes):
                value = unicode(value, self.context.app.configuration.frontendCodepage)
            if value is None:
                return default
            return value
        if not len(value):
            return default
        elif len(value)==1:
            if value is None:
                return default
            return value[0]
        if value is None:
            return default
        return value            


    def GetFormValues(self, request=None, method=None):
        """
        Extract all form fields from request. 
        Works with webob requests and simple dictionaries.
        
        returns dictionary
        """
        if not request:
            request = self.request
        if method is None and hasattr(request, "method"):
            method = request.method
        try:
            if method == "POST":
                if request.content_type=="application/json":
                    values = request.json_body
                else:
                    values = request.POST.mixed()
            elif method == "GET":
                values = request.GET.mixed()
            else:
                values = request.GET.mixed()
                if request.content_type=="application/json":
                    values.update(request.json_body)
                else:
                    values.update(request.POST.mixed())
        except AttributeError:
            try:
                if method == "POST":
                    if request.content_type=="application/json":
                        values = request.json_body
                    else:
                        values = request.POST
                elif method == "GET":
                    values = request.GET
                else:
                    values = {}
                    values.update(request.GET)
                    if request.content_type=="application/json":
                        values.update(request.json_body)
                    else:
                        values.update(request.POST)
            except AttributeError:
                values = request
        if not values:
            return {}
        return values
    

    def FmtURLParam(self, **kw):
        """
        Format all kw items as url parameter. 
        
        returns string
        """
        url = []
        params = kw
        #opt
        for p in params.keys():
            if len(url):
                url.append(u"&")
            url.append(u"%s=%s" % (p, params[p]))
        return u"".join(url)    #urllib.quote_plus()
    

    def FmtFormParam(self, **kw):
        """    
        Format all kw items as hidden input fields for forms.
        
        returns string 
        """
        form = []
        params = kw
        for p in params.keys():
            value = ConvertToStr(params[p])
            form.append(u"<input type='hidden' name='%s' value='%s'>" % (p, value))
        return "".join(form)


    def FmtTextAsHTML(self, text):
        """
        Converts newlines to <br>.

        returns string
        """
        if not text:
            return u""
        if text.find(u"\r\n")!=-1:
            text = text.replace(u"\r\n",u"<br>\r\n")
        else:
            text = text.replace(u"\n",u"<br>\n")
        return text

    def FmtDateText(self, date, language=None):
        """
        Formats dates as readable text in conventional format.

        returns string
        """
        if not date:
            return u""
        if not isinstance(date, datetime):
            date = ConvertToDateTime(date)
        return date.strftime(u"%c")

    def FmtDateNumbers(self, date, language=None):
        """
        Formats dates as numbers e.g 13.12.2011.

        returns string
        """
        if not date:
            return u""
        if not isinstance(date, datetime):
            date = ConvertToDateTime(date)
        return date.strftime(u"%x")

    def FmtSeconds(self, secs):
        """ seconds to readable text """
        return FmtSeconds(secs)

    def FmtBytes(self, size):
        """ bytes to readable text """
        return FormatBytesForDisplay(size)

    def FmtTag(self, tag, closeTag="tag", **attributes):
        """
        Write a html tag with attributes.
        closeTag: 'tag', 'inline', 'no', 'only'
        """
        if closeTag=="only":
            return u"</%s>" % (tag)
        attrs = u""
        if attributes:
            attrs = [u'%s="%s"'%(a[0],unicode(a[1])) for a in attributes.items()]
            attrs = u" " + u" ".join(attrs)
        if closeTag=="inline":
            return u"<%s%s/>" % (tag, attrs)
        elif closeTag in (None,'no'):
            return u"<%s%s>" % (tag, attrs)
        return u"<%s%s></%s>" % (tag, attrs, tag)

    def CutText(self, text, length):
        """ bytes to readable text """
        return CutText(text, length)


    def mark(self):
        return time.time() - self._t

    def mark2(self):
        try:
            return u"""<div class="mark">%.04f</div>""" % (time.time() - self.request.environ.get("START_TIME", self._t))
        except:
            return u""


    # to be removed in the future
    def IsPage(self, object=None):
        # to be removed
        if not object:
            return IPage.providedBy(self.context)
        return IPage.providedBy(object)


    @property
    def viewModule(self):
        # bw 0.9.13
        # use self.configuration instead
        if self.__configuration__:
            return self.configuration
        if not self.viewModuleID:
            return self._c_vm
        self._c_vm = self._c_vm or self.context.app.QueryConfByName(IViewModuleConf, self.viewModuleID)
        return self._c_vm


 
# Configuration helper -------------------------------------------------
def UpdateViewConf(viewModule, viewname, **viewconfig):
    """
    Update and replace the view configuration for the view `viewname` in the given view module.
    You can pass a single or multiple values as `viewconfig` to overwrite the original views
    configuration.

    :param viewModule:
    :param viewname:
    :param **viewconfig:
    :return: None
    """
    p = 0
    for v in viewModule.views:
        if v.name==viewname:
            # create a copy fo the view and replace the original
            vcopy = ViewConf(copyFrom=v, **viewconfig)
            viewModule.views = list(viewModule.views)
            viewModule.views[p] = vcopy
            viewModule.views = tuple(viewModule.views)
            return
        p += 1



# Response utilities -------------------------------------------------
from zope.interface import implementer
from pyramid.interfaces import IExceptionResponse

@implementer(IExceptionResponse)
class ExceptionalResponse(HTTPOk):
    def __init__(self, headers=None, **kw):
        # HTTPException: map status int to self.code
        if "status" in kw:
            status = kw["status"]
            if status is not None:
                self.code = int(kw["status"].split()[0])
            del kw["status"]
        super(HTTPOk,self).__init__(headers=headers, detail=kw.get("detail","HTTP OK Response"), **kw)

    def __str__(self):
        return self.detail

    def __call__(self, environ, start_response):
        return Response.__call__(self, environ, start_response)


def SendResponse(data, mime="text/html", filename=None, raiseException=True, status=None, headers=None):
    """
    See views.BaseView class function for docs
    """
    cd = None
    if filename:
        cd = 'attachment; filename=%s'%(filename)
    if raiseException:
        raise ExceptionalResponse(content_type=mime, body=data, content_disposition=cd, status=status, headers=headers)
    return Response(content_type=mime, body=data, content_disposition=cd, status=status, headerlist=headers)


def Redirect(url, request, messages=None, slot="", raiseException=True, refresh=True, force=False):
    """
    See views.BaseView class function for docs
    """
    if not force and request.environ.get("HTTP_X_REQUESTED_WITH")=="XMLHttpRequest":
        # ajax call -> use relocate to handle this case
        return Relocate(url, request, messages, slot, raiseException, refresh)
    if messages:
        if isinstance(messages, basestring):
            request.session.flash(messages, slot)
        else:
            for m in messages:
                request.session.flash(m, slot)
    headers = None
    if hasattr(request.response, "headerlist"):
        headers = request.response.headerlist
    if raiseException:
        raise HTTPFound(location=url, headers=headers)
    return HTTPFound(location=url, headers=headers)
    

def Relocate(url, request, messages=None, slot="", raiseException=True, refresh=True):
    """
    See views.BaseView class function for docs
    """
    if messages:
        if isinstance(messages, basestring):
            request.session.flash(messages, slot)
        else:
            for m in messages:
                request.session.flash(m, slot)
    if isinstance(url, unicode):
        url = url.encode("utf-8")
    body = json.dumps({u"location": url, u"messages": messages, "refresh": refresh})
    headers = [('X-Relocate', url)]
    if hasattr(request.response, "headerlist"):
        for h in list(request.response.headerlist):
            # remove content type and content length
            if h[0].lower() in ("content-type", "content-length"):
                continue
            headers.append(h)
    if raiseException:
        raise ExceptionalResponse(headers=headers, body=body, content_type="application/json; charset=utf-8")
    return body


def ResetFlashMessages(request, slot=""):
    """
    See views.BaseView class function for docs
    """
    while request.session.pop_flash(slot):
        continue
        
    
def AddHeader(request, name, value, append=False):
    """
    See views.BaseView class function for docs
    """
    if append:
        headers = [(name, value)]
        if hasattr(request.response, "headerlist"):
            headers += list(request.response.headerlist)
        request.response.headerlist = headers
    else:
        request.response.headers[name] = value


def PreflightRequest(request,
                     allowOrigins="*",
                     allowMethods="POST, GET, DELETE, OPTIONS",
                     allowHeaders="",
                     allowCredentials=True,
                     maxAge=3600,
                     response=None):
    """
    Handles Access-Control preflight requests.

    :param request: The current request.
    :param allowOrigins: Either '*' (all allowed) or a list of hosts e.g ('http://mydomain.com')
    :param allowMethods: 'POST, GET, DELETE, OPTIONS'. Allowed http methods as string.
    :param allowHeaders: Custom headers passed in a request as string.
    :param allowCredentials: True/False. Credentials are made accessible in the client application.
    :param response: The response to be returned. if None `request.response` is used.
    :return: response
    """
    response = response or request.response
    origin = request.headers.get("Origin")
    if origin is None:
        # not a access-control preflight?
        return response
    if allowOrigins!="*":
        # check request origin, might also be checked against host
        if not origin in allowOrigins and not "*" in allowOrigins:
            # not allowed
            # set status to 405
            response.status="405 Not Allowed"
            return response
    headers = [
        ("Access-Control-Allow-Origin", origin),
        ("Access-Control-Allow-Methods", allowMethods),
        ("Access-Control-Allow-Credentials", str(allowCredentials).lower()),
        ("Access-Control-Max-Age", maxAge),
        ("Access-Control-Allow-Headers", allowHeaders),
        ("Vary", "Accept-Encoding, Origin")
    ]
    if hasattr(response, "headerlist"):
        headers += list(response.headerlist)
    response.headerlist = headers
    return response


def OriginResponse(request,
                   allowOrigins="*",
                   allowCredentials=True,
                   exposeHeaders="",
                   response=None):
    """
    Handles Access-Control responses to Origin header containing requests. This function
    adds required headers only and does not change the reponse.

    Returns None if the Origin does not match or the header is not present in the request.

    :param request: The current request.
    :param exposeHeaders: A list of custom headers to be made accessible in the client application as string.
    :param allowCredentials: True/False. Credentials are made accessible in the client application.
    :param response: The response to be returned. if None `request.response` is used.
    :return: response or None
    """
    response = response or request.response
    origin = request.headers.get("Origin")
    if origin is None or allowOrigins is None:
        # not a access-control aware request?
        return response
    if allowOrigins!="*":
        # check request origin, might also be checked against host
        if not origin in allowOrigins and not "*" in allowOrigins:
            # not allowed
            return None
    headers = [
        ("Access-Control-Allow-Origin", origin),
        ("Access-Control-Allow-Credentials", str(allowCredentials).lower()),
        ("Access-Control-Expose-Headers", exposeHeaders),
        ("Vary", "Accept-Encoding, Origin")
    ]
    if hasattr(response, "headerlist"):
        headers += list(response.headerlist)
    response.headerlist = headers
    return response


def User(context, request, sessionuser=True):
    """
    Get the currently signed in user. If sessionuser=False the function will return
    the uncached write enabled user from database.

    returns the *Authenticated User Object* or None
    """
    # cached session user object
    if not sessionuser:
        ident = authenticated_userid(request)
        if not ident:
            return None
        return context.app.portal.userdb.root().LookupUser(ident=ident)
    try:
        user = request.environ["authenticated_user"]
        if user:
            return user
    except KeyError:
        pass
    ident = authenticated_userid(request)
    if not ident:
        return None
    return context.app.portal.userdb.root().GetUser(ident)


class FieldRenderer(object):
    
    def __init__(self, context, skip=()):
        self.context = context
        self.skipRender = skip
        
    def Render(self, fieldConf, value, useDefault=False, listItems=None, context=None, **kw):
        """
        fieldConf = FieldConf of field to be rendered
        value = the value to be rendered
        useDefault = use default values from fieldConf if not found in value
        listItems = used for list lookup key -> name
        context = context object the field is rendered for. Required if listItems=None.
        
        **kw:
        static = static root path for images
        """
        data = u""
        if useDefault:
            data = fieldConf["default"]
        if value != None:
            data = value
        if fieldConf["id"] in self.skipRender:
            return data

        def loadListItems(fld, context):
            if not context:
                return []
            pool_type = context.GetTypeID() 
            return helper.LoadListItems(fld, app=context.app, obj=context, pool_type=pool_type)
        
        # format for output
        fType = fieldConf["datatype"]

        # fomat settings
        settings = fieldConf.get("settings",{})
        if settings:
            fmt = settings.get("format")
            if fmt=="bytesize":
                data = FormatBytesForDisplay(data)
                return data
            elif fmt=="image":
                tmpl = settings.get("path", u"")
                path = tmpl % {"data":data, "static": kw.get("static",u"")}
                data = """<img src="%(path)s" title="%(name)s">""" % {"path":path, "name": fieldConf.name}
                return data
        
        if fType == "bool":
            if data:
                data = _(u"Yes")
            else:
                data = _(u"No")

        elif fType == "string":
            if settings.get("relation") == u"userid":
                # load user name from database
                try:
                    udb = context.app.portal.userdb.root()
                    user = udb.GetUser(data, activeOnly=0)
                    if user:
                        data = user.GetTitle()
                except AttributeError:
                    pass

        elif fType == "text":
            fmt = settings.get("format")
            if fmt=="newlineToBr":
                data = data.replace(u"\r\n", u"\r\n<br>")
            elif fmt=="markdown":
                import markdown2
                data = markdown2.markdown(data)

        elif fType == "date":
            if not isinstance(data, datetime):
                if not data:
                    return u""
                data = ConvertToDateTime(data)
            fmt = settings.get("strftime", u"%x")
            return data.strftime(fmt)

        elif fType in ("datetime", "timestamp"):
            fmt = settings.get("format")
            if not isinstance(data, datetime):
                if not data:
                    return u""
                data = ConvertToDateTime(data)
            # defaults
            fmt = settings.get("strftime")
            if not fmt:
                fmt = u"%x %H:%M"
                # hide hour and minutes if zero
                if data.hour==0 and data.minute==0 and data.second==0:
                    fmt = u"%x"
                elif settings.get("seconds"):
                    fmt = u"%x %X"
            return data.strftime(fmt)

        elif fType == "unit":
            if data == 0 or data == "0":
                return ""
            return data

        elif fType == "unitlist":
            if isinstance(data, (list, tuple)):
                return ConvertListToStr(data)
            return str(data)

        elif fType == "list" or fType == "radio":
            options = listItems or loadListItems(fieldConf, context)
            if not options:
                options = fieldConf.get("listItems")
                if hasattr(options, "__call__"):
                    options = options(fieldConf, self.context)

            if options:
                for item in options:
                    if item["id"] == data:
                        data = item["name"]
                        break
                
        elif fType in("multilist", "checkbox", "mselection", "mcheckboxes"):
            values = []
            options = listItems or loadListItems(fieldConf, context)
            if not options:
                options = fieldConf.get("listItems")
                if hasattr(options, "__call__"):
                    options = options(fieldConf, self.context)

            if isinstance(data, basestring):
                data = tuple(data.split(u"\n"))
            for ref in data:
                if options:
                    for item in options:
                        if item["id"] == ref:
                            values.append(item["name"])
                else:
                    values.append(ref)
            delimiter = u", "
            if settings and u"delimiter" in settings:
                delimiter = settings[u"delimiter"]
            data = delimiter.join(values)

        elif fType == "url":
            if render:
                if data != u"" and data.find(u"http://") == -1:
                    data = u"http://" + data
                l = data[7:50]
                if len(data) > 50:
                    l += u"..."
                data = u"<a alt='%s' href='%s' target='_blank'>%s</a>" % (data, data, l)

        elif fType == "urllist":
            urllist = data
            data = []
            if len(urllist) and urllist[0] == u"[":
                urllist = urllist[1:-1]
                ul = urllist.split(u"', u'")
                ul[0] = ul[0][1:]
                ul[len(ul)-1] = ul[len(ul)-1][:-1]
            else:
                ul = urllist.replace(u"\r",u"")
                ul = ul.split(u"\n")
            links = []
            for l in ul:
                t = l.split(u"|||")
                title = u""
                url = t[0]
                if len(t) > 1:
                    title = t[1]
                if title != u"":
                    title = u'%s (%s)' % (title, url)
                else:
                    title = url
                links.append({"id": l, "name": title})
                data.append(u"<a alt='%s' title='%s' href='%s' target='_blank'>%s</a><br>" % (title, title, url, title))
            data = u"".join(data)

        elif fType == "password":
            data = u"*****"

        elif fType == "lines":
            if data:
                tmpl = u"%s<br>"
                if settings and u"tmpl" in settings:
                    tmpl = settings[u"tmpl"]
                if isinstance(data, basestring):
                    data = data.split("\n")
                data = u"".join([tmpl%ll for ll in data])

        return data
    

# Mail template mapper -------------------------------------------------

class Mail(object):
    """
    Mail template object with template link and title. ::
    
        mail = Mail(title="New mail", tmpl="mypackage:templates/foo.pt")
        body = mail(value1=1, value2=2)
        
    the body of the mail is generated by calling the mail object. *kw* parameters
    are passed on in template.render()
    """
    title = u""
    tmpl = None     # 'mypackage:templates/foo.pt'
    
    def __init__(self, title=u"", tmpl=None):
        self.title = title
        self.tmpl = tmpl
    
    def __call__(self, **kws):
        mail = render(self.tmpl, kws)
        return mail
