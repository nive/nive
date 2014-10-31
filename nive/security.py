# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
User and security functions.
"""

# imports used by other files
from pyramid.security import Allow 
from pyramid.security import Deny
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Everyone, Authenticated
from pyramid.security import remember, forget, authenticated_userid
from pyramid.security import has_permission

from pyramid import threadlocal
from pyramid.interfaces import IAuthenticationPolicy, IAuthorizationPolicy

from nive.definitions import Conf
from nive.definitions import Interface, implements


def GetUsers(app):
    """
    Loads all users from user database if available.
    """
    portal = app.portal
    try:
        userdb = portal.userdb
        return userdb.root().GetUsers()
    except:
        return []

    
class User(object):
    """
    A fake user object for testing.
    """
    def __str__(self):
        return self.data.name
    
    def __init__(self, name, id=0):
        self.id = id
        self.groups = []
        self.meta = Conf(title=name,pool_state=1)
        self.data = Conf(name=name,email="",groups=[])

    @property
    def identity(self):
        return str(self)
        
    def GetGroups(self, context=None):
        return self.groups
    
    def InGroups(self, groups):
        """
        check if user has one of these groups
        """
        if isinstance(groups, basestring):
            return groups in self.groups
        for g in groups:
            if g in self.groups:
                return True
        return False
    
    def ReadableName(self):
        return self.data.name
    
    def Commit(self, user=None):
        return


class Unauthorized(Exception):
    """
    failed login
    """

class UserFound(Exception):
    """
    Can be used in *getuser* listeners to break user lookup and
    pass a session user to LookupUser. The second argument is the session
    user 
    """
    def __init__(self, user):
        self.user = user



class IAdminUser(Interface):
    """
    Used for admin user instance hard coded in configration 
    """


class AdminUser(object):
    """
    Admin User object with groups and login possibility. 
    """
    implements(IAdminUser)
    
    def __init__(self, values, ident):
        self.id = 0
        self.data = Conf(**values)
        self.meta = Conf()
        self.identity = ident or str(self.id)
        if values.get("groups"):
            groups = tuple(values.get("groups"))
        else:
            groups = (u"group:admin",)
        self.groups = self.data.groups = groups

    def __str__(self):
        return str(self.identity)

    def Authenticate(self, password):
        return password == unicode(self.data["password"])
    
    def Login(self):
        """ """

    def Logout(self):
        """ """

    def GetGroups(self, context=None):
        """ """
        return self.groups

    def InGroups(self, groups):
        """
        check if user has one of these groups
        """
        if isinstance(groups, basestring):
            return groups in self.groups
        for g in groups:
            if g in self.groups:
                return True
        return False
    
    def ReadableName(self):
        return self.data.name


def SetupRuntimeAcls(acl, context):
    """
    Can be used during object initialisation to process acls.
    Acls can have a additional callback parameter called with the context
    to find out whetther to apply the single acl or not. The callback should return
    true or false. e.g. ::

        (Allow, "group:reader", "read", lambda context: context.meta.pool_state),

    or ::

        def check(context):
            return context.meta.pool_state

        (Allow, "group:reader", "read", check),

    :param acl:
    :param context:
    :return: tuple of acls to be stored as __acl__
    """
    processed = []
    for a in acl:
        if len(a)==4:
            if apply(a[3], (context,)):
                processed.append(tuple(list(a[:3])))
            continue
        processed.append(tuple(a))
    return tuple(processed)


def effective_principals(request=None):
    # uses pyramid authentication groupfinder callback to lookup principals
    # returns None if no auth policy is configured (e.g. in tests)
    registry = threadlocal.get_current_registry()
    request = request or threadlocal.get_current_request()
    authn_policy = registry.queryUtility(IAuthenticationPolicy)
    authz_policy = registry.queryUtility(IAuthorizationPolicy)
    if authn_policy and authz_policy:
        principals = authn_policy.effective_principals(request)
        return principals
    return None


        