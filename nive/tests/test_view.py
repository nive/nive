
import time
import unittest
from types import DictType

from nive.definitions import *
from nive.security import *
from nive.tests import db_app
from nive.views import *
from nive.helper import DecorateViewClassWithViewModuleConf
from nive.tests import __local

from pyramid.response import Response
from pyramid.request import Request
from pyramid import testing

def getRequest():
    r = Request({"PATH_INFO": "http://aaa.com/test?key=123", "wsgi.url_scheme":"http", "SERVER_NAME": "testserver.de","SERVER_PORT":80, "REQUEST_METHOD": "GET"})
    r.subpath = ["file1.txt"]
    r.context = None
    return r

class viewModule(object):
    template = "nive.tests:index.pt"
    templates = u"nive.tests:"
    parent = None
    static = u"nive.tests:"
    assets = (("jquery.js", "nive.adminview:static/mods/jquery.min.js"), ("another.css", "nive.adminview:static/adminview.css"))

class viewTest_db:

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        self.config.include('pyramid_chameleon')
        self.request._LOCALE_ = "en"
        self.request.subpath = ["file1.txt"]
        self.request.context = None
        self.request.content_type = None
        self._loadApp(["nive.adminview.view"])
        self.app.Startup(self.config)
        #self.request = getRequest()
        user = User(u"test")
        r = self.app.root()
        self.context = db_app.createObj1(r)
        self.context2 = db_app.createObj2(r)
        self.context2.StoreFile("file1", db_app.file2_1, user=user)
        self.context2.StoreFile("file2", db_app.file2_2, user=user)

    def tearDown(self):
        user = User(u"test")
        r = self.app.root()
        r.Delete(self.context.id, user=user)
        r.Delete(self.context2.id, user=user)
        testing.tearDown()
        pass
    

    def test_conf(self):
        view = BaseView(self.context2, self.request)
        self.assertFalse(view.configuration)
        conf = Conf(id="test")
        newcls = DecorateViewClassWithViewModuleConf(conf, BaseView)
        view = newcls(self.context2, self.request)
        self.assert_(view.configuration.id=="test")

    def test_excp(self):
        def rtest():
            raise Unauthorized, "test"
        self.assertRaises(Unauthorized, rtest)
    

    def test_urls(self):
        view = BaseView(self.context2, self.request)

        #urls
        self.assert_(view.Url())
        self.assert_(view.Url(self.context))
        self.assert_(view.FolderUrl())
        self.assert_(view.FolderUrl(self.context))
        self.assert_(view.FileUrl("file1"))
        self.assert_(view.FileUrl("file1", self.context2))
        self.assert_(view.PageUrl())
        self.assert_(view.PageUrl(self.context, usePageLink=1))
        self.assert_(view.PageUrl(addAnchor=True))
        self.assert_(view.PageUrl(self.context, addAnchor=True))
        self.assert_(view.CurrentUrl(retainUrlParams=False))
        self.assert_(view.CurrentUrl(retainUrlParams=True))

        self.assertRaises(ValueError, view.StaticUrl, "file.js")
        self.assertRaises(ValueError, view.StaticUrl, "myproject:file.js")
        self.assert_(view.StaticUrl("http://file.js"))
        self.assert_(view.StaticUrl("/file.js"))

        urls = ["page_url", "obj_url", "obj_folder_url", "parent_url"]
        for url in urls:
            self.assert_(view.ResolveUrl(url, context=None))
            self.assert_(view.ResolveUrl(url, context=self.context2))
        self.assertFalse(view.ResolveUrl("", context=None))
        
        self.assert_(view.ResolveLink(str(self.context.id))!=str(self.context.id))
        self.assert_(view.ResolveLink("none")=="none")

        self.request.virtual_root = self.app.root()
        self.assert_(view.PageUrl(self.context))
        self.assert_(view.Url(self.context))
        self.assert_(view.PageUrl(self.app.root()))
        self.assert_(view.Url(self.app.root()))



    
    def test_http(self):
        view = BaseView(self.context2, self.request)
        
        self.assertRaises(HTTPFound, view.Redirect, "nowhere", messages=None, slot="")
        self.assertRaises(HTTPFound, view.Redirect, "nowhere", messages=[u"aaa",u"bbb"], slot="")
        self.assertRaises(HTTPFound, view.Redirect, "nowhere", messages=[u"aaa",u"bbb"], slot="test")
        self.assertRaises(ExceptionalResponse, view.Relocate, "nowhere", messages=None, slot="", raiseException=True)
        self.assertRaises(ExceptionalResponse, view.Relocate, "nowhere", messages=[u"aaa",u"bbb"], slot="", raiseException=True)
        self.assertRaises(ExceptionalResponse, view.Relocate, "nowhere", messages=[u"aaa",u"bbb"], slot="test", raiseException=True)
        self.assert_(view.Relocate("nowhere", messages=[u"aaa",u"bbb"], slot="test", raiseException=False)!=u"")
        view.ResetFlashMessages(slot="")
        view.ResetFlashMessages(slot="test")
        view.AddHeader("name", "value")


    def test_send(self):
        view = BaseView(self.context2, self.request)
        self.assert_(view.SendResponse("the response", mime="text/html", raiseException=False, filename=None))
        self.assert_(view.SendResponse("the response", mime="text/html", raiseException=False, filename="file.html", headers=[("X-Result", "true")]))
        self.assertRaises(ExceptionalResponse, view.SendResponse, "the response", mime="text/html", raiseException=True, filename="file.html", headers=[("X-Result", "true")])


    def test_files(self):
        view = BaseView(self.context2, self.request)
        #files
        view.File()
        file = self.context2.GetFile("file1")
        view.SendFile(file)

    
    def test_render(self):
        view = BaseView(self.context2, self.request)
        self.assert_(view.index_tmpl(path=None)==None)
        self.assert_(view.index_tmpl(path="nive.tests:index.pt"))
        
        view._c_vm=viewModule()
        self.assert_(view.index_tmpl(path=None))
        
        self.assertRaises(ValueError, view.DefaultTemplateRenderer, {}, templatename = None)
        view.DefaultTemplateRenderer({}, templatename = "test.pt")

        #views
        view.RenderView(self.context, name="", secure=True, raiseUnauthorized=False)
        view.RenderView(self.context, name="test", secure=False, raiseUnauthorized=True)
        view.RenderView(self.context, name="", secure=True, raiseUnauthorized=False, codepage="utf-8")
        view.IsPage(self.context)
        view.IsPage()
        view.tmpl()

    
    def test_cache(self):
        view = BaseView(self.context2, self.request)
        # header
        view.CacheHeader(Response(), user=None)
        view.NoCache(Response(), user=None)
        view.Modified(Response(), user=None)
        user = view.User()
        view.CacheHeader(Response(), user=user)
        view.NoCache(Response(), user=user)
        view.Modified(Response(), user=user)
        

    def test_user(self):
        view = BaseView(self.context2, self.request)
        #users
        view.user
        view.User()
        view.UserName()
        view.Allowed("test", context=None)
        view.Allowed("test", context=self.context)
        view.InGroups([])
        

    def test_forms(self):
        view = BaseView(self.context2, self.request)
        #values
        self.assert_(view.GetFormValue("test", default=123, method=None)==123)
        self.assert_(view.GetFormValue("test", default=123, method="GET")==123)
        self.assert_(view.GetFormValue("test", default=111, method="POST")==111)
        view.GetFormValues()
        view.GetFormValues(method="POST")
        
        self.assert_(view.FmtURLParam(**{u"aaa":123,u"bbb":u"qwertz"}))
        self.assert_(view.FmtFormParam(**{u"aaa":123,u"bbb":u"qwertz"}))



    def test_renderer(self):
        view2 = BaseView(self.context, self.request)
        #render fields
        self.assert_(view2.RenderField("ftext"))
        self.assert_(view2.RenderField("fnumber"))
        self.assert_(view2.RenderField("fdate"))
        self.assert_(view2.RenderField("flist"))
        self.assert_(view2.RenderField("pool_type"))
        self.assert_(view2.RenderField("pool_category"))
        self.assert_(view2.HtmlTitle()=="")
        self.assert_(view2.FmtTextAsHTML("text"))
        self.assert_(view2.FmtDateText("2008/06/23 16:55", language=None))
        self.assert_(view2.FmtDateNumbers( "2008/06/23 16:55", language=None))
        self.assert_(view2.FmtSeconds(2584))
        self.assert_(view2.FmtBytes(135786))


    def test_assets(self):
        view2 = BaseView(self.context, self.request)
        view2._c_vm=viewModule()
        self.assert_(view2.Assets())
        self.assert_(view2.Assets(ignore="jquery.js"))
        self.assert_(view2.Assets(assets=(("jquery.js", "nive.adminview:static/mods/jquery.min.js"),)))
        self.assertFalse(view2.Assets(assets=[]))
        self.assert_(view2.Assets(types="js").find(".css")==-1)
        self.assert_(view2.Assets(types="css").find(".js")==-1)
        
    
    def test_htmltag(self):
        view2 = BaseView(self.context, self.request)
        self.assert_(view2.FmtTag("div"))
        self.assert_(view2.FmtTag("div")==u"<div></div>", view2.FmtTag("div"))
        self.assert_(view2.FmtTag("div", id=0)==u"""<div id="0"></div>""")
        self.assert_(view2.FmtTag("div", closeTag=None, id=0)==u"""<div id="0">""")
        self.assert_(view2.FmtTag("div", closeTag="inline", id=0)==u"""<div id="0"/>""")
        



class viewTest_db_sqlite(viewTest_db, __local.SqliteTestCase):
    """
    see tests.__local
    """

class viewTest_db_mysql(viewTest_db, __local.MySqlTestCase):
    """
    see tests.__local
    """

class viewTest_db_pg(viewTest_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """
