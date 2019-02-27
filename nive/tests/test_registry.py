
import time
import unittest

from zope.interface.registry import Components
from zope.interface import Interface, implementer, alsoProvides, Provides

from nive.definitions import ObjectConf, Conf, IObjectConf, IConf



# -----------------------------------------------------------------
class ITest(Interface):
    pass
class ITest2(Interface):
    pass
class ITestaaaa(Interface):
    pass

class Test(object):
    Provides(ITest)
    def __call__(self, context):
        return self, context

@implementer(ITest)
class Test2(object):
    pass

# -----------------------------------------------------------------
testconf = ObjectConf(
    id = "text",
    name = "Text",
    dbparam = "texts",
    context = "nive.tests.thelper.text",
    selectTag = 1,
    description = ""
)
configuration = testconf



class registryTest(unittest.TestCase):

    def test_init1(self):
        registry = Components()
        #registerUtility(self, component=None, provided=None, name='', info='', event=True, factory=None)

        t2 = Test2()
        alsoProvides(t2, ITest2)
        self.assertTrue(ITest2.providedBy(t2))
        ITest.providedBy(Test())
        registry.registerUtility(Test(), provided=ITest, name='testconf')

        ITest2.providedBy(Test())
        registry.registerUtility(Test2(), name='testconf2')
        
        self.assertTrue(registry.queryUtility(ITestaaaa)==None)
        self.assertTrue(registry.queryUtility(ITest, name='testconf'))
        for u in registry.getUtilitiesFor(ITest):
            self.assertTrue(u)
        self.assertTrue(registry.getAllUtilitiesRegisteredFor(ITest))
        
        
    def test_init2(self):
        registry = Components()
        IConf.providedBy(Conf())
        registry.registerUtility(Conf(), provided=IConf, name='testconf2')
        
        IObjectConf.providedBy(testconf)
        registry.registerUtility(testconf, provided=IObjectConf, name='testconf3')
        
        registry.registerUtility(configuration, provided=IObjectConf, name='testconf')
        
        
        
    def test_init3(self):
        registry = Components()
        registry.registerAdapter(Test(), (IConf,), ITest, name='testadapter')
        registry.registerAdapter(Test(), (IConf,), ITest, name='testadapter2')
        registry.registerAdapter(Test(), (IConf,), ITest)
        c = Conf()
        
        self.assertTrue(IConf.providedBy(c))
        #registry.getAdapter(c, ITest, name='testadapter')
        self.assertTrue(registry.getAdapter(c, ITest))
        
        self.assertFalse(registry.queryAdapter(c, ITest, name='nix'))
        self.assertTrue(registry.queryAdapter(c, ITest, name='testadapter'))
        a = list(registry.getAdapters((c,), ITest))
        self.assertTrue(len(a)==3,a)
        
