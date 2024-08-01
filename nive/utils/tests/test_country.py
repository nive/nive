# -*- coding: utf-8 -*-

import unittest

from nive.utils import country_data


class Country_data(unittest.TestCase):
    
    def test_defs(self):
        for ccc in country_data.countries:
            self.assertTrue(ccc[0], ccc)
            self.assertTrue(ccc[1], ccc)
            self.assertTrue(ccc[2], ccc)
            self.assertTrue(ccc[3], ccc)
                        
        
    def test_codes(self):
        for conf in country_data.GetCountries():
            self.assertTrue(conf.get("id"), conf)
            self.assertTrue(conf.get("name"), conf)
            
            
    def test_get(self):
        self.assertTrue(country_data.GetConf("DEU").get("code2")=="DE")
        self.assertTrue(country_data.GetConf("DE").get("code")=="DEU")
        self.assertTrue(country_data.GetConf("XX").get("code2")==None)
                        
        

            
            
            