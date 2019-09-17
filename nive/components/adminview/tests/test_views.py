# -*- coding: utf-8 -*-

from nive.components.adminview import view

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
        self._closeApp()
        testing.tearDown()


    def test_basics(self):
        v = view.AdminBasics(context=self.app, request=self.request)
        self.assertTrue(v.GetAdminWidgets())
        self.assertTrue(v.RenderConf(view.configuration))
        self.assertTrue(v.RenderConf(view.dbAdminConfiguration))
        self.assertTrue(v.Format(view.configuration, view.configuration.id))
        self.assertTrue(v.Format(view.dbAdminConfiguration, view.configuration.id))
        self.assertTrue(v.AdministrationLinks(context=None))
        self.assertTrue(v.AdministrationLinks(context=self.app))


    def test_views(self):
        v = view.AdminView(context=self.app, request=self.request)
        v.__configuration__ = lambda: view.configuration
        v.view()
        self.assertTrue(v.index_tmpl())
        self.assertTrue(v.editbasics())
        self.assertTrue(v.editdatabase())
        self.assertTrue(v.editportal())
        self.assertTrue(v.tools())
        v.doc()


    def test_form(self):
        v = view.AdminBasics(context=self.app, request=self.request)
        form = view.ConfigurationForm(context=view.configuration, request=self.request, view=v, app=self.app)
        form.fields = (
            FieldConf(id="title",           datatype="string", size=255,  required=0, name="Application title"),
            FieldConf(id="description",     datatype="text",   size=5000, required=0, name="Application description"),
            FieldConf(id="workflowEnabled", datatype="bool",   size=2,    required=0, name="Enable workflow engine"),
            FieldConf(id="fulltextIndex",   datatype="bool",   size=2,    required=0, name="Enable fulltext index"),
            FieldConf(id="frontendCodepage",datatype="string", size=10,   required=1, name="Codepage used in html frontend"),
        )
        form.Setup()
        self.request.POST = {"name": "testuser", "email": "testuser@domain.net"}
        self.request.GET = {}

        self.assertTrue(form.Start(None))
        self.assertTrue(form.Update(None))
             


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
        render("nive.components.adminview:form.pt", values)
        
        values = v.tools()
        values.update(vrender)
        render("nive.components.adminview:tools.pt", values)
        
        render("nive.components.adminview:modules.pt", vrender)
        render("nive.components.adminview:root.pt", vrender)
        render("nive.components.adminview:views.pt", vrender)
        render("nive.components.adminview:help.pt", values)

    

