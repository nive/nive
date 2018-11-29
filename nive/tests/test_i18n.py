
import time
import unittest

from nive.i18n import *


class i18nTest(unittest.TestCase):

    def test_translate(self):
        t = translate("a nice string")
        self.assertTrue(t=="a nice string")

    def test_translator(self):
        t = translator()
        self.assertTrue(t("a nice string")=="a nice string")

