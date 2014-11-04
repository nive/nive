# -*- coding: utf-8 -*-

import time
import unittest

from nive.helper import FormatConfTestFailure
from nive.definitions import DataTypes, FieldConf, Conf
from nive.components.reform.reformed import *

class testform(object):
    actionPostfix="$$$"
    @property
    def context(self):
        return None
    @property
    def app(self):
        return self
    def root(self):
        return self

    def LoadListItems(self, *kw):
        return [
            {"id": "item1", "name": "Item 1"},
            {"id": "item2", "name": "Item 2"},
            {"id": "item3", "name": "Item 3"},
            {"id": "item4", "name": "Item 4"},
            {"id": "item5", "name": "Item 5"},
        ]

class TestSchema(unittest.TestCase):

    def test_datatypes(self):
        for dt in DataTypes:
            fnc = nodeMapping.get(dt.id)
            if not fnc:
                raise TypeError, "Missing form SchemaNode for "+dt.id

    def test_hidden(self):
        field = FieldConf(datatype="string",hidden=True,id="field",name="Field")
        self.assert_(hidden_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_node(self):
        field = FieldConf(datatype="string",id="field",name="Field", node="node")
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_validator(self):
        def Validator():
            return
        field = FieldConf(datatype="string",id="field",name="Field", validator=Validator)
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_widget(self):
        field = FieldConf(datatype="string",id="field",name="Field", widget=Widget)
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_widget2(self):
        field = FieldConf(datatype="string",id="field",name="Field", widget="nive.components.reform.widget.Widget")
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_widget(self):
        field = FieldConf(datatype="string",id="field",name="Field", required=True, default="widget")
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        field = FieldConf(datatype="string",id="field",name="Field", required=False, default="widget")
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_actions(self):
        field = FieldConf(datatype="string",id="field",name="Field")
        action1 = Conf(id="action1", name="Action 1", cls="btn", hidden=False)
        action2 = Conf(id="action2", name="Action 2", cls="btn", hidden=True)
        nodes, buttons = SchemaFactory(testform(), [field], [action1,action2], force=False)
        self.assert_(len(buttons)==1)
        

    
class TestNodes(unittest.TestCase):
    
    def test_string(self):
        field = FieldConf(datatype="string",id="field",name="Field")
        self.assert_(string_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_number(self):
        field = FieldConf(datatype="number",id="field",name="Field")
        self.assert_(number_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_float(self):
        field = FieldConf(datatype="float",id="field",name="Field")
        self.assert_(float_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_bool(self):
        field = FieldConf(datatype="bool",id="field",name="Field")
        self.assert_(bool_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_htext(self):
        field = FieldConf(datatype="htext",id="field",name="Field")
        self.assert_(htext_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_text(self):
        field = FieldConf(datatype="text",id="field",name="Field")
        self.assert_(text_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_code(self):
        field = FieldConf(datatype="code",id="field",name="Field")
        self.assert_(code_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_json(self):
        field = FieldConf(datatype="json",id="field",name="Field")
        self.assert_(json_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_file(self):
        field = FieldConf(datatype="file",id="field",name="Field")
        self.assert_(file_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_date(self):
        field = FieldConf(datatype="date",id="field",name="Field")
        self.assert_(date_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_datetime(self):
        field = FieldConf(datatype="datetime",id="field",name="Field")
        self.assert_(datetime_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)
        
    def test_list(self):
        field = FieldConf(datatype="list",id="field",name="Field",settings={"addempty":True, "controlset":"yes"})
        self.assert_(list_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_radio(self):
        field = FieldConf(datatype="radio",id="field",name="Field")
        self.assert_(radio_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_multilist(self):
        field = FieldConf(datatype="multilist",id="field",name="Field")
        self.assert_(multilist_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_checkbox(self):
        field = FieldConf(datatype="checkbox",id="field",name="Field")
        self.assert_(checkbox_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_lines(self):
        field = FieldConf(datatype="lines",id="field",name="Field")
        self.assert_(lines_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_email(self):
        field = FieldConf(datatype="email",id="field",name="Field")
        self.assert_(email_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_url(self):
        field = FieldConf(datatype="url",id="field",name="Field")
        self.assert_(url_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_urllist(self):
        field = FieldConf(datatype="urllist",id="field",name="Field")
        self.assert_(urllist_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_password(self):
        field = FieldConf(datatype="password",id="field",name="Field",settings={"single":True})
        self.assert_(password_node(field, {}, {}, testform()))
        field = FieldConf(datatype="password",id="field",name="Field",settings={"single":False})
        self.assert_(password_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_unit(self):
        field = FieldConf(datatype="unit",id="field",name="Field")
        self.assert_(unit_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_unitlist(self):
        field = FieldConf(datatype="unitlist",id="field",name="Field")
        self.assert_(unitlist_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==1)

    def test_timestamp(self):
        field = FieldConf(datatype="timestamp",id="field",name="Field")
        self.assertFalse(timestamp_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==0)

    def test_nlist(self):
        field = FieldConf(datatype="nlist",id="field",name="Field")
        self.assertFalse(nlist_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==0)

    def test_binary(self):
        field = FieldConf(datatype="binary",id="field",name="Field")
        self.assertFalse(binary_node(field, {}, {}, testform()))
        nodes, buttons = SchemaFactory(testform(), [field], [], force=False)
        self.assert_(len(nodes)==0)



        
        