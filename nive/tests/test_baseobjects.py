
import time
import unittest

from nive.definitions import *
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


