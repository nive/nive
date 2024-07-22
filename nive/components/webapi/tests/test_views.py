# -*- coding: utf-8 -*-

import unittest

from nive.definitions import Conf, ConfigurationError
from nive.security import DummySecurityPolicy
from nive.security import User
from nive.views import ExceptionalResponse
from nive.components.webapi.view import ExtractJSValue, DeserializeItems, APIv1

from nive.components.webapi.tests.db_app import create_bookmark, create_track
from nive.components.webapi.tests import __local

from pyramid import testing



class viewModule(object):
    template = "nive.tests:index.pt"
    templates = "nive.tests:"
    parent = None
    views = []
    static = "nive.components.reform:"
    assets = (("jquery.js", "nive.components.adminview:static/mods/jquery.min.js"), ("another.css", "nive.components.adminview:static/adminview.css"))
    def get(self, key):
        return None

class tWebapi_db(object):

    def setUp(self):
        request = testing.DummyRequest()
        request._LOCALE_ = "en"
        self.request = request
        self.request.content_type = ""
        self.request.method = "POST"
        self.request.environ = dict(dummyUser="username", dummyPrincipals=["username", "system.Authenticated", "group:admin"])
        self.config = testing.setUp(request=request)
        self.config.registry.registerUtility(DummySecurityPolicy("test"))
        self.config.include('pyramid_chameleon')
        self._loadApp()
        self.app.Startup(self.config)
        self.root = self.app.root
        user = User("test")
        user.groups.append("group:manager")
        self.request.context = self.root
        self.remove = []

    def tearDown(self):
        user = User("test")
        for r in self.root.GetObjsList(fields=["id"]):
            self.root.Delete(r["id"], user)
        self.app.Close()
        testing.tearDown()


    def test_functions(self):
        values = {"key1":"", "key2":"null", "key3":"undefined", "key4":"123", "key5":"123.456",
                  "key6":"false", "key7":"true", "key8": "something"}
        self.assertTrue(ExtractJSValue(values, "key1", "default", "string")=="default")
        self.assertTrue(ExtractJSValue(values, "key2", "default", "string")=="default")
        self.assertTrue(ExtractJSValue(values, "key3", "default", "string")=="default")
        self.assertTrue(ExtractJSValue(values, "key4", "default", "int")==123)
        self.assertTrue(ExtractJSValue(values, "key5", "default", "float")==123.456)
        self.assertTrue(ExtractJSValue(values, "key6", True, "bool")==False)
        self.assertTrue(ExtractJSValue(values, "key7", False, "bool")==True)
        self.assertTrue(ExtractJSValue(values, "keyx", True, "bool")==True)
        self.assertTrue(ExtractJSValue(values, "key8", False, "none")=="something")

        
    def test_deserialize(self):
        user = User("test")
        view = APIv1(self.root, self.request)
        r = self.root
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        items = [o1]
        values = DeserializeItems(view, items, ("comment", "link"))
        self.assertTrue(len(values)==1)
        values = DeserializeItems(view, items, o1.configuration)
        self.assertTrue(len(values)==1)
        values = DeserializeItems(view, items, {"bookmark": ("comment", "link")})
        self.assertTrue(len(values)==1)
        values = DeserializeItems(view, items, {"default__": ("comment", "link")})
        self.assertTrue(len(values)==1)

        values = DeserializeItems(view, items, {"default__": ("comment", "link")}, render=("comment","link"))
        self.assertTrue(len(values)==1)

        items = o1
        values = DeserializeItems(view, items, ("comment", "link"))
        self.assertTrue(len(values)==1)


    def test_new(self):
        view = APIv1(self.root, self.request)
        user = User("test")
        user.groups.append("group:manager")

        # add success
        # single item
        self.request.POST = {"pool_type": "bookmark", "link": "the link", "comment": "some text"}
        result = view.newItem()
        self.assertTrue(len(result["result"])==1)
        self.root.Delete(result["result"][0], user=user)
        # single item list
        self.request.POST = {"items": [{"pool_type": "bookmark", "link": "the link", "comment": "some text"}]}
        result = view.newItem()
        self.assertTrue(len(result["result"])==1)
        self.root.Delete(result["result"][0], user=user)
        # multiple items list
        self.request.POST = {"items": [{"pool_type": "bookmark", "link": "the link 1", "comment": "some text"},
                                       {"pool_type": "bookmark", "link": "the link 2", "comment": "some text"},
                                       {"pool_type": "bookmark", "link": "the link 3", "comment": "some text"}]}
        result = view.newItem()
        self.assertTrue(len(result["result"])==3)
        self.root.Delete(result["result"][0], user=user)
        self.root.Delete(result["result"][1], user=user)
        self.root.Delete(result["result"][2], user=user)

        # add failure
        # no type
        self.request.POST = {"pool_type": "nonono", "link": "the link", "comment": "some text"}
        result = view.newItem()
        self.assertTrue(len(result["result"])==0)
        self.request.POST = {"link": "the link", "comment": "some text"}
        result = view.newItem()
        self.assertTrue(len(result["result"])==0)
        # validatio error
        self.request.POST = {"pool_type": "track", "number": "the link", "something": "some text"}
        result = view.newItem()
        self.assertTrue(len(result["result"])==0)
        # single item list
        self.request.POST = {"items": [{"pool_type": "nonono", "link": "the link", "comment": "some text"}]}
        result = view.newItem()
        self.assertTrue(len(result["result"])==0)
        self.request.POST = {"items": [{"link": "the link", "comment": "some text"}]}
        result = view.newItem()
        self.assertTrue(len(result["result"])==0)
        # multiple items list
        self.request.POST = {"items": [{"pool_type": "bookmark", "link": "the link 1", "comment": "some text"},
                                       {"link": "the link 2", "comment": "some text"},
                                       {"pool_type": "bookmark", "link": "the link 3", "comment": "some text"}]}
        result = view.newItem()
        self.assertTrue(len(result["result"])==2)
        
        # to many
        self.app.configuration.unlock()
        self.app.configuration.maxStoreItems = 2
        self.request.POST = {"items": [{"pool_type": "bookmark", "link": "the link 1", "comment": "some text"},
                                                  {"link": "the link 2", "comment": "some text"},
                                                  {"pool_type": "bookmark", "link": "the link 3", "comment": "some text"}]}
        result = view.newItem()
        self.app.configuration.maxStoreItems = 20
        self.app.configuration.lock()
        self.assertTrue(len(result["result"])==0)
        
        
    def test_get(self):
        view = APIv1(self.root, self.request)
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        o2 = create_track(r, user)
        self.remove.append(o2.id)
        o3 = create_bookmark(r, user)
        self.remove.append(o3.id)
        
        # get single
        self.request.POST = {"id": str(o1.id)}
        result = view.getItem()
        self.assertTrue(len(result)==1)
        self.assertTrue(result[0]["link"]=="the link")
        
        # get three
        self.request.POST = {"id": [o1.id,o2.id,o3.id]}
        result = view.getItem()
        self.assertTrue(len(result)==3)
        self.assertTrue(result[0]["link"]=="the link")
        self.assertTrue(result[1]["url"]=="the url")
        self.assertTrue(result[2]["link"]=="the link")
        
        # get two rigth
        self.root.Delete(o3.id, user=user)
        self.request.POST = {"id": [o1.id,o2.id,o3.id]}
        result = view.getItem()
        self.assertTrue(len(result)==2)
        self.assertTrue(result[0]["link"]=="the link")
        self.assertTrue(result[1]["url"]=="the url")

        # get none
        self.request.POST = {"id": ""}
        result = view.getItem()
        self.assertTrue(result.get("error"))
        
        self.request.POST = {"id": "ababab"}
        result = view.getItem()
        self.assertTrue(result.get("error"))


    def test_set(self):
        view = APIv1(self.root, self.request)
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        o2 = create_track(r, user)
        self.remove.append(o2.id)
        o3 = create_bookmark(r, user)
        self.remove.append(o3.id)
        
        # update single
        self.request.POST = {"id": str(o1.id), "link": "the link new", "comment": "some text"}
        result = view.setItem()
        self.assertTrue(len(result)==1)
        o = self.root.GetObj(o1.id)
        self.assertTrue(o.data.link=="the link new")
        
        # update single
        self.request.POST = {"items": [{"id": str(o1.id), "link": "the link", "comment": "some text"}]}
        result = view.setItem()
        self.assertTrue(len(result["result"])==1)
        o = self.root.GetObj(result["result"][0])
        self.assertTrue(o.data.link=="the link")
        
        # update multiple
        self.request.POST = {"items": [
                             {"id": str(o1.id), "link": "the link new", "comment": "some text"},
                             {"id": str(o2.id), "url": "the url new"},
                             {"id": str(o3.id), "link": "the link new", "comment": "some text"},
                             ]}
        result = view.setItem()
        self.assertTrue(len(result["result"])==3)
        o = self.root.GetObj(result["result"][0])
        self.assertTrue(o.data.link=="the link new")
        o = self.root.GetObj(result["result"][1])
        self.assertTrue(o.data.url=="the url new")
        o = self.root.GetObj(result["result"][2])
        self.assertTrue(o.data.link=="the link new")

        # failures
        # update single
        self.request.POST = {"id": str(9999999), "link": "the link new", "comment": "some text"}
        result = view.setItem()
        self.assertTrue(len(result["result"])==0)
        
        # update single
        self.request.POST = {"items": [{"link": "the link", "comment": "some text"}]}
        result = view.setItem()
        self.assertTrue(len(result["result"])==0)
        
        # not found
        self.request.POST = {"items": [
                             {"id": str(o1.id), "link": "the link new", "comment": "some text"},
                             {"id": "999999999", "url": "the url new"},
                             {"id": str(o3.id), "link": "the link new", "comment": "some text"},
                             ]}
        result = view.setItem()
        self.assertTrue(len(result["result"])==2)
        # no id
        self.request.POST = {"items": [
                             {"id": str(o1.id), "link": "the link new", "comment": "some text"},
                             {"url": "the url new"},
                             {"id": str(o3.id), "link": "the link new", "comment": "some text"},
                             ]}
        result = view.setItem()
        self.assertTrue(len(result["result"])==2)
        # validation error
        self.request.POST = {"items": [
                             {"id": str(o1.id), "link": "the link new", "comment": "some text"},
                             {"id": str(o2.id), "number": 444},
                             {"id": str(o3.id), "link": "the link new", "comment": "some text"},
                             ]}
        result = view.setItem()
        self.assertTrue(len(result["result"])==2)


    def test_delete(self):
        view = APIv1(self.root, self.request)
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        o2 = create_track(r, user)
        self.remove.append(o2.id)
        o3 = create_bookmark(r, user)
        self.remove.append(o3.id)
        
        # delete single
        self.request.POST = {"id": str(o1.id)}
        self.request.method = "POST"
        result = view.deleteItem()
        self.assertTrue(len(result["result"])==1)
        o = self.root.GetObj(o1.id)
        self.assertTrue(o==None)

        # delete two
        self.request.POST = {"id": [str(o2.id),str(o3.id)]}
        result = view.deleteItem()
        self.assertTrue(len(result["result"])==2)
        o = self.root.GetObj(o2.id)
        self.assertTrue(o==None)
        o = self.root.GetObj(o3.id)
        self.assertTrue(o==None)

        # delete error
        self.request.POST = {"id": 9999999}
        result = view.deleteItem()
        self.assertTrue(len(result["result"])==0)
        self.request.POST = {"idno": 9999999}
        result = view.deleteItem()
        self.assertTrue(len(result["result"])==0)

        # delete json err
        self.request.POST = {"id": "oh no"}
        result = view.deleteItem()
        self.assertTrue(len(result["result"])==0)
        
        
    def test_itemcontext(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        o2 = create_track(r, user)
        self.remove.append(o2.id)
        
        self.request.context = o1
        view = APIv1(o1, self.request)
        result = view.getItem()
        self.assertTrue(result)
        self.assertTrue(result["link"]=="the link")

        self.request.context = o2
        view = APIv1(o2, self.request)
        result = view.getItem()
        self.assertTrue(result)
        self.assertTrue(result["url"]=="the url")


        self.request.context = o1
        view = APIv1(o1, self.request)
        self.request.POST = {"link": "the link new", "comment": "some text"}
        result = view.setItem()
        o = self.root.GetObj(o1.id)
        self.assertTrue(o.data.link=="the link new")

        self.request.context = o2
        view = APIv1(o2, self.request)
        self.request.POST = {"number": 444}
        result = view.setItem()
        self.assertTrue(result.get("error"))
        o = self.root.GetObj(o2.id)
        self.assertTrue(o.data.number==123)
   
   
    def test_listings(self):
        user = User("test")
        user.groups.append("group:manager")
        view = APIv1(self.root, self.request)
        r = self.root
        objs=r.GetObjs()
        for o in objs:
            r.Delete(o.id, obj=o, user=user)
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        o2 = create_track(r, user)
        self.remove.append(o2.id)
        o3 = create_bookmark(r, user)
        self.remove.append(o3.id)
        o4 = create_track(r, user)
        self.remove.append(o4.id)

        # testing listings and parameter
        self.request.POST = {}
        result = view.listItems()
        self.assertTrue(len(result["items"])==4)

        self.request.POST = {"start":2}
        result = view.listItems()
        self.assertTrue(result["start"]==2)
        self.assertTrue(len(result["items"])==2)

        self.request.POST = {"pool_type": "track"}
        result = view.listItems()
        self.assertTrue(len(result["items"])==2)

        self.request.POST = {"sort":"pool_change", "order":"<", "size":2}
        result = view.listItems()
        self.assertTrue(len(result["items"])==2)

        self.request.POST = {"sort":"id", "order":"<", "size":2}
        result = view.listItems()
        self.assertTrue(len(result["items"])==2)
        ids = result["items"]
        self.request.POST = {"sort":"id", "order":">", "size":2}
        result = view.listItems()
        self.assertTrue(result["items"]!=ids)
        
        self.request.POST = {"sort":"id", "order":"<", "size":4}
        result = view.listItems()
        ids = result["items"]
        self.request.POST = {"sort":"id", "order":">", "size":4}
        result = view.listItems()
        self.assertTrue(ids[0]==result["items"][3])
        self.assertTrue(ids[1]==result["items"][2])
        
        
    def test_listingsContainer(self):
        user = User("test")
        user.groups.append("group:manager")
        view = APIv1(self.root, self.request)
        r = self.root
        objs=r.GetObjs()
        for o in objs:
            r.Delete(o.id, obj=o, user=user)
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        o3 = create_bookmark(r, user)
        self.remove.append(o3.id)
        
        o2 = create_bookmark(o1, user)
        create_track(o1, user)
        create_track(o1, user)
        create_track(o3, user)

        # testing listings and parameter
        self.request.POST = {}
        result = view.listItems()
        self.assertTrue(len(result["items"])==2)

        view = APIv1(o1, self.request)
        result = view.listItems()
        self.assertTrue(len(result["items"])==3)

        view = APIv1(o1, self.request)
        result = view.listItems()
        self.assertTrue(len(result["items"])==3)

        view = APIv1(o2, self.request)
        result = view.listItems()
        self.assertTrue(len(result["items"])==0)

        view = APIv1(o1, self.request)
        self.request.POST = {"pool_type": "track"}
        result = view.listItems()
        self.assertTrue(len(result["items"])==2)

        
    def test_listingsFailure(self):
        user = User("test")
        user.groups.append("group:manager")
        view = APIv1(self.root, self.request)
        r = self.root

        # testing listings and parameter
        self.request.POST = {"start": "wrong number"}
        result = view.listItems()
        self.assertTrue(result["error"])
        self.assertTrue(len(result["items"])==0)

        # testing listings and parameter
        self.request.POST = {"size": "wrong number"}
        result = view.listItems()
        self.assertTrue(result["error"])
        self.assertTrue(len(result["items"])==0)


    def test_searchConf(self):
        user = User("test")
        user.groups.append("group:manager")
        view = APIv1(self.root, self.request)
        r = self.root
        objs=r.GetObjs()
        for o in objs:
            r.Delete(o.id, obj=o, user=user)
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        o3 = create_bookmark(r, user)
        self.remove.append(o3.id)
        
        o2 = create_bookmark(o1, user)
        create_track(o1, user)
        create_track(o1, user)
        create_track(o3, user)

        self.request.POST = {}
        result = view.search()
        self.assertTrue(len(result["items"])==6, result)

        self.request.POST = {"profile":"bookmarks"}
        result = view.search()
        self.assertTrue(len(result["items"])==3)
    
        # container activated
        self.request.POST = {"profile":"tracks"}
        result = view.search()
        self.assertTrue(len(result["items"])==0, result)

        view = APIv1(o1, self.request)
        self.request.POST = {"profile":"tracks"}
        result = view.search()
        self.assertTrue(len(result["items"])==2, result)
    
        self.request.POST = {"size":2}
        result = view.search()
        self.assertTrue(len(result["items"])==2)
        self.assertTrue(result["size"]==2)
        self.assertTrue(result["start"]==1,result)
        self.assertTrue(result["total"]==6)

        self.request.POST = {"size":2,"start":3}
        result = view.search()
        self.assertTrue(len(result["items"])==2)
        self.assertTrue(result["size"]==2)
        self.assertTrue(result["start"]==3,result)
        self.assertTrue(result["total"]==6)

        self.request.POST = {"size":2,"start":6}
        result = view.search()
        self.assertTrue(len(result["items"])==1, result)
        self.assertTrue(result["size"]==1)
        self.assertTrue(result["start"]==6)
        self.assertTrue(result["total"]==6,result)

    
    def test_searchParam(self):
        user = User("test")
        user.groups.append("group:manager")
        view = APIv1(self.root, self.request)
        r = self.root
        objs=r.GetObjs()
        for o in objs:
            r.Delete(o.id, obj=o, user=user)
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        o3 = create_bookmark(r, user)
        self.remove.append(o3.id)

        o2 = create_bookmark(o1, user)
        create_track(o1, user)
        create_track(o1, user)
        create_track(o3, user)

        self.request.POST = {}

        profile = {
            "container": False,
            "fields": ["id", "pool_changedby"],
            "parameter": {}
        }
        view.GetViewConf = lambda: Conf(settings=profile)
        result = view.search()
        self.assertTrue(len(result["items"])==6)

        profile = {
            "container": False,
            "fields": ["id", "pool_changedby"],
            "parameter": {"pool_changedby":"test"},
            "operators": {"pool_changedby":"="}
        }
        view.GetViewConf = lambda: Conf(settings=profile)
        result = view.search()
        self.assertTrue(len(result["items"])==6)

        profile = {
            "container": False,
            "fields": ["id", "pool_changedby"],
            "parameter": lambda c, r: {"pool_changedby":"test"},
            "operators": {"pool_changedby":"="}
        }
        view.GetViewConf = lambda: Conf(settings=profile)
        result = view.search()
        self.assertTrue(len(result["items"])==6)

        profile = {
            "container": False,
            "fields": ["id", "pool_changedby"],
            "parameter": {"pool_changedby":"test"},
            "operators": {"pool_changedby":"<>"}
        }
        view.GetViewConf = lambda: Conf(settings=profile)
        result = view.search()
        self.assertTrue(len(result["items"])==0)

        profile = {
            "container": False,
            "fields": ["pool_type"],
            "parameter": {"pool_changedby":"test"},
            "operators": {"pool_changedby":"="},
            "advanced": {"groupby": "pool_type"}
        }
        view.GetViewConf = lambda: Conf(settings=profile)
        result = view.search()
        self.assertTrue(len(result["items"])==2)

    
    def test_searchFailure(self):
        user = User("test")
        user.groups.append("group:manager")
        view = APIv1(self.root, self.request)
        r = self.root

        # testing listings and parameter
        self.request.POST = {"start": "wrong number"}
        result = view.search()
        self.assertTrue(result["error"])
        self.assertTrue(len(result["items"])==0)

        # testing listings and parameter
        self.request.POST = {"size": "wrong number"}
        result = view.search()
        self.assertTrue(result["error"])
        self.assertTrue(len(result["items"])==0)

        # testing listings and parameter
        self.request.POST = {"profile": "not a profile"}
        result = view.search()
        self.assertTrue(result["error"])
        self.assertTrue(len(result["items"])==0)

        # testing listings and parameter
        profiles = self.app.configuration.search
        self.app.configuration.unlock()
        self.app.configuration.search = None
        self.request.POST = {"profile": "all"}
        try:
            result = view.search()
        except:
            self.app.configuration.search = profiles
            self.app.configuration.lock()
            raise
        self.app.configuration.search = profiles
        self.assertTrue(result["error"])
        self.assertTrue(len(result["items"])==0)
        self.app.configuration.lock()

        
    def test_renderjson(self):
        user = User("test")
        user.groups.append("group:manager")
        view = APIv1(self.root, self.request)
        r = self.root
        objs=r.GetObjs()
        for o in objs:
            r.Delete(o.id, obj=o, user=user)
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        o3 = create_bookmark(r, user)
        self.remove.append(o3.id)

        o2 = create_bookmark(o1, user)
        create_track(o1, user)
        create_track(o1, user)
        create_track(o3, user)

        values = view.subtree()
        self.assertTrue(self.request.response.status.startswith("400"))

        self.request.POST = {"profile": "none"}
        values = view.subtree()
        self.assertTrue(self.request.response.status.startswith("400"))

        profile = {"descent": ("nive.definitions.IContainer",),
                   "addContext": True}
        view.GetViewConf = lambda: Conf(settings=profile)
        values = view.subtree()
        self.assertTrue(values!={})
        self.assertTrue(len(values["items"])==2)
        self.assertTrue(len(values["items"][0]["items"])==3)

        profile = {"descent": ("nive.definitions.IContainer",),
                   "parameter": {"pool_type": "bookmark"},
                   "addContext": True}
        view.GetViewConf = lambda: Conf(settings=profile)
        values = view.subtree()
        self.assertTrue(values!={})
        self.assertTrue(len(values["items"])==2)
        self.assertTrue(len(values["items"][0]["items"])==1)

        view = APIv1(o1, self.request)
        self.request.POST = {"subtree": "0"}
        values = view.subtree()
        self.assertTrue(values!={})
        self.assertTrue(values.get("items")==None)
        

    def test_rendertmpl(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        objs=r.GetObjs()
        for o in objs:
            r.Delete(o.id, obj=o, user=user)
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        o3 = create_bookmark(r, user)
        self.remove.append(o3.id)

        o2 = create_bookmark(o1, user)
        create_track(o1, user)
        create_track(o1, user)
        create_track(o3, user)

        view = APIv1(o1, self.request)
        data = view.renderTmpl()
        self.assertTrue(data)


    def test_newform(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        
        view = APIv1(r, self.request)
        view.__configuration__ = viewModule

        self.request.POST = {"pool_type": "bookmark", "link": "the link", "comment": "some text"}
        result = view.newItemForm()
        self.assertTrue(self.request.response.headers["X-Result"])

        objs=len(r.GetObjsList(fields=["id"]))
        self.request.POST = {"pool_type": "bookmark", "link": "the link", "comment": "some text", "create$": "1"}
        try:
            view.newItemForm()
        except ExceptionalResponse as result:
            self.assertTrue(self.request.response.headers["X-Result"])
            self.assertTrue(objs+1==len(r.GetObjsList(fields=["id"])))

        view = APIv1(r, self.request)
        view.__configuration__ = viewModule
        view.GetViewConf = lambda: Conf(settings={"form": {"fields": ("comment",)}})

        self.request.POST = {"pool_type": "bookmark", "link": "the link", "comment": "some text"}
        result = view.newItemForm()
        self.assertTrue(self.request.response.headers["X-Result"])

        objs=len(r.GetObjsList(fields=["id"]))
        self.request.POST = {"pool_type": "bookmark", "link": "the link", "comment": "some text", "create$": "1"}
        try:
            view.newItemForm()
        except ExceptionalResponse as result:
            self.assertTrue(self.request.response.headers["X-Result"])
            self.assertTrue(objs+1==len(r.GetObjsList(fields=["id"])))


    def test_newform_assets(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root

        view = APIv1(r, self.request)
        view.__configuration__ = viewModule

        self.request.POST = {"assets":"only"}
        result = view.newItemForm()
        self.assertTrue(result["content"])
        self.assertTrue(result["content"].find("<form")==-1)


    def test_newform_noajax(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root

        view = APIv1(r, self.request)
        view.__configuration__ = viewModule
        view.GetViewConf = lambda: Conf(settings={"form": {"fields": ("comment",), "use_ajax": False}, "includeAssets": False})

        self.request.POST = {"pool_type": "bookmark", "link": "the link", "comment": "some text"}
        result = view.newItemForm()
        self.assertTrue(self.request.response.headers["X-Result"])

        objs=len(r.GetObjsList(fields=["id"]))
        self.request.POST = {"pool_type": "bookmark", "link": "the link", "comment": "some text", "create$": "1"}
        result = view.newItemForm()
        self.assertTrue(self.request.response.headers["X-Result"])
        self.assertTrue(result["content"])
        self.assertTrue(objs+1==len(r.GetObjsList(fields=["id"])))


    def test_newformfailures(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        
        view = APIv1(r, self.request)
        view.__configuration__ =viewModule

        # no type
        self.request.POST = {"link": "the link", "comment": "some text"}
        result = view.newItemForm()
        self.assertTrue(self.request.response.headers["X-Result"])

        objs=len(r.GetObjsList(fields=["id"]))
        self.request.POST = {"link": "the link", "comment": "some text", "create$": "1"}
        result = view.newItemForm()
        self.assertTrue(self.request.response.headers["X-Result"])
        self.assertTrue(objs==len(r.GetObjsList(fields=["id"])))
        
        # wrong subset
        self.request.POST = {"subset": "unknown!", "pool_type": "bookmark", "link": "the link", "comment": "some text"}
        self.assertRaises(ConfigurationError, view.newItemForm)

        # wrong action
        objs=len(r.GetObjsList(fields=["id"]))
        self.request.POST = {"pool_type": "bookmark", "link": "the link", "comment": "some text", "unknown$": "1"}
        result = view.newItemForm()
        self.assertTrue(self.request.response.headers["X-Result"])
        self.assertTrue(objs==len(r.GetObjsList(fields=["id"])))
        
        
    def test_setform(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        
        view = APIv1(o1, self.request)
        view.__configuration__ = viewModule

        self.request.POST = {}
        result = view.setItemForm()
        self.assertTrue(self.request.response.headers["X-Result"])

        objs=len(r.GetObjsList(fields=["id"]))
        self.request.POST = {"link": "the new link", "comment": "some new text", "create$": "1"}
        result = view.setItemForm()
        self.assertTrue(result["content"])
        self.assertTrue(self.request.response.headers["X-Result"])
        self.assertTrue(objs==len(r.GetObjsList(fields=["id"])))

        view = APIv1(o1, self.request)
        view.__configuration__ = viewModule
        view.GetViewConf = lambda: Conf(settings={"form": {"fields": ("comment",)}})

        self.request.POST = {}
        result = view.setItemForm()
        self.assertTrue(self.request.response.headers["X-Result"])

        objs=len(r.GetObjsList(fields=["id"]))
        self.request.POST = {"link": "the new link", "comment": "some new text", "create$": "1"}
        result = view.setItemForm()
        self.assertTrue(result["content"])
        self.assertTrue(self.request.response.headers["X-Result"])
        self.assertTrue(objs==len(r.GetObjsList(fields=["id"])))


    def test_setform_assets(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)

        view = APIv1(o1, self.request)
        view.__configuration__ = viewModule

        self.request.POST = {"assets":"only"}
        result = view.setItemForm()
        self.assertTrue(result["content"])
        self.assertTrue(result["content"].find("<form")==-1)


    def test_sertform_noajax(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)

        view = APIv1(o1, self.request)
        view.__configuration__ = viewModule
        view.GetViewConf = lambda: Conf(settings={"form": {"fields": ("comment",), "use_ajax": False}, "includeAssets": False})

        self.request.POST = {}
        result = view.setItemForm()
        self.assertTrue(self.request.response.headers["X-Result"])

        objs=len(r.GetObjsList(fields=["id"]))
        self.request.POST = {"link": "the new link", "comment": "some new text", "create$": "1"}
        result = view.setItemForm()
        self.assertTrue(result["content"])
        self.assertTrue(self.request.response.headers["X-Result"])
        self.assertTrue(objs==len(r.GetObjsList(fields=["id"])))


    def test_setformfailures(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        
        view = APIv1(o1, self.request)
        view.__configuration__ = viewModule

        # wrong subset
        self.request.POST = {"subset": "unknown!", "pool_type": "bookmark", "link": "the link", "comment": "some text"}
        self.assertRaises(ConfigurationError, view.setItemForm)

        # wrong action
        objs=len(r.GetObjsList(fields=["id"]))
        self.request.POST = {"pool_type": "bookmark", "link": "the link", "comment": "some text", "unknown$": "1"}
        result = view.setItemForm()
        self.assertTrue(self.request.response.headers["X-Result"])
        self.assertTrue(objs==len(r.GetObjsList(fields=["id"])))
        
        
    def test_noaction(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        
        view = APIv1(o1, self.request)

        self.request.POST = {"action": "unknown!"}
        result = view.action()
        self.assertFalse(result["result"])

        # test returns true if no workflow loaded
        self.request.POST = {"action": "unknown!", "test":"true"}
        result = view.action()
        self.assertTrue(result["result"])

        self.request.POST = {"action": "unknown!", "transition":"oooooo"}
        result = view.action()
        self.assertFalse(result["result"])


    def test_nostate(self):
        user = User("test")
        user.groups.append("group:manager")
        r = self.root
        o1 = create_bookmark(r, user)
        self.remove.append(o1.id)
        
        view = APIv1(o1, self.request)

        result = view.state()
        self.assertFalse(result["result"])





class tWebapi_db_sqlite(tWebapi_db, __local.SqliteTestCase):
    """
    see tests.__local
    """

class tWebapi_db_mysql(tWebapi_db, __local.MySqlTestCase):
    """
    see tests.__local
    """
    
class tWebapi_db_pg(tWebapi_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """



