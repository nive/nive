# -*- coding: utf-8 -*-
# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
This file contains all base classes for subclassing your own objects. All required components
are already included as parent classes.
"""

from nive.application import Application, AppFactory, Configuration, Registration
from nive.container import Root, Container, ContainerEdit, ContainerSecurity, ContainerFactory, RootWorkflow
from nive.objects import Object, ObjectEdit, ObjectWorkflow
from nive.events import Events
from nive.search import Search
from nive.definitions import implements
from nive.definitions import IApplication, IContainer, IRoot, IReadonly, INonContainer, IObject
# bw 0.9.12: might be used by other files
from nive.definitions import IPage, IPageContainer, IPageElement, IFile, IPageElementContainer, IFolder


class ApplicationBase(Application, AppFactory, Configuration, Registration, Events):
    """
    *Nive cms application* 
    
    The application manages module registration, module configuration, root dispatching
    and basic application events.
    """
    implements(IApplication)


class RootBase(Root, Container, Search, ContainerEdit, ContainerSecurity, Events, ContainerFactory, RootWorkflow):
    """
    *Root Edit*
    
    Default root class with add and delete support for subobjects. 
    """
    implements(IContainer, IRoot)
    
class RootReadOnlyBase(Root, Container, Search, Events, ContainerFactory, RootWorkflow):
    """
    *Root with readonly access and cache*
    
    Root class without add and delete support for subobjects. Objects are cached in memory.
    """
    implements(IRoot, IContainer, IReadonly)

    
    
class ObjectBase(Object, ObjectEdit, Events, ObjectWorkflow):
    """
    *Default non-container object with write access*
    
    This one does not support subobjects. 
    """
    implements(INonContainer, IObject)
    
class ObjectReadOnlyBase(Object, Events, ObjectWorkflow):
    """
    *Non-container object with read only access*
    
    This one does not support subobjects. 
    """
    implements(INonContainer, IObject, IReadonly)

class ObjectContainerBase(Object, ObjectEdit, ObjectWorkflow, Container, ContainerEdit,ContainerSecurity,  Events, ContainerFactory):
    """
    *Default container object with write access*
    
    This one supports subobjects. 
    """
    implements(IContainer, IObject)
    
class ObjectContainerReadOnlyBase(Object, ObjectWorkflow, Container, Events, ContainerFactory):
    """
    *Container object with read only access and cache*
    
    This one supports subobjects and caches them in memory. 
    """
    implements(IObject, IContainer, IReadonly)

