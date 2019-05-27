# -*- coding: utf-8 -*-

import time
import unittest

from nive.security import User

"""
#totest:
templates/
definitions.py
parts.py
root.py
search.py
view.py
"""


class IfaceTest:#(unittest.TestCase): # TODO tests

	def setUp(self):
		app = App()
		app.SetConfiguration({"objects": [typedef]})
		self.c = IFace(app)


	def testReg(self):
		self.c.RegisterType(typedef)
		self.c.RegisterComponent(viewdef)
		
	def testGet(self):
		container = Ob()
		container.IContainer=1
		object = Ob()
		addtype = "page"
		self.assertTrue(self.c.GetFldsAdd(container, addtype))
		self.assertTrue(self.c.GetFldsEdit(object))
		self.assertTrue(self.c.GetFldsMetaView(object))
		self.assertTrue(self.c.GetFldsDataView(object))

	def testSearch(self):
		container = Ob()
		container.IContainer=1
		self.assertTrue(self.c.GetSearchConf("", container=container))
		self.assertTrue(self.c.GetSearchConf("default", container=container))

	def testF(self):	
		object = Ob()
		self.assertTrue(self.c.GetTabs(object))
		self.assertTrue(self.c.GetShortcuts(object))
		
	def testRedirect(self):	
		object = Ob()
		self.assertTrue(self.c.GetRedirect("delete", view=object))


