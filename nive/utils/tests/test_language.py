# -*- coding: utf-8 -*-

import unittest

from nive.utils import language_data
from nive.utils import language


class Langugage_data(unittest.TestCase):
    

    def test_defs(self):
        for lang in language_data.languages:
            conf = language_data.GetConf(lang)
            self.assertTrue(conf.get("code"), lang)
            self.assertTrue(conf.get("code2"), lang)
            self.assertTrue(conf.get("name"), lang)
        conf = language_data.GetConf("xxx")
        self.assertTrue(conf.get("code")=="")
        
    def test_codes(self):
        for conf in language_data.GetLanguages():
            self.assertTrue(conf.get("id"), conf)
            self.assertTrue(conf.get("name"), conf)
            
            
    def test_get(self):
        self.assertTrue(language_data.GetConf("ger").get("code2")=="de")
        self.assertTrue(language_data.GetConf("de").get("code")=="ger")
                        
        


class Langugage(unittest.TestCase):
    
    def test_lang(self):
        lext = language.LanguageExtension()
        for c in lext.Codelist():
            self.assertTrue(c.get("id"))
            self.assertTrue(c.get("name"))
            
    def test_conf(self):
        lext = language.LanguageExtension()
        for l in language_data.languages:
            conf = lext.GetConf(l)
            self.assertTrue(conf.get("code"), l)
            self.assertTrue(conf.get("code2"), l)
            self.assertTrue(conf.get("name"), l)
            

    def test_name(self):
        lext = language.LanguageExtension()
        for l in language_data.languages:
            name = lext.GetName(l)
            self.assertTrue(name, l)
            
            
            
            
            