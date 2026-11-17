

import unittest

from nive.helper import FormatConfTestFailure

from nive.components.adminview import view


class TestConf(unittest.TestCase):

    def test_conf1(self):
        r=view.configuration.test()
        if not r:
            return
        self.fail(FormatConfTestFailure(r))


