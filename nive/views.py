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
from datetime import datetime
from email.utils import formatdate

from pyramid.response import Response
from pyramid.renderers import render_to_response, get_renderer, render
from pyramid.url import static_url, resource_url
from pyramid.view import render_view
from pyramid.security import authenticated_userid
from pyramid.security import has_permission
from pyramid.i18n import get_localizer

from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPOk, HTTPForbidden
from pyramid.exceptions import NotFound

from nive.i18n import _
from nive import helper
from nive.utils.utils import ConvertToStr, ConvertListToStr, ConvertToDateTime
from nive.utils.utils import FmtSeconds, FormatBytesForDisplay, CutText, GetMimeTypeExtension
from nive import FileNotFound
from nive.definitions import IPage, IObject, IViewModuleConf



class Unauthorized(Exception):
    """
    Raised by failed logins or insufficient permissions
    """
    


class BaseView(object):
    """    """
    viewModuleID = None
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.appRequestKeys = []
        self.fileExpires = 3600
        self._t = time.time()
        self._c_vm = None     # caches the view module configuration

    @property
    def viewModule(self):
        """
        View module configuration lookup
        
        Views in pyramid are not connected to configuration settings by default. In `nive` view
        configurations can be linked to view classes by setting the view module configuraions ID
        as a class attribute.  
        
        E.g. the following line will link all instances of the view class to the registered 
        ``IViewModuleConf`` with id = `design`.
        
            self.viewModuleID = "design"
            
        The configurations are stored and looked in the applications registry. 
        """
        if not self.viewModuleID:
            return self._c_vm
        self._c_vm = self._c_vm or self.context.app.QueryConfByName(IViewModuleConf, self.viewModuleID)
        return self._c_vm
        
    # url handling ----------------------------------------------------------------

    def Url(self, resource=None):
        """
        Generates the default url for the resource. Includes the file extension if one specified 
        for the object.
        
        If resource is None the current context object is used as resource.

        returns url
        """
        if not resource:
            resource=self.context
        if hasattr(resource, "extension") and resource.extension:
            return u"%s.%s" % (resource_url(resource, self.request)[:-1], resource.extension)
        return resource_url(resource, self.request)

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

    def PageUrl(self, resource=None, usePageLink=0, addAnchor=False):
        """
        Generates the default page url for the resource with extension. If resource is a page element
        the page containing this element is used for the url. 
        
        If `resource` is None the current context object is used as resource.

        If `addAnchor` is true and resource is not the actula page the url is generated for, the function 
        will append a anchor for the resource to the url based on the id.
        
        returns url
        """
        if not resource:
            resource=self.context
        try:
            page = resource.GetPage()
        except:
            page = self.context
        link = page.data.get("pagelink")
        if usePageLink and link:
            return self.ResolveUrl(link, resource)
        if hasattr(page, "extension"):
            url = u"%s.%s" % (resource_url(page, self.request)[:-1], page.extension)
        else:
            url = resource_url(page, self.request)
        if not addAnchor or resource == page:
            return url
        return "%s#nive-element%d"%(url,resource.id)

    def CurrentUrl(self, retainUrlParams=False):
        """
        Returns the current url that triggered this request. Url parameter are removed by
        default.
        
        returns url
        """
        if retainUrlParams:
            return self.request.url
        return self.request.url.split(u"?")[0]

    def ResolveUrl(self, url, object=None):
        """
        Resolve a string to url for object or the current context.

        Possible values:
        
        - page_url
        - page_url_anchor
        - obj_url
        - obj_folder_url
        - parent_url
        """
        if url==None:
            return u""
        if not object or not IObject.providedBy(object):
            object = self.context
        if url == "page_url":
            url = self.PageUrl(object)
        elif url == "page_url_anchor":
            url = self.PageUrl(object, addAnchor=True)
        elif url == "obj_url":
            url = self.Url(object)
        elif url.find("obj_folder_url")!=-1:
            url = url.replace("obj_folder_url", self.FolderUrl(object))
        elif url == "parent_url":
            url = self.Url(object.parent)
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

    def SendResponse(self, data, mime="text/html", filename=None, raiseException=True):
        """
        Creates a response with data as body. If ``raiseException`` is true the function
        will raise a HTTPOk Exception with data as body.
        
        If filename is not none the response will extended with a ``attachment; filename=filename``
        header.
        """
        return SendResponse(data, mime=mime, filename=filename, raiseException=raiseException)
        
        
    def Redirect(self, url, messages=None, slot="", raiseException=True):
        """
        Redirect to the given URL. Messages are stored in session and can be accessed
        by calling ``request.session.pop_flash()``. Messages are added by calling
        ``request.session.flash(m, slot)``.
        """
        return Redirect(url, self.request, messages=messages, slot=slot, raiseException=raiseException)
    

    def Relocate(self, url, messages=None, slot="", raiseException=True):
        """
        Returns messages and X-Relocate header in response.
        If raiseException is True HTTPOk is raised with empty body.
        """
        return Relocate(url, self.request, messages=messages, slot=slot, raiseException=raiseException)


    def ResetFlashMessages(self, slot=""):
        """
        Removes all messages stored in session.
        """
        ResetFlashMessages(self.request, slot)
        
    
    def AddHeader(self, name, value):
        """
        Add a additional response header value.
        """
        AddHeader(self.request, name, value)

    
    # render other elements and objects ---------------------------------------------
    
    def index_tmpl(self, path=None):
        if path:
            return get_renderer(path).implementation()
        if not self.viewModule or not self.viewModule.mainTemplate:
            return None
        tmpl = self._LookupTemplate(self.viewModule.mainTemplate)
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
        self.request.context = obj
        if not raiseUnauthorized:
            try:
                value = render_view(obj, self.request, name, secure)
                self.request.context = orgctx
            except HTTPNotFound:
                self.request.context = orgctx
                return u"Not found!"
            except HTTPForbidden:
                self.request.context = orgctx
                return u""
        else:
            try:
                value = render_view(obj, self.request, name, secure)
            except HTTPNotFound:
                self.request.context = orgctx
                return u"Not found!"
            except:
                self.request.context = orgctx
                raise
        self.request.context = orgctx
        if not value:
            return u""
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
        

    def IsPage(self, object=None):
        """
        Check if object is a page.
        
        returns bool
        """
        if not object:
            return IPage.providedBy(self.context)
        return IPage.providedBy(object)
    
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
        file = self.context.GetFileByName(self.request.subpath[0])
        if not file:
            raise NotFound
        return self.SendFile(file)


    def SendFile(self, file):
        """
        Creates the response and sends the file back. Uses the FileIterator.
        
        #!date format
        """
        if not file:
            return HTTPNotFound()
        last_mod = file.mtime()
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
        if user:
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
            if self.context.meta.get("pool_change"):
                t = ConvertToDateTime(self.context.meta.get("pool_change")).timetuple()
                t = time.mktime(t)
            else:
                t = None
            response.last_modified = formatdate(timeval=t, localtime=True, usegmt=True)
        response.etag = '%s-%s-%s' % (response.last_modified, response.content_length, str(self.context.id))
        return response


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
        # cached session user object
        if not sessionuser:
            ident = authenticated_userid(self.request)
            if not ident:
                return None
            return self.context.app.portal.userdb.root().LookupUser(ident=ident)
        try:
            user = self.request.environ["authenticated_user"]
            if user:
                return user
        except KeyError:
            pass
        ident = authenticated_userid(self.request)
        if not ident:
            return None
        return self.context.app.portal.userdb.root().GetUser(ident)
    
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
    
    def RenderField(self, fld, data=None):
        """
        Render the data field for html display. Rendering depends on the datatype defined
        in the field configuration.
        
        If data is None the current context is used.
        
        returns string
        """
        if isinstance(fld, basestring):
            fld = self.context.GetFieldConf(fld)
        if not fld:
            return _(u"<em>Unknown field</em>")
        if data == None:
            data = self.context.data.get(fld['id'], self.context.meta.get(fld['id']))
        if fld['datatype']=='file':
            url = self.FileUrl(fld['id'])
            if not url:
                return u""
            url2 = url.lower()
            if url2.find(u".jpg")!=-1 or url2.find(u".jpeg")!=-1 or url2.find(u".png")!=-1 or url2.find(u".gif")!=-1:
                return u"""<img src="%s">""" % (url)
            return u"""<a href="%s">download</a>""" % (url)
        return FieldRenderer(self.context).Render(fld, data, context=self.context)
    
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
        elif closeTag==None:
            return u"<%s%s>" % (tag, attrs)
        return u"<%s%s></%s>" % (tag, attrs, tag)

    def CutText(self, text, length):
        """ bytes to readable text """
        return CutText(text, length)

    # parameter handling ------------------------------------------------------------

    def GetFormValue(self, key, default=None, request=None, method=None):
        """
        Extract a form field from request. 
        Works with webob requests and simple dictionaries.
        
        returns the value or *default*
        """
        if not request:
            request = self.request
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
                    value = request.json_body.get(key)
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
            if value==None:
                return default
            return value
        if not len(value):
            return default
        elif len(value)==1:
            if value==None:
                return default
            return value[0]
        if value==None:
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
        #method = method or request.method
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


    def _LookupTemplate(self, tmplfile):
        if not self.viewModule or u":" in tmplfile:
            return tmplfile
        fn = self.viewModule.templates + u"/" + tmplfile
        try:
            if get_renderer(fn):
                return fn
        except ValueError:
            pass
        if not self.viewModule.parent:
            return tmplfile
        return u"%s/%s" % (self.viewModule.parent.templates, tmplfile)


    def mark(self):
        return time.time() - self._t

    def mark2(self):
        try:
            return u"""<div class="mark">%.04f</div>""" % (time.time() - self.request.environ.get("START_TIME", self._t))
        except:
            return u""

 

# Response utilities -------------------------------------------------

def SendResponse(data, mime="text/html", filename=None, raiseException=True):
    """
    See views.BaseView class function for docs
    """
    cd = None
    if filename:
        cd = 'attachment; filename=%s'%(filename)
    if raiseException:
        raise HTTPOk(content_type=mime, body=data, content_disposition=cd)
    return Response(content_type=mime, body=data, content_disposition=cd)


def Redirect(url, request, messages=None, slot="", raiseException=True):
    """
    See views.BaseView class function for docs
    """
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
    

def Relocate(url, request, messages=None, slot="", raiseException=True):
    """
    See views.BaseView class function for docs
    """
    if messages:
        if isinstance(messages, basestring):
            request.session.flash(messages, slot)
        else:
            for m in messages:
                request.session.flash(m, slot)
    headers = [('X-Relocate', str(url))]
    if hasattr(request.response, "headerlist"):
        headers += list(request.response.headerlist)
    request.response.headerlist = headers    
    if raiseException:
        raise HTTPOk(headers=headers, body_template="redirect "+url)
    return u""


def ResetFlashMessages(request, slot=""):
    """
    See views.BaseView class function for docs
    """
    while request.session.pop_flash(slot):
        continue
        
    
def AddHeader(request, name, value):
    """
    See views.BaseView class function for docs
    """
    headers = [(name, value)]
    if hasattr(request.response, "headerlist"):
        headers += list(request.response.headerlist)
    request.response.headerlist = headers    



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
        data = ""
        if useDefault:
            data = fieldConf["default"]
        if value != None:
            data = value
        if fieldConf.id in self.skipRender:
            return data

        def loadListItems(fld, context):
            if not context:
                return []
            pool_type = context.GetTypeID() 
            return helper.LoadListItems(fld, app=context.app, obj=context, pool_type=pool_type)
        
        # format for output
        fType = fieldConf["datatype"]

        # fomat settings
        fmt = fieldConf.settings.get("format")
        if fmt:
            if fmt=="bytesize":
                data = FormatBytesForDisplay(data)
                return data
            elif fmt=="image":
                tmpl = fieldConf.settings.get("path", u"")
                path = tmpl % {"data":data, "static": kw.get("static",u"")}
                data = """<img src="%(path)s" title="%(name)s">""" % {"path":path, "name": fieldConf.name}
                return data
        
        if fType == "bool":
            if data:
                data = _(u"Yes")
            else:
                data = _(u"No")

        elif fType == "string":
            if fieldConf.settings.get("relation") == u"userid":
                # load user name from database
                try:
                    udb = context.app.portal.userdb.root()
                    user = udb.GetUser(data, activeOnly=0)
                    if user:
                        data = user.GetTitle()
                except AttributeError:
                    pass

        elif fType == "text":
            data = data.replace(u"\r\n", u"\r\n<br>")

        elif fType == "date":
            if not isinstance(data, datetime):
                if not data:
                    return u""
                data = ConvertToDateTime(data)
            fmt = fieldConf.settings.get("strftime", u"%x")
            return data.strftime(fmt)

        elif fType in ("datetime", "timestamp"):
            fmt = fieldConf.settings.get("format")
            if not isinstance(data, datetime):
                if not data:
                    return u""
                data = ConvertToDateTime(data)
            # defaults
            fmt = fieldConf.settings.get("strftime")
            if not fmt:
                fmt = u"%x %H:%M"
                # hide hour and minutes if zero
                if data.hour==0 and data.minute==0 and data.second==0:
                    fmt = u"%x"
                elif fieldConf.settings.get("seconds"):
                    fmt = u"%x %X"
            return data.strftime(fmt)

        elif fType == "unit":
            if data == 0 or data == "0":
                return ""
            return data

        elif fType == "unitlist":
            if(type(data) == ListType):
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
                
        elif fType == "mselection" or fType == "mcheckboxes":
            values = []
            options = listItems or loadListItems(fieldConf, context)
            if not options:
                options = fieldConf.get("listItems")
                if hasattr(options, "__call__"):
                    options = options(fieldConf, self.context)

            if isinstance(data, basestring):
                data = tuple(value.split(u"\n"))
            for ref in data:
                if options:
                    for item in options:
                        if item["id"] == ref:
                            values.append(item["name"])
                else:
                    values.append(ref)
            delimiter = u", "
            if fieldConf.settings and u"delimiter" in fieldConf.settings:
                delimiter = fieldConf.settings[u"delimiter"]
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
