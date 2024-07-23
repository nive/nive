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
from pyramid.request import RequestLocalCache
from pyramid.interfaces import ISecurityPolicy
from pyramid.authentication import AuthTktCookieHelper
from pyramid.authorization import ACLHelper


from pyramid import threadlocal

from nive.definitions import Conf, IPortal
from nive.definitions import Interface, implementer


def GetUsers(app):
    """
    Loads all users from user database if available.
    """
    portal = app.portal
    try:
        userdb = portal.userdb
        return userdb.root.GetUsers()
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
        if isinstance(groups, str):
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


@implementer(IAdminUser)
class AdminUser(object):
    """
    Admin User object with groups and login possibility. 
    """

    def __init__(self, values, ident):
        self.id = 0
        self.data = Conf(**values)
        self.meta = Conf()
        self.identity = ident or str(self.id)
        if values.get("groups"):
            groups = tuple(values.get("groups"))
        else:
            groups = ("group:admin",)
        self.groups = self.data.groups = groups

    def __str__(self):
        return str(self.identity)

    def Authenticate(self, password):
        return password == str(self.data["password"])
    
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
        if isinstance(groups, str):
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
            if a[3](*(context,)):
                processed.append(tuple(list(a[:3])))
            continue
        processed.append(tuple(a))
    return tuple(processed)


def effective_principals(request=None):
    # uses pyramid authentication groupfinder callback to lookup principals
    # returns None if no auth policy is configured (e.g. in tests)
    registry = threadlocal.get_current_registry()
    request = request or threadlocal.get_current_request()
    policy = registry.queryUtility(ISecurityPolicy)
    if policy is not None:
        ident = policy.identity(request)
        if ident is not None:
            return ident.get("principals")
    return None



@implementer(ISecurityPolicy)
class AuthTktSecurityPolicy:

    def __init__(self, secret, **kw):
        self.helper = AuthTktCookieHelper(secret, **kw)
        self.identity_cache = RequestLocalCache(self.load_identity)

    def _principals(self, userid, request):
        # context based callback
        context = request.context
        if context is None or IPortal.providedBy(context):
            return request.root.userdb.Principals(userid, request, context)
        return context.app.portal.userdb.Principals(userid, request, context)

    def load_identity(self, request):
        # define our simple identity as None or a dict with userid and principals keys
        identity = self.helper.identify(request)
        if identity is None:
            return None
        userid = identity['userid']  # identical to the deprecated request.unauthenticated_userid

        principals = self._principals(userid, request)

        # assuming the userid is valid, return a map with userid and principals
        if principals is not None:
            return {
                'userid': userid,
                'principals': principals,
            }
        return None

    def identity(self, request):
        return self.identity_cache.get_or_create(request)

    def authenticated_userid(self, request):
        # defer to the identity logic to determine if the user id logged in
        # and return None if they are not
        identity = request.identity
        if identity is not None:
            return identity['userid']
        return None

    def permits(self, request, context, permission):
        # use the identity to build a list of principals, and pass them
        # to the ACLHelper to determine allowed/denied
        identity = request.identity
        principals = {Everyone}
        if identity is not None:
            principals.add(Authenticated)
            principals.add(identity['userid'])
            principals.update(identity['principals'])
        return ACLHelper().permits(context, principals, permission)

    def remember(self, request, userid, response=None, **kw):
        headers = self.helper.remember(request, userid, **kw)
        if response is None:
            return headers
        if not hasattr(request.response, "headerlist"):
            request.response.headerlist = []
        request.response.headerlist += list(headers)

    def forget(self, request, response=None, **kw):
        headers = self.helper.forget(request, **kw)
        if response is None:
            return headers
        if not hasattr(request.response, "headerlist"):
            request.response.headerlist = []
        request.response.headerlist += list(headers)




@implementer(ISecurityPolicy)
class DummySecurityPolicy:

    def __init__(self, secret, **kw):
        pass

    def identity(self, request):
        # define our simple identity as None or a dict with userid and principals keys
        userid = request.environ.get("dummyUser")
        if userid is None:
            return dict(userid=None, principals=['system.Everyone'])

        # fake database access
        principals = request.environ.get("dummyPrincipals", [userid])

        # assuming the userid is valid, return a map with userid and principals
        if principals is not None:
            return dict(
                userid=userid,
                principals=principals
            )
        return dict(userid=userid, principals=['system.Authenticated'])

    def authenticated_userid(self, request):
        # defer to the identity logic to determine if the user id logged in
        # and return None if they are not
        identity = request.identity
        if identity is not None:
            return identity['userid']
        return None

    def permits(self, request, context, permission):
        # use the identity to build a list of principals, and pass them
        # to the ACLHelper to determine allowed/denied
        identity = request.identity
        principals = {Everyone}
        if identity is not None:
            principals.add(Authenticated)
            principals.add(identity['userid'])
            principals.update(identity['principals'])
        return ACLHelper().permits(context, principals, permission)

    def remember(self, request, userid, response=None, **kw):
        pass

    def forget(self, request, response=None, **kw):
        pass
