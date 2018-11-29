
import time
import unittest

from nive.definitions import *
from nive.components.objects import base
from nive.components import baseobjects

class baseTest(unittest.TestCase):

    def test_imports(self):
        self.assertTrue(baseobjects.ApplicationBase)
        self.assertTrue(IApplication.implementedBy(baseobjects.ApplicationBase))
        
        self.assertTrue(baseobjects.RootBase)
        self.assertTrue(IContainer.implementedBy(baseobjects.RootBase))
        self.assertTrue(IRoot.implementedBy(baseobjects.RootBase))
        
        self.assertTrue(baseobjects.RootReadOnlyBase)
        self.assertTrue(IRoot.implementedBy(baseobjects.RootReadOnlyBase))
        self.assertTrue(IContainer.implementedBy(baseobjects.RootReadOnlyBase))
        self.assertTrue(IReadonly.implementedBy(baseobjects.RootReadOnlyBase))
    
        self.assertTrue(baseobjects.ObjectBase)
        self.assertTrue(INonContainer.implementedBy(baseobjects.ObjectBase))
        self.assertTrue(IObject.implementedBy(baseobjects.ObjectBase))
    
        self.assertTrue(baseobjects.ObjectReadOnlyBase)
        self.assertTrue(INonContainer.implementedBy(baseobjects.ObjectReadOnlyBase))
        self.assertTrue(IObject.implementedBy(baseobjects.ObjectReadOnlyBase))
        self.assertTrue(IReadonly.implementedBy(baseobjects.ObjectReadOnlyBase))
    
        self.assertTrue(baseobjects.ObjectContainerBase)
        self.assertTrue(IContainer.implementedBy(baseobjects.ObjectContainerBase))
        self.assertTrue(IObject.implementedBy(baseobjects.ObjectContainerBase))
    
        self.assertTrue(baseobjects.ObjectContainerReadOnlyBase)
        self.assertTrue(IObject.implementedBy(baseobjects.ObjectContainerReadOnlyBase))
        self.assertTrue(IContainer.implementedBy(baseobjects.ObjectContainerReadOnlyBase))
        self.assertTrue(IReadonly.implementedBy(baseobjects.ObjectContainerReadOnlyBase))


    
    
    def test_old_imports(self):
        self.assertTrue(base.ApplicationBase)
        self.assertTrue(base.RootBase)
        self.assertTrue(base.RootReadOnlyBase)
        self.assertTrue(base.ObjectBase)
        self.assertTrue(base.ObjectReadOnlyBase)
        self.assertTrue(base.ObjectContainerBase)
        self.assertTrue(base.ObjectContainerReadOnlyBase)
        # moved to nive_cms
        #self.assert_(base.PageBase)
        #self.assert_(base.PageRootBase)
        #self.assert_(base.PageElementBase)
        #self.assert_(base.PageElementFileBase)
        #self.assert_(base.PageElementContainerBase)
        #self.assert_(base.FolderBase)
