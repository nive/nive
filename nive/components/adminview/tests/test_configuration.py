# -*- coding: utf-8 -*-

import time
import unittest

from nive.definitions import *
from nive.helper import FormatConfTestFailure

from nive.components.adminview import view




class TestConf(unittest.TestCase):

    def test_conf1(self):
        r=view.configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))



    def test_conf2(self):
        r=view.dbAdminConfiguration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


