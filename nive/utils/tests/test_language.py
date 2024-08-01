# -*- coding: utf-8 -*-

import unittest

from nive.utils import language_data


class Langugage_data(unittest.TestCase):
    

    def test_defs(self):
        for lang, info in language_data.LANGUAGES.items():
            conf = language_data.GetConf(lang)
            self.assertTrue(conf.get("code")==lang, lang)
            self.assertTrue(conf.get("code2")!=lang, lang)
            self.assertTrue(conf.get("name"), lang)

    def test_codes(self):
        for conf in language_data.GetLanguages():
            self.assertTrue(conf.get("id"), conf)
            self.assertTrue(conf.get("name"), conf)

    def test_codes2(self):
        for conf in language_data.GetLanguages2():
            self.assertTrue(conf.get("id"), conf)
            self.assertTrue(conf.get("title"), conf)
            self.assertTrue(conf.get("name"), conf)


    def test_get(self):
        self.assertTrue(language_data.GetConf("ger").get("code2")=="de")
        self.assertTrue(language_data.GetConf("de").get("code")=="ger")
        self.assertTrue(language_data.GetConf("xxx").get("code")=="")


