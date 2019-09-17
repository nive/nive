
import time
import unittest

from nive.definitions import Conf
from nive.events import *



# -----------------------------------------------------------------

class testobj(Events):
    def __init__(self):
        self.called = 0
        self.InitEvents()
    
    def callme(self):
        self.Signal("callme", data=1)

    def event_testLocal(self, **kw):
        self.called = kw.get("data")
        

class EventTest(unittest.TestCase):

    def setUp(self):
        self.obj = testobj()


    def event_test(self, **kw):
        self.called = kw.get("data")

    def test_events1(self):
        self.obj.ListenEvent("test", "event_testLocal")
        self.obj.Signal("test", data=12345)
        self.assertTrue(self.obj.called==12345)
        self.obj.RemoveListener("test", "event_testLocal")
        self.obj.Signal("test", data=67890)
        self.assertTrue(self.obj.called==12345)

    def test_eventobj(self):
        self.called = 0
        self.obj.ListenEvent("callme", self.event_test)
        self.obj.callme()
        self.assertTrue(self.called==1)
        self.obj.RemoveListener("callme", self.event_test)
        self.called=0
        self.obj.callme()
        self.assertTrue(self.called==0)


    def test_eventcontext(self):
        
        def event_fnc_test(context=None, data=None):
            self.assertTrue(context==self.obj)
            self.called=1
        
        self.called = 0
        self.obj.ListenEvent("callme", event_fnc_test)
        self.obj.callme()
        self.assertTrue(self.called==1)
        self.obj.RemoveListener("callme", event_fnc_test)
        self.called=0
        self.obj.callme()
        self.assertTrue(self.called==0)


    def test_eventresult(self):
        
        def event_fnc_test1(context=None, data=None):
            self.assertTrue(context==self.obj)
            return data
        def event_fnc_test2(context=None, data=None):
            self.assertTrue(context==self.obj)
            return data
        
        self.called = 0
        self.obj.ListenEvent("callme", event_fnc_test1)
        result = self.obj.Signal("callme", data=1)
        self.assertTrue(len(result)==1)
        self.assertTrue(result[0][0]==1, result)

        self.obj.ListenEvent("callme", event_fnc_test2)
        result = self.obj.Signal("callme", data=1)
        self.assertTrue(len(result)==2, result)
        self.assertTrue(result[0][0]==1)
        self.assertTrue(result[1][0]==1)

        self.obj.RemoveListener("callme")


    def test_eventfromconf(self):

        def event_fnc_test1(context=None, data=None):
            self.assertTrue(context==self.obj)
            return data
        def event_fnc_test2(context=None, data=None):
            self.assertTrue(context==self.obj)
            return data

        events = [Conf(event="callme1",callback=event_fnc_test1),
                  Conf(event="callme2",callback=event_fnc_test2)]

        self.called = 0
        self.obj.SetupEventsFromConfiguration(events)

        result = self.obj.Signal("callme1", data=1)
        self.assertTrue(len(result)==1)
        self.assertTrue(result[0][0]==1, result)

        result = self.obj.Signal("callme2", data=2)
        self.assertTrue(len(result)==1, result)
        self.assertTrue(result[0][0]==2)

        self.obj.RemoveListener("callme1")
        self.obj.RemoveListener("callme2")
