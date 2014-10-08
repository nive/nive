
import time
import unittest
from pyramid import testing

from nive.portal import Portal
from nive.definitions import ConfigurationError
from nive.definitions import ModuleConf
from nive.helper import Event
from nive.definitions import OperationalError
from nive.tests.test_application import testapp, mApp2, mApp


class DummyClass1(object):
    def __init__(self, conf):
        pass
class DummyClass2(object):
    def hello(self):
        return "hello"
        

class portalTest(unittest.TestCase):
    
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)
        self.portal = Portal()
        self.app = testapp(mApp2)

    def tearDown(self):
        pass


    def test_register(self):
        self.portal.Register(mApp)
        self.portal.Register(self.app, "another")
        self.portal.Register("nive.tests.test_application.mApp2")
        self.assertRaises(ImportError, self.portal.Register, "nive.tests.test_application.mApp56875854")
        self.assertRaises(ConfigurationError, self.portal.Register, time)

    def test_module(self):
        testconf = ModuleConf(
            id = "module",
            name = "Module",
            context = "nive.tests.test_portal.DummyClass1",
            extensions = (DummyClass2,),
            events = None,
            description = ""
        )
        self.portal.Register(testconf, "test")
        m=self.portal["test"]
        self.assert_(self.portal["test"].hello()=="hello")

    def test_portal(self):
        self.portal.Register(mApp2)
        self.portal.Register(self.app, "nive")
        self.portal.RegisterGroups(self.app)
        self.assert_(self.portal.__getitem__("app2"))
        self.assert_(self.portal.__getitem__("nive"))
        try:
            self.portal.Startup(None)
        except OperationalError:
            pass
        self.assert_(len(self.portal.GetApps())==2)
        self.assert_(self.portal.GetGroups(sort=u"id", visibleOnly=False))
        self.assert_(self.portal.GetGroups(sort=u"name", visibleOnly=True))
        self.assert_(self.portal.portal)


    def test_portal2(self):
        self.portal.StartConnection(Event(self.request))
        self.portal.FinishConnection(Event(self.request))




