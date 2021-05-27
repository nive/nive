# -*- coding: utf-8 -*-

import unittest
import os
import tempfile

from nive.utils.utils import MakeListItems, ConvertHTMLToText, ConvertToDateTime



class UtilsTest(unittest.TestCase):
    

    def test_makelistitems1(self):
        l = ["1","2","3"]
        li = MakeListItems(l)
        self.assertTrue(len(li)==3)
        self.assertTrue(li[0]["id"]=="1")
        self.assertTrue(li[1]["name"]=="2")
        l = ("1","2","3")
        li = MakeListItems(l)
        self.assertTrue(len(li)==3)
        self.assertTrue(li[0]["id"]=="1")
        self.assertTrue(li[1]["name"]=="2")

    def test_makelistitems2(self):
        l = [["1","N1"],["2","N2"],["3","N3"]]
        li = MakeListItems(l)
        self.assertTrue(len(li)==3)
        self.assertTrue(li[0]["id"]=="1")
        self.assertTrue(li[1]["name"]=="N2")

        l = (("1","N1"),("2","N2"),("3","N3"))
        li = MakeListItems(l)
        self.assertTrue(len(li)==3)
        self.assertTrue(li[0]["id"]=="1")
        self.assertTrue(li[1]["name"]=="N2")

    def test_makelistitems3(self):
        l = [1,2,3]
        li = MakeListItems(l)
        self.assertTrue(len(li)==3)
        self.assertTrue(li[0]["id"]=="1")
        self.assertTrue(li[1]["name"]=="2")
        l = (1,2,3)
        li = MakeListItems(l)
        self.assertTrue(len(li)==3)
        self.assertTrue(li[0]["id"]=="1")
        self.assertTrue(li[1]["name"]=="2")

    def test_htmltotext(self):
        html = "Hello!"
        t = ConvertHTMLToText(html, removeReST=True)
        self.assertEqual(t, html)

        html = "<h1>Hello!</h1>"
        t = ConvertHTMLToText(html, removeReST=True)
        self.assertEqual(t, "Hello!")

        html = "<h1>Hello!</h1>"
        t = ConvertHTMLToText(html, removeReST=False)
        self.assertEqual(t, "Hello!", t)

        html = "# Hello!"
        t = ConvertHTMLToText(html, removeReST=True)
        self.assertEqual(t, "# Hello!")

    def test_todatetime(self):
        import datetime
        dt = datetime.datetime.now()
        self.assertTrue(ConvertToDateTime(dt)==dt)

        import time
        self.assertTrue(ConvertToDateTime(time.time()))

        self.assertTrue(ConvertToDateTime(0)==None)
        self.assertTrue(ConvertToDateTime(None)==None)

        self.assertTrue(ConvertToDateTime(str(dt)).strftime("%Y-%m-%d %H:%M:%S")==dt.strftime("%Y-%m-%d %H:%M:%S"))
        self.assertTrue(ConvertToDateTime("2015-01-02").strftime("%Y-%m-%d")=="2015-01-02")
        self.assertTrue(ConvertToDateTime("2015/01/02").strftime("%Y-%m-%d")=="2015-01-02")
        self.assertTrue(ConvertToDateTime("2015/01/02 12:23").strftime("%Y-%m-%d %H:%M")=="2015-01-02 12:23")
        self.assertTrue(ConvertToDateTime("2015/01/02 12:23:43").strftime("%Y-%m-%d %H:%M:%S")=="2015-01-02 12:23:43")
