import time
import unittest

from nive.definitions import FieldConf, Conf, ConfigurationError, ReadonlySystemFlds, UserFlds
from nive.components.reform.forms import Form, HTMLForm, ToolForm, JsonMappingForm, ObjectForm
from nive.components.reform import schema
from nive.events import Events
from nive.views import BaseView
from nive.security import User as UserO
from nive.helper import Request
from nive.tests import db_app
from nive.tests import __local


data1_1 = { "ftext": "this is text!",
            "fnumber": "123456",
            "fdate": "2008-06-23 16:55:20",#
            "flist": "item 2",
            "fmselect": "item 5",
            "funit": 35,
            "funitlist": [34, 35, 36],
            "pool_type": "type1"}

data1_2 = { "ftext": "this is a new text!",
            "funit": "0",
            "fdate": "2008-06-23 12:00:00"}


class Viewy(BaseView):
    def __init__(self, c):
        self.request = Request()
        self.context = c
    
    def User(self, **kw):
        return UserO("test")

# -----------------------------------------------------------------
from pyramid import testing

class FormTest_db:

    def setUp(self):
        self._loadApp()
        self.request = testing.DummyRequest()
        self.request._LOCALE_ = "en"
        self.config = testing.setUp(request=self.request)
        self.view = Viewy(self.app)
        self.config.include('pyramid_chameleon')
        self.remove=[]
    
    def tearDown(self):
        self._closeApp(True)
        testing.tearDown()


    def test_form(self, **kw):
        form = HTMLForm(loadFromType="type1", context=self.app, request=Request(), app=self.app, view=self.view)
        form.Setup()
        self.assertTrue(form.GetFields())
        form._SetUpSchema()
        self.assertFalse(form.GetField("test000"))
        request = Request()
        form.LoadDefaultData()
        form.GetActions(True)
        form.GetActions(False)
        form.GetFormValue("test", request=request, method=None)
        form.GetFormValues(request)
        form.StartForm("action", defaultData={"a":1})
        form.StartForm("action")
        form.StartRequestGET("action")
        form.StartRequestPOST("action")
        form.Cancel("action")


    def test_empty(self, **kw):
        form = Form(loadFromType="type1", app=self.app, view=self.view)
        form.Setup()
        result, data = form.Extract({"ftext": ""})
        self.assertTrue(data.get("ftext")=="")
        
        form = Form(loadFromType="type2", app=self.app, view=self.view)
        form.Setup()
        result, data = form.Extract({"fstr": ""})
        self.assertTrue(data.get("fstr")=="" and data.get("ftext")==None)

        
    def test_values(self, **kw):
        form = Form(loadFromType="type1", app=self.app, view=self.view)
        form.Setup()

        v,d,e = form.Validate(data=data1_1)
        self.assertTrue(v, str(e))
        
        v,d,e = form.Validate(data1_2)
        self.assertFalse(v, e)
        
        result, data = form.Extract(data1_1)
        self.assertTrue(data)
        result, data = form.Extract(data1_2)
        self.assertTrue(data)        


    def test_values2(self, **kw):
        form = Form(loadFromType="type1", app=self.app, view=self.view)
        subsets = {"test": {"fields": ["ftext","funit"]}}
        form.subsets = subsets
        form.Setup(subset="test")
        v,d,e = form.Validate(data1_2)
        self.assertTrue(v, e)

        form = Form(loadFromType="type1", app=self.app, view=self.view)
        subsets = {"test": {"fields": ["ftext", FieldConf(**{"id": "section1", "name": "Section 1", "datatype": "unit"})]}}
        form.subsets = subsets
        form.Setup(subset="test")
        v,d,e = form.Validate(data1_2)
        self.assertTrue(v, e)

        result, data = form.Extract(data1_1)
        self.assertTrue(data)
        result, data = form.Extract(data1_2)
        self.assertTrue(data)


    def test_values3(self, **kw):
        form = Form(loadFromType="type1", app=self.app, view=self.view)
        subsets = {"test": {"fields": ["ftext", FieldConf(id="section1", name="Section 1", datatype="string", schema=schema.String())]}}
        form.subsets = subsets
        form.Setup(subset="test")
        v,d,e = form.Validate(data1_2)
        self.assertTrue(v, e)

        result, data = form.Extract(data1_1)
        self.assertTrue(data)
        result, data = form.Extract(data1_2)
        self.assertTrue(data)


    def test_html(self, **kw):
        form = HTMLForm(loadFromType="type1", app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = "upload"
        form.css_class = "niveform"
        form.Setup()

        v,d,e = form.Validate(data1_1)
        self.assertTrue(v, str(e))
        
        v,d,e = form.Validate(data1_2)
        self.assertFalse(v, e)
        form.Render(d, msgs=None, errors=None)
        
        result, data = form.Extract(data1_1)
        self.assertTrue(data)
        result, data = form.Extract(data1_2)
        self.assertTrue(data)
        
        
    def test_html2(self, **kw):
        form = HTMLForm(loadFromType="type1", app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = "upload"
        form.css_class = "niveform"
        form.subsets = {"test": {"fields": ["ftext","funit"]}}
        form.Setup(subset="test")
        v,d,e = form.Validate(data1_2)
        self.assertTrue(v, e)
        form.Render(d, msgs=None, errors=None)


    def test_html3(self, **kw):
        form = HTMLForm(loadFromType="type1", app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = "upload"
        form.css_class = "niveform"
        form.subsets = {"test": {"fields": ["ftext", FieldConf(**{"id": "section1", "name": "Section 1", "datatype": "number"})]}}
        form.Setup(subset="test")
        v,d,e = form.Validate(data1_2)
        self.assertTrue(v, e)
        form.Render(d, msgs=None, errors=None)


    def test_tool(self, **kw):
        tool = self.app.GetTool("nive.tools.example")
        form = ToolForm(loadFromType=tool.configuration, context=tool,app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = "upload"
        form.css_class = "niveform"
        form.actions = [
            Conf(**{"id": "default", "name": "Speichern", "method": "StartForm", "description": "", "hidden":True, "css_class":"", "html":"", "tag":""}),
            Conf(**{"id": "run",       "name": "Speichern", "method": "RunTool",      "description": "", "css_class":"", "html":"", "tag":""}),
            Conf(**{"id": "cancel",  "name": "Abbrechen", "method": "Cancel",    "description": "", "css_class":"", "html":"", "tag":""})
            ]
        form.Setup()
        data = {"parameter1": "True", "parameter2": "test"}

        form.Process()
        req = {"run$":1}
        req.update(data)
        form.request = req
        form.Process()
        req = {"cancel$":1}
        form.request = req
        form.Process()
        
        form.subsets = {"test": {"fields": ["parameter1"]}}
        form.Setup("test")
        form.Process()
        req = {"run$":1}
        req.update(data)
        form.request = req
        form.Process()
        req = {"cancel$":1}
        form.request = req
        form.Process()

        form.subset = "test"
        form.subsets = {"test": {"fields": ["parameter1", FieldConf(**{"id": "section1", "name": "Section 1", "datatype": "lines"})]}}
        form.Setup("test")
        form.Process()
        req = {"run$":1}
        req.update(data)
        form.request = req
        form.Process()
        req = {"cancel$":1}
        form.request = req
        form.Process()
        

    def test_json(self, **kw):
        form = JsonMappingForm(request=Request(), app=self.app, view=self.view)
        form.fields = (
            FieldConf(id="parameter1", datatype="text", size=1000),
            FieldConf(id="parameter2", datatype="string", size=100),
        )
        form.Setup()

        data = {"parameter1": "True", "parameter2": "test"}
        r,v,e = form.Validate(data)
        self.assertTrue(r, e)
        self.assertTrue(isinstance(v, dict))
        data = {"parameter1": "True", "parameter2": "test"}
        r,v = form.Extract(data)
        self.assertTrue(r, v)
        self.assertTrue(isinstance(v, dict))
        

    def test_actions(self, **kw):
        form = HTMLForm(loadFromType="type1", app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = "upload"
        form.css_class = "niveform"

        # create
        form.actions = [
        Conf(**{"id": "default", "method": "StartForm","name": "Initialize", "hidden":True,  "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "create",  "method": "CreateObj","name": "Create",     "hidden":False, "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "cancel",  "method": "Cancel",   "name": "Cancel",     "hidden":False, "description": "", "css_class":"", "html":"", "tag":""})
        ]
        form.Setup()
        a = form.GetActions(removeHidden=False)
        self.assertTrue(len(a)==3)
        a = form.GetActions(removeHidden=True)
        self.assertTrue(len(a)==2)


    def test_fields(self, **kw):
        form = HTMLForm(loadFromType="type1", app=self.app, view=self.view, request=Request())
        form.formUrl = "form/url"
        form.cssID = "upload"
        form.css_class = "niveform"
        # create
        form.Setup()

        f = form.GetFields(removeReadonly=True)
        self.assertTrue(len(f)==len(db_app.type1.data)+len(db_app.appconf.meta)-len(ReadonlySystemFlds)-len(UserFlds))
        f = form.GetFields(removeReadonly=False)
        self.assertTrue(len(f)==len(db_app.type1.data)+len(db_app.appconf.meta)-len(ReadonlySystemFlds))



    def test_obj(self, **kw):
        root = self.app.GetRoot()
        v = Viewy(self.app)
        form = ObjectForm(loadFromType="type1", context=root, view=v, request=Request(), app=self.app)
        form.formUrl = "form/url"
        form.cssID = "upload"
        form.css_class = "niveform"

        # create
        form.actions = [
        Conf(**{"id": "default", "method": "StartForm","name": "Initialize", "hidden":True,  "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "create",  "method": "CreateObj","name": "Create",     "hidden":False, "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "cancel",  "method": "Cancel",   "name": "Cancel",     "hidden":False, "description": "", "css_class":"", "html":"", "tag":""})
        ]
        form.Setup(addTypeField = True)
        
        count = self.app.db.GetCountEntries()
        result, data, action=form.Process()
        self.assertTrue(result)
        self.assertEqual(action.id,"default")
        self.assertEqual(count, self.app.db.GetCountEntries())

        req = {"create$":1, "pool_type":"type1"}
        req.update(data1_1)
        form.request = req
        result, data, action=form.Process(values={"fnumber":999})
        self.assertTrue(result)
        self.assertEqual(action.id,"create")
        self.assertEqual(count+1, self.app.db.GetCountEntries())
        self.remove.append(result.id)
        
        req = {"cancel$":1}
        form.request = req
        result, data, action=form.Process()
        self.assertTrue(result)
        self.assertEqual(action.id,"cancel")
        self.assertEqual(count+1, self.app.db.GetCountEntries())
        
        form = ObjectForm(loadFromType="type1", context=root, view=v, request=Request(), app=self.app)
        form.subsets = {"test": {"fields": ["ftext","funit"], 
                                  "actions": ["default", "create","cancel"]}}
        form.Setup(subset = "test", addTypeField = True)
        result, data, action=form.Process()
        self.assertTrue(result)
        self.assertEqual(action.id,"default")
        self.assertEqual(count+1, self.app.db.GetCountEntries())

        req = {"create$":1, "pool_type":"type1"}
        req.update(data1_2)
        form.request = req
        result, data, action=form.Process()
        self.assertTrue(result)
        self.assertEqual(action.id,"create")
        self.assertEqual(count+2, self.app.db.GetCountEntries())
        self.remove.append(result.id)
        
        req = {"cancel$":1}
        form.request = req
        result, data, action=form.Process()
        self.assertTrue(result)
        self.assertEqual(action.id,"cancel")
        self.assertEqual(count+2, self.app.db.GetCountEntries())

        form = ObjectForm(loadFromType="type1", context=root, view=v, request=Request(), app=self.app)
        form.subsets = {"test": {"fields": ["ftext", FieldConf(**{"id": "section1", "name": "Section 1", "datatype": "email"})], 
                                  "actions": ["default", "create","cancel"]}}
        form.Setup(subset = "test", addTypeField = True)
        result, data, action=form.Process()
        self.assertTrue(result)
        self.assertEqual(action.id,"default")
        self.assertEqual(count+2, self.app.db.GetCountEntries())
        
        req = {"create$":1, "pool_type":"type1"}
        req.update(data1_2)
        form.request = req
        result, data, action=form.Process()
        self.assertTrue(result)
        self.assertEqual(action.id,"create")
        self.assertEqual(count+3, self.app.db.GetCountEntries())
        self.remove.append(result.id)

        req = {"cancel$":1}
        form.request = req
        result, data, action=form.Process()
        self.assertTrue(result)
        self.assertEqual(action.id,"cancel")
        self.assertEqual(count+3, self.app.db.GetCountEntries())


    def test_obj2(self, **kw):
        user = UserO("test")
        root = self.app.GetRoot()
        obj = root.Create("type1", data1_2, user)
        self.remove.append(obj.id)
        v = Viewy(self.app)

        form = ObjectForm(loadFromType="type1", context=obj, view=v, request=Request(), app=self.app)
        form.formUrl = "form/url"
        form.cssID = "upload"
        form.css_class = "niveform"
        count = self.app.db.GetCountEntries()
        # edit
        form.actions = [
        Conf(**{"id": "default", "method": "StartObject","name": "Initialize",    "hidden":True, "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "save",       "method": "UpdateObj","name": "Save",         "hidden":False, "description": "", "css_class":"", "html":"", "tag":""}),
        Conf(**{"id": "cancel",  "method": "Cancel",    "name": "Cancel",         "hidden":False, "description": "", "css_class":"", "html":"", "tag":""})
        ]
        form.Setup()
        form.Process()
        req = {"save$":1}
        req.update(data1_1)
        form.request = req
        form.Process()
        req = {"cancel$":1}
        form.request = req
        form.Process()
        d = form.LoadObjData()
        self.assertEqual(count, self.app.db.GetCountEntries())

        form = ObjectForm(loadFromType="type1", context=obj, view=v, request=Request(), app=self.app)
        form.subsets = {"test": {"fields": ["ftext","funit"], 
                                  "actions": ["defaultEdit","edit","cancel"]}}
        form.Setup(subset = "test")
        form.Process()
        req = {"edit$":1}
        req.update(data1_2)
        form.request = req
        form.Process(values={"fnumber":333})
        req = {"cancel$":1}
        form.request = req
        form.Process()
        self.assertEqual(count, self.app.db.GetCountEntries())

        form = ObjectForm(loadFromType="type1", context=obj, view=v, request=Request(), app=self.app)
        form.subsets = {"test": {"fields": ["ftext", FieldConf(**{"id": "section1", "name": "Section 1", "datatype": "url"})],
                                  "actions": ["defaultEdit","edit","cancel"]}}
        form.subset = "test"
        form.Setup(subset = "test")
        form.Process()
        req = {"edit$":1}
        req.update(data1_2)
        form.request = req
        form.Process()
        req = {"cancel$":1}
        form.request = req
        form.Process()
        self.assertEqual(count, self.app.db.GetCountEntries())

        form = ObjectForm(loadFromType="type1", context=obj, view=v, request=Request(), app=self.app)
        form.subsets = {"test": {"fields": ["ftext", FieldConf(**{"id": "section1", "name": "Section 1", "datatype": "unitlist"})],
                                  "actions": ["defaultEdit","edit","cancel"]}}
        try:
            form.Setup(subset="test3")
            form.Process()
            self.assertTrue(False)
        except ConfigurationError:
            pass
        self.assertEqual(count, self.app.db.GetCountEntries())


    def test_json(self, **kw):
        user = UserO("test")
        root = self.app.GetRoot()
        obj = root.Create("type1", data1_2, user)
        obj.data["fjson"] = {}
        obj.Commit(user=user)
        self.remove.append(obj.id)
        v = Viewy(self.app)

        form = JsonMappingForm(request=Request(),app=self.app,context=obj, view=v)
        form.fields = (
            FieldConf(id="parameter1", datatype="string", size=1000),
            FieldConf(id="parameter2", datatype="string", size=100),
        )
        form.jsonDataField = "fjson"
        form.Setup()

        data = {"parameter1": "True", "parameter2": "test"}
        form.request = data
        form.Process()
        
        data["edit$"] = 1
        form.request = data
        form.Process()

        self.assertTrue(obj.data.get("ftext"))
        

class FormTest_db_sqlite(FormTest_db, __local.SqliteTestCase):
    """
    see tests.__local
    """

class FormTest_db_mysql(FormTest_db, __local.MySqlTestCase):
    """
    see tests.__local
    """
    
class FormTest_db_pg(FormTest_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """

