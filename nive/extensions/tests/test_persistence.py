# -*-coding:utf-8 -*-

import unittest

from nive.extensions.persistence import *
from nive.definitions import Conf
from nive.helper import FormatConfTestFailure

from nive.tests import db_app
from nive.tests import __local

        

class Persistence(unittest.TestCase):
    
    def setUp(self):
        self.app = db_app.app_nodb()

    def tearDown(self):
        self.app.Close()


    def test_1(self):
        p = PersistentConf(self.app, self.app.configuration)
        
        
    def test_2(self):
        LoadStoredConfValues(self.app, None)
        
        
        
class tdbPersistence(__local.DefaultTestCase):
    
    def setUp(self):
        self._loadApp(["nive.extensions.persistence.dbPersistenceConfiguration"])

    def tearDown(self):
        self._closeApp()

    
    def test_conf(self):
        r=dbPersistenceConfiguration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))

        
        
    def test_storedconf(self):
        storage = self.app.NewModule(IModuleConf, "persistence")
        self.assertTrue(storage)
        LoadStoredConfValues(self.app, None)


    def test_load(self):
        storage = self.app.NewModule(IModuleConf, "persistence")
        self.assertTrue(storage)
        storage(self.app, Conf(id="test")).Save({"title":"öäüß", "something": 123})

        values = Conf(id="test")
        storage(self.app, values).Load()
        self.assertTrue(values["something"] == 123)
        self.assertTrue(values["title"] == "öäüß")