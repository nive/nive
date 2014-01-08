"""
Running mysql tests
-------------------
Create a database 'ut_nive' and assign all permissions for user 'root@localhost'. 
File root is '/var/tmp/nive'.

To customize settings change 'dbconfMySql' in 'nive/tests/__local.py'.  

"""

import unittest

from nive.utils.path import DvPath

from nive.definitions import *
from nive.components.objects.base import ApplicationBase
from nive.portal import Portal

from nive.tests import db_app
from nive.tests import test_application
from nive.tests import test_container
from nive.tests import test_objects 
from nive.tests import __local


# switch test class to enable / disable tests
if not __local.ENABLE_MYSQL_TESTS:
    class utc:
        pass
    uTestCase = utc
else:
    uTestCase = unittest.TestCase
    
    
def myapp(modules=None):
    a = ApplicationBase()
    a.Register(DatabaseConf(__local.MYSQL_CONF))
    a.Register(db_app.appconf)
    if modules:
        for m in modules:
            a.Register(m)
    p = Portal()
    p.Register(a, "nive")
    a.SetupRegistry()
    root = DvPath(a.dbConfiguration.fileRoot)
    if not root.IsDirectory():
        root.CreateDirectories()
    try:
        a.Query("select id from pool_meta where id=1")
        a.Query("select id from data1 where id=1")
        a.Query("select id from data2 where id=1")
        a.Query("select id from data3 where id=1")
        a.Query("select id from pool_files where id=1")
        a.Query("select id from pool_sys where id=1")
        a.Query("select id from pool_groups where id=1")
    except:
        a.GetTool("nive.tools.dbStructureUpdater")()
    a.Startup(None)
    return a


class myappTest_db(test_application.appTest_db, uTestCase):
    def _loadApp(self, mods=None):
        self.app = myapp(mods)

class mycontainerTest_db(test_container.containerTest_db, uTestCase):
    def _loadApp(self, mods=None):
        self.app = myapp(mods)

class mygroupsTest_db(test_objects.groupsTest_db, uTestCase):
    def _loadApp(self, mods=None):
        self.app = myapp(mods)

class myobjTest_db(test_objects.objTest_db, uTestCase):
    def _loadApp(self, mods=None):
        self.app = myapp(mods)

class mygroupsrootTest_db(test_container.groupsrootTest_db, uTestCase):
    def _loadApp(self, mods=None):
        self.app = myapp(mods)


"""


class myobjToolTest_db(test_objects.objToolTest_db, uTestCase):
    def _loadApp(self, mods=None):
        self.app = myapp(mods)

class myobjWfTest_db(test_objects.objWfTest_db, uTestCase):
    def _loadApp(self, mods=None):
        self.app = myapp(mods)

"""

