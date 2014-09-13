
import time
import unittest
from types import DictType

from nive.definitions import implements
from nive.security import User, AdminUser, GetUsers, Unauthorized, UserFound, IAdminUser
from nive.security import effective_principals


class securityTest(unittest.TestCase):

    def test_excps(self):
        u = Unauthorized()
        f = UserFound("user")

    def test_iface(self):
        class aaaaa(object):
            implements(IAdminUser)
        a = aaaaa()

    def test_user(self):
        u = User("name", 123)
        self.assert_(str(u)=="name")
        self.assert_(u.id==123)
        u.GetGroups()

    def test_adminuser(self):
        u = AdminUser({"name":"admin", "password":"11111", "email":"admin@aaa.ccc"}, "admin")
        
        self.assert_(u.identity=="admin")
        self.assert_(str(u)=="admin")
        self.assert_(u.Authenticate("11111"))
        self.assertFalse(u.Authenticate("aaaaaaa"))
        u.Login()
        u.Logout()
        self.assert_(u.ReadableName()=="admin")
        
    def test_adminuser_groups(self):
        u = AdminUser({"name":"admin", "password":"11111", "email":"admin@aaa.ccc"}, "admin")
        self.assert_(u.GetGroups()==("group:admin",))
        self.assert_(u.InGroups("group:admin"))
        self.assertFalse(u.InGroups("group:traa"))
        
        u = AdminUser({"name":"admin", "password":"11111", "email":"admin@aaa.ccc", "groups":("group:admin",)}, "admin")
        self.assert_(u.GetGroups()==("group:admin",))
        self.assert_(u.InGroups("group:admin"))
        self.assertFalse(u.InGroups("group:traa"))

        u = AdminUser({"name":"admin", "password":"11111", "email":"admin@aaa.ccc", "groups":("group:admin","group:another")}, "admin")
        self.assert_(len(u.GetGroups())==2)
        self.assert_(u.InGroups("group:admin"))
        self.assert_(u.InGroups("group:another"))
        self.assertFalse(u.InGroups("group:traa"))

    def test_principals(self):
        p = effective_principals()
        self.assert_(p==None)

