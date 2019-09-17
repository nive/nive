# -*- coding: utf-8 -*-

import unittest


from nive.extensions.path import PathExtension
from nive.utils import language_data



class TestPath(unittest.TestCase):
    
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    
    def test_1(self):
        p = PathExtension()

        fn = p.EscapeFilename("this is a filename")
        self.assertTrue(fn ==    "this_is_a_filename", fn)
        
        fn = p.EscapeFilename("this is a filename")
        self.assertTrue(fn ==    "this_is_a_filename", fn)
        
        fn = p.EscapeFilename("this is a filename")
        self.assertTrue(fn ==    "this_is_a_filename", fn)
        
        fn = p.EscapeFilename("This Is a Filename")
        self.assertTrue(fn ==    "this_is_a_filename", fn)
        
        fn = p.EscapeFilename("This_Is_a_Filename")
        self.assertTrue(fn ==    "this_is_a_filename", fn)
        
        fn = p.EscapeFilename("This_Is_a_Filename/")
        self.assertTrue(fn ==    "this_is_a_filename", fn)
        
        fn = p.EscapeFilename("This_Is_a§+#.~$%&_Filename")
        self.assertTrue(fn ==    "this_is_a_filename", fn)
        
        fn = p.EscapeFilename("This Is a looooooooooooooooooooooooooooooooooooooooooooooong Filename")
        self.assertTrue(fn == "this_is_a_loooooooooooooooooooooooooooooooooooooooooooo", fn)
        
        fn = p.EscapeFilename("This Is a looooooooooooooooooooooooooooooooooooong Filename")
        self.assertTrue(fn == "this_is_a_looooooooooooooooooooooooooooooooooooong", fn)
        
        fn = p.EscapeFilename("This Is ä Filename")
        self.assertTrue(fn == "this_is_a_filename", fn)
        
        
    def test_special_chars(self):
        p = PathExtension()

        for lang in language_data.languages:
            conf = language_data.GetConf(lang)
            if not conf.get("special_chars"):
                continue
            
            fn = p.EscapeFilename("test " + conf.get("special_chars"))
            self.assertTrue(fn.startswith("test"), fn)
            
        
