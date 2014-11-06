# -*- coding: utf-8 -*-

import unittest
import os
import tempfile

from nive.utils.utils import MakeListItems, ConvertHTMLToText, ConvertToDateTime



class UtilsTest(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    
    def test_makelistitems1(self):
        l = ["1","2","3"]
        li = MakeListItems(l)
        self.assert_(len(li)==3)
        self.assert_(li[0]["id"]=="1")
        self.assert_(li[1]["name"]=="2")
        l = ("1","2","3")
        li = MakeListItems(l)
        self.assert_(len(li)==3)
        self.assert_(li[0]["id"]=="1")
        self.assert_(li[1]["name"]=="2")

    def test_makelistitems2(self):
        l = [["1","N1"],["2","N2"],["3","N3"]]
        li = MakeListItems(l)
        self.assert_(len(li)==3)
        self.assert_(li[0]["id"]=="1")
        self.assert_(li[1]["name"]=="N2")

        l = (("1","N1"),("2","N2"),("3","N3"))
        li = MakeListItems(l)
        self.assert_(len(li)==3)
        self.assert_(li[0]["id"]=="1")
        self.assert_(li[1]["name"]=="N2")

    def test_makelistitems3(self):
        l = [1,2,3]
        li = MakeListItems(l)
        self.assert_(len(li)==3)
        self.assert_(li[0]["id"]=="1")
        self.assert_(li[1]["name"]=="2")
        l = (1,2,3)
        li = MakeListItems(l)
        self.assert_(len(li)==3)
        self.assert_(li[0]["id"]=="1")
        self.assert_(li[1]["name"]=="2")

    def test_htmltotext(self):
        html = "Hello!"
        t = ConvertHTMLToText(html, removeReST=True)
        self.assert_(t==html+"\n\n")

        html = "<h1>Hello!</h1>"
        t = ConvertHTMLToText(html, removeReST=True)
        self.assert_(t == "Hello!"+"\n\n")

        html = "<h1>Hello!</h1>"
        t = ConvertHTMLToText(html, removeReST=False)
        self.assert_(t == "# Hello!"+"\n\n", t)

        html = "# Hello!"
        t = ConvertHTMLToText(html, removeReST=True)
        self.assert_(t == "Hello!"+"\n\n")

    def test_todatetime(self):
        import datetime
        dt = datetime.datetime.now()
        self.assert_(ConvertToDateTime(dt)==dt)

        import time
        self.assert_(ConvertToDateTime(time.time()))

        self.assert_(ConvertToDateTime(0)==None)
        self.assert_(ConvertToDateTime(None)==None)

        self.assert_(ConvertToDateTime(str(dt)).strftime("%Y-%m-%d %H:%M:%S")==dt.strftime("%Y-%m-%d %H:%M:%S"))
        self.assert_(ConvertToDateTime("2015-01-02").strftime("%Y-%m-%d")=="2015-01-02")
        self.assert_(ConvertToDateTime("2015/01/02").strftime("%Y-%m-%d")=="2015-01-02")
        self.assert_(ConvertToDateTime("2015/01/02 12:23").strftime("%Y-%m-%d %H:%M")=="2015-01-02 12:23")
        self.assert_(ConvertToDateTime("2015/01/02 12:23:43").strftime("%Y-%m-%d %H:%M:%S")=="2015-01-02 12:23:43")
