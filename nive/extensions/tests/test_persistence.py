

import unittest

from nive.definitions import *

from nive.extensions.persistence import *

from nive.tests import db_app
from nive.tests import __local

        

class Persistence(unittest.TestCase):
    
    def setUp(self):
        self.app = db_app.app_nodb()
        pass
    
    def tearDown(self):
        pass
    
    
    def test_1(self):
        p = PersistentConf(self.app, self.app.configuration)
        
        
    def test_2(self):
        LoadStoredConfValues(self.app, None)
        
        
        
class tdbPersistence(__local.DefaultTestCase):
    
    def setUp(self):
        self._loadApp(["nive.extensions.persistence.dbPersistenceConfiguration"])
    
    def tearDown(self):
        pass
    
    def test_conf1(self):
        r=dbPersistenceConfiguration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")
        
        
    def test_2(self):
        storage = self.app.Factory(IModuleConf, "persistence")
        self.assert_(storage)
        LoadStoredConfValues(self.app, None)