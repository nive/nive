# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Owner Group extension module
----------------------------
Security extension to handle local group assginments for users.
Can be used for Roots and Objects or any other python class supporting events
and id attribute (number). Uses idhash for root objects.
"""

from nive.definitions import ModuleConf, Conf
from nive.definitions import implementer, ILocalGroups


@implementer(ILocalGroups)
class OwnerGroup(object):
    """
    """
    _owner = "group:owner"

    def GetLocalGroups(self, username, user=None):
        """
        Group assignments use the user name.
        returns a list of all local user groups, including parent settings
        """
        if username==self.meta.pool_createdby:
            return [self._owner]
        return []


    def AllLocalGroups(self):
        """
        returns a list of all local user group settings as list including 
        [username, group, id]. This function does not include parent level
        settings.
        """
        return [self._owner]


    def AddOwner(self, user, **kw):
        """
        Set the current user as group:owner in pool_createdby
        """
        if user is None:
            return
        self.meta["pool_createdby"] = str(user)

        
    def AddLocalGroup(self, username, group):
        """
        Add a local group assignment for username.
        """
        pass

        
    def RemoveLocalGroups(self, username, group=None):
        """
        Remove a local group assignment. If group is None all local groups
        will be removed.
        """
        pass


    def RemoveGroups(self, **kw):
        """
        Remove all group assignments before deleting the object. 
        """
        pass



def SetupOwnerGroup(app, pyramidConfig):
    # get all roots and add extension
    extension = "nive.extensions.owner.OwnerGroup"
    def add(confs):
        for c in confs:
            e = c.extensions
            if e and extension in e:
                continue
            if e is None:
                e = []
            if isinstance(e, tuple):
                e = list(e)
            e.append(extension)
            c.unlock()
            c.extensions = tuple(e)
            c.lock()
    
    add(app.configurationQuery.GetAllRootConfs())
    add(app.configurationQuery.GetAllObjectConfs())
    
    
configuration = ModuleConf(
    id = "localGroups",
    name = "Owner Group assignment for objects and roots",
    context = "nive.extensions.owner.OwnerGoup",
    events = (Conf(event="startRegistration", callback=SetupOwnerGroup),),
)
