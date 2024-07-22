# -*- coding: utf-8 -*-

import unittest

from nive.security import User, DummySecurityPolicy
from nive.components.webapi.tests import __local

from pyramid import testing



class tWebapiDispatch_db(object):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.request = request
        self.config = testing.setUp(request=request)
        self.config.registry.registerUtility(DummySecurityPolicy("test"))
        self._loadApp()
        self.app.Startup(self.config)
        self.root = self.app.root
        user = User("test")
        user.groups.append("group:manager")
        self.request.context = self.root
        self.remove = []

    def tearDown(self):
        user = User("test")
        for r in self.remove:
            self.root.Delete(r, user)
        self.app.Close()
        testing.tearDown()



    def test_newUnsecured(self):
        user = User("test")
        user.groups.append("group:manager")

        # add success
        # single item
        param = {"pool_type": "bookmark", "link": "the link", "comment": "some text"}
        result, stat = self.root.dispatch("newItem", **param)
        self.assertTrue(len(result["result"])==1)
        self.root.Delete(result["result"][0], user=user)
        # single item list
        param = {"items": [{"pool_type": "bookmark", "link": "the link", "comment": "some text"}]}
        result, stat = self.root.dispatch("newItem", **param)
        self.assertTrue(len(result["result"])==1)
        self.root.Delete(result["result"][0], user=user)
        # multiple items list
        param = {"items": [{"pool_type": "bookmark", "link": "the link 1", "comment": "some text"},
                                      {"pool_type": "bookmark", "link": "the link 2", "comment": "some text"},
                                      {"pool_type": "bookmark", "link": "the link 3", "comment": "some text"}]}
        result,stat = self.root.dispatch("newItem", **param)
        self.assertTrue(len(result["result"])==3)
        self.root.Delete(result["result"][0], user=user)
        self.root.Delete(result["result"][1], user=user)
        self.root.Delete(result["result"][2], user=user)

        # add failure
        # no type
        param = {"pool_type": "nonono", "link": "the link", "comment": "some text"}
        result,stat = self.root.dispatch("newItem", **param)
        self.assertTrue(len(result["result"])==0)
        param = {"link": "the link", "comment": "some text"}
        result,stat = self.root.dispatch("newItem", **param)
        self.assertTrue(len(result["result"])==0)
        # validatio error
        param = {"pool_type": "track", "number": "the link", "something": "some text"}
        result,stat = self.root.dispatch("newItem", **param)
        self.assertTrue(len(result["result"])==0)
        # single item list
        param = {"items": [{"pool_type": "nonono", "link": "the link", "comment": "some text"}]}
        result,stat = self.root.dispatch("newItem", **param)
        self.assertTrue(len(result["result"])==0)
        param = {"items": [{"link": "the link", "comment": "some text"}]}
        result,stat = self.root.dispatch("newItem", **param)
        self.assertTrue(len(result["result"])==0)
        # multiple items list
        param = {"items": [{"pool_type": "bookmark", "link": "the link 1", "comment": "some text"},
                           {"link": "the link 2", "comment": "some text"},
                           {"pool_type": "bookmark", "link": "the link 3", "comment": "some text"}]}
        result,stat = self.root.dispatch("newItem", **param)
        self.assertTrue(len(result["result"])==2)
        
        # to many
        self.app.configuration.unlock()
        self.app.configuration.maxStoreItems = 1
        param = {"items": [{"pool_type": "bookmark", "link": "the link 1", "comment": "some text"},
                           {"link": "the link 2", "comment": "some text"},
                           {"pool_type": "bookmark", "link": "the link 3", "comment": "some text"}]}
        result,stat = self.root.dispatch("newItem", **param)
        self.app.configuration.maxStoreItems = 20
        self.app.configuration.lock()
        self.assertTrue(len(result["result"])==0)
        
        
        
    def test_newSecured(self):
        user = User("test")
        user.groups.append("group:manager")

        # add success
        # single item
        param = {"pool_type": "bookmark", "link": "the link", "comment": "some text"}
        result, stat = self.root.dispatch("newItem", True, self.request, **param)
        self.assertTrue(len(result["result"])==1)
        self.root.Delete(result["result"][0], user=user)
        
        

class tWebapiDispatch_db_sqlite(tWebapiDispatch_db, __local.SqliteTestCase):
    """
    see tests.__local
    """

class tWebapiDispatch_db_mysql(tWebapiDispatch_db, __local.MySqlTestCase):
    """
    see tests.__local
    """
    
class tWebapiDispatch_db_pg(tWebapiDispatch_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """



