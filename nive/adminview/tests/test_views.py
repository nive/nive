# -*- coding: utf-8 -*-

from nive.adminview import view

from nive.tests.db_app import *
from nive.tests import __local

from pyramid import testing
from pyramid.renderers import render



class tViews(__local.DefaultTestCase):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.request = request
        self.request.content_type = ""
        self.config = testing.setUp(request=request)
        self.config.include('pyramid_chameleon')
        self._loadApp()
        self.portal = Portal()
        self.portal.Register(self.app, "nive")
        self.app.Register(view.configuration)
        self.app.Register(view.dbAdminConfiguration)
        self.app.Register("nive.components.reform")
        self.app.Startup(self.config)
        self.request.context = self.app
    

    def tearDown(self):
        self.app.Close()
        testing.tearDown()


    def test_basics(self):
        v = view.AdminBasics(context=self.app, request=self.request)
        self.assert_(v.GetAdminWidgets())
        self.assert_(v.RenderConf(view.configuration))
        self.assert_(v.RenderConf(view.dbAdminConfiguration))
        self.assert_(v.Format(view.configuration, view.configuration.id))
        self.assert_(v.Format(view.dbAdminConfiguration, view.configuration.id))
        self.assert_(v.AdministrationLinks(context=None))
        self.assert_(v.AdministrationLinks(context=self.app))


    def test_views(self):
        v = view.AdminView(context=self.app, request=self.request)
        v.__configuration__ = lambda: view.configuration
        v.view()
        self.assert_(v.index_tmpl())
        self.assert_(v.editbasics())
        self.assert_(v.editdatabase())
        self.assert_(v.editportal())
        self.assert_(v.tools())
        v.doc()


    def test_form(self):
        v = view.AdminBasics(context=self.app, request=self.request)
        form = view.ConfigurationForm(context=view.configuration, request=self.request, view=v, app=self.app)
        form.fields = (
            FieldConf(id=u"title",           datatype="string", size=255,  required=0, name=u"Application title"),
            FieldConf(id=u"description",     datatype="text",   size=5000, required=0, name=u"Application description"),
            FieldConf(id=u"workflowEnabled", datatype="bool",   size=2,    required=0, name=u"Enable workflow engine"),
            FieldConf(id=u"fulltextIndex",   datatype="bool",   size=2,    required=0, name=u"Enable fulltext index"),
            FieldConf(id=u"frontendCodepage",datatype="string", size=10,   required=1, name=u"Codepage used in html frontend"),
        )
        form.Setup()
        self.request.POST = {"name": "testuser", "email": "testuser@domain.net"}
        self.request.GET = {}

        self.assert_(form.Start(None))
        self.assert_(form.Update(None))
             


class tTemplates(__local.DefaultTestCase):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.request = request
        self.request.content_type = ""
        self.config = testing.setUp(request=request)
        self.config.include('pyramid_chameleon')
        self._loadApp()
        self.portal = Portal()
        self.portal.Register(self.app, "nive")
        self.app.Register(view.configuration)
        self.app.Register(view.dbAdminConfiguration)
        self.app.Register("nive.components.reform")
        self.app.Startup(self.config)
        self.request.context = self.app

    def tearDown(self):
        self.app.Close()
        testing.tearDown()

    def test_templates(self):
        v = view.AdminView(context=self.app, request=self.request)
        v.__configuration__ = lambda: view.configuration
        vrender = {"context":self.app, "view":v, "request": self.request}

        values = v.editbasics()
        values.update(vrender)
        render("nive.adminview:form.pt", values)
        
        values = v.tools()
        values.update(vrender)
        render("nive.adminview:tools.pt", values)
        
        render("nive.adminview:modules.pt", vrender)
        render("nive.adminview:root.pt", vrender)
        render("nive.adminview:views.pt", vrender)
        render("nive.adminview:help.pt", values)

    

