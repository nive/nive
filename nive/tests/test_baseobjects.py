
import time
import unittest

from nive.definitions import *
from nive.components.objects import base
from nive.components import baseobjects

class baseTest(unittest.TestCase):

    def test_imports(self):
        self.assert_(baseobjects.ApplicationBase)
        self.assert_(IApplication.implementedBy(baseobjects.ApplicationBase))
        
        self.assert_(baseobjects.RootBase)
        self.assert_(IContainer.implementedBy(baseobjects.RootBase))
        self.assert_(IRoot.implementedBy(baseobjects.RootBase))
        
        self.assert_(baseobjects.RootReadOnlyBase)
        self.assert_(IRoot.implementedBy(baseobjects.RootReadOnlyBase))
        self.assert_(IContainer.implementedBy(baseobjects.RootReadOnlyBase))
        self.assert_(IReadonly.implementedBy(baseobjects.RootReadOnlyBase))
    
        self.assert_(baseobjects.ObjectBase)
        self.assert_(INonContainer.implementedBy(baseobjects.ObjectBase))
        self.assert_(IObject.implementedBy(baseobjects.ObjectBase))
    
        self.assert_(baseobjects.ObjectReadOnlyBase)
        self.assert_(INonContainer.implementedBy(baseobjects.ObjectReadOnlyBase))
        self.assert_(IObject.implementedBy(baseobjects.ObjectReadOnlyBase))
        self.assert_(IReadonly.implementedBy(baseobjects.ObjectReadOnlyBase))
    
        self.assert_(baseobjects.ObjectContainerBase)
        self.assert_(IContainer.implementedBy(baseobjects.ObjectContainerBase))
        self.assert_(IObject.implementedBy(baseobjects.ObjectContainerBase))
    
        self.assert_(baseobjects.ObjectContainerReadOnlyBase)
        self.assert_(IObject.implementedBy(baseobjects.ObjectContainerReadOnlyBase))
        self.assert_(IContainer.implementedBy(baseobjects.ObjectContainerReadOnlyBase))
        self.assert_(IReadonly.implementedBy(baseobjects.ObjectContainerReadOnlyBase))


    
    
    def test_old_imports(self):
        self.assert_(base.ApplicationBase)
        self.assert_(base.RootBase)
        self.assert_(base.RootReadOnlyBase)
        self.assert_(base.ObjectBase)
        self.assert_(base.ObjectReadOnlyBase)
        self.assert_(base.ObjectContainerBase)
        self.assert_(base.ObjectContainerReadOnlyBase)
        # moved to nive_cms
        #self.assert_(base.PageBase)
        #self.assert_(base.PageRootBase)
        #self.assert_(base.PageElementBase)
        #self.assert_(base.PageElementFileBase)
        #self.assert_(base.PageElementContainerBase)
        #self.assert_(base.FolderBase)
