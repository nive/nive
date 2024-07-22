# -*- coding: utf-8 -*-

import time
import unittest

from nive.helper import FormatConfTestFailure

from nive.components.webapi import view




class TestConf(unittest.TestCase):

    def test_confcontainer(self):
        r=view.configuration.test()
        if not r:
            return
        print(FormatConfTestFailure(r))
        self.assertTrue(False, "Configuration Error")

