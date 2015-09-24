
import unittest

from nive.definitions import implements, Conf
from nive.security import User, AdminUser, GetUsers, Unauthorized, UserFound, IAdminUser
from nive.security import effective_principals
from nive.security import SetupRuntimeAcls


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


    def test_setupacls(self):
        acl = [("Allow", "group:reader", "read", lambda context: context.pool_state)]

        a = SetupRuntimeAcls(acl, Conf(pool_state=1))
        self.assert_(len(a)==1)
        self.assert_(len(a[0])==3)

        a = SetupRuntimeAcls(acl, Conf(pool_state=0))
        self.assert_(len(a)==0)

        def check(context):
            return context.pool_state
        acl = [("Allow", "group:reader", "read", check)]

        a = SetupRuntimeAcls(acl, Conf(pool_state=1))
        self.assert_(len(a)==1)
        self.assert_(len(a[0])==3)

        a = SetupRuntimeAcls(acl, Conf(pool_state=0))
        self.assert_(len(a)==0)


