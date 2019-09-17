
import unittest

from nive.definitions import implementer, Conf
from nive.security import User, AdminUser, GetUsers, Unauthorized, UserFound, IAdminUser
from nive.security import effective_principals
from nive.security import SetupRuntimeAcls


class securityTest(unittest.TestCase):

    def test_excps(self):
        u = Unauthorized()
        f = UserFound("user")

    def test_iface(self):
        @implementer(IAdminUser)
        class aaaaa(object):
            pass
        a = aaaaa()

    def test_user(self):
        u = User("name", 123)
        self.assertTrue(str(u)=="name")
        self.assertTrue(u.id==123)
        u.GetGroups()

    def test_adminuser(self):
        u = AdminUser({"name":"admin", "password":"11111", "email":"admin@aaa.ccc"}, "admin")
        
        self.assertTrue(u.identity=="admin")
        self.assertTrue(str(u)=="admin")
        self.assertTrue(u.Authenticate("11111"))
        self.assertFalse(u.Authenticate("aaaaaaa"))
        u.Login()
        u.Logout()
        self.assertTrue(u.ReadableName()=="admin")
        
    def test_adminuser_groups(self):
        u = AdminUser({"name":"admin", "password":"11111", "email":"admin@aaa.ccc"}, "admin")
        self.assertTrue(u.GetGroups()==("group:admin",))
        self.assertTrue(u.InGroups("group:admin"))
        self.assertFalse(u.InGroups("group:traa"))
        
        u = AdminUser({"name":"admin", "password":"11111", "email":"admin@aaa.ccc", "groups":("group:admin",)}, "admin")
        self.assertTrue(u.GetGroups()==("group:admin",))
        self.assertTrue(u.InGroups("group:admin"))
        self.assertFalse(u.InGroups("group:traa"))

        u = AdminUser({"name":"admin", "password":"11111", "email":"admin@aaa.ccc", "groups":("group:admin","group:another")}, "admin")
        self.assertTrue(len(u.GetGroups())==2)
        self.assertTrue(u.InGroups("group:admin"))
        self.assertTrue(u.InGroups("group:another"))
        self.assertFalse(u.InGroups("group:traa"))

    def test_principals(self):
        p = effective_principals()
        self.assertTrue(p==None)


    def test_setupacls(self):
        acl = [("Allow", "group:reader", "read", lambda context: context.pool_state)]

        a = SetupRuntimeAcls(acl, Conf(pool_state=1))
        self.assertTrue(len(a)==1)
        self.assertTrue(len(a[0])==3)

        a = SetupRuntimeAcls(acl, Conf(pool_state=0))
        self.assertTrue(len(a)==0)

        def check(context):
            return context.pool_state
        acl = [("Allow", "group:reader", "read", check)]

        a = SetupRuntimeAcls(acl, Conf(pool_state=1))
        self.assertTrue(len(a)==1)
        self.assertTrue(len(a[0])==3)

        a = SetupRuntimeAcls(acl, Conf(pool_state=0))
        self.assertTrue(len(a)==0)


