
"""
FormWorker for reform
---------------------
This is the connection between nive.Form and reform and maps FieldConf()
to schema nodes. 
"""

from pkg_resources import resource_filename
from nive.components.reform.template import ZPTRendererFactory

from nive.i18n import _
from nive.i18n import translate
from nive.definitions import ModuleConf, ViewModuleConf

from nive.components.reform.schema import *
from nive.components.reform.widget import *
from nive.components.reform.form import Button



# view module definition ------------------------------------------------------------------
#@nive_module
configuration = ModuleConf(
    id = "reformed",
    name = u"Form widgets and resources",
    context = "nive.components.reform.reformed",
    views = (ViewModuleConf(static="nive.components.reform:static",id="reform"),),
)

template_dir = resource_filename('nive.components.reform', 'templates/')
zpt_renderer = ZPTRendererFactory([template_dir], translator=translate)



def SchemaFactory(form, fields, actions, force=False):
    """
    converts the fields to colander schema nodes including widget.
    If fielddef has node set and force is false node is used as widget. To overwrite set
    force = True.
    
    SchemaNode(...)
    """
    kwWidget = {"form": form}

    nodeMapping = {
        "string": string_node,
        "number": number_node,
        "float": float_node,
        "bool": bool_node,
        "htext": htext_node,
        "text": text_node,
        "code": code_node,
        "json": json_node,
        "file": file_node,
        "date": date_node,
        "datetime": datetime_node,
        "list": list_node,
        "radio": radio_node,
        "mselection": mselection_node,
        "mcheckboxes": mcheckboxes_node,
        "lines": lines_node,
        "email": email_node,
        "url": url_node,
        "urllist": urllist_node,
        "password": password_node,
        "unit": unit_node,
        "unitlist": unitlist_node,
        "timestamp": timestamp_node
    }

    nodes = []
    for field in fields:
        # use field configuration node: node must be a valid 
        # SchemaNode 
        if field.get("node") and not force:
            sc.add(field.get("node"))
            continue
        
        # default node setup
        # for all fields
        kw = {
            "name": field.id,
            "title": field.name,
            "description": field.description
        }
        # custom validator
        if field.settings and field.settings.get("validator"):
            kw["validator"] = field.settings["validator"]
        # custom widget
        if field.settings and field.settings.get("widget"):
            kw["widget"] = field.settings["widget"]

        # setup missing and default value
        if not field.required:
            kw["missing"] = null # or "" ?
        if field.default != None:
            kw["default"] = field.default 
            
        ftype = field.datatype
        if field.hidden:
            n = hidden_node(field, kw, kwWidget, form)

        else:
            n = apply(nodeMapping[ftype], (field, kw, kwWidget, form))
            
        # add node to form
        if not n:
            continue
        nodes.append(n)
            
    # add buttons
    buttons = []
    for action in actions:
        if action.get("hidden"):
            continue
        buttons.append(Button(name=u"%s%s"%(action.get("id"), form.actionPostfix), 
                              title=action.get("name"), 
                              action=action, 
                              cls=action.get("cls", "btn submit")))

    # returns the prepared nodes and buttons
    return nodes, buttons


def hidden_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        kw["widget"] = HiddenWidget(**kwWidget)
    return SchemaNode(String(), **kw)

def string_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",255))
    if not "widget" in kw:
        kw["widget"] = TextInputWidget(size=field.get("len",50), **kwWidget)
    return SchemaNode(String(), **kw)

def number_node(field, kw, kwWidget, form):
    return SchemaNode(Integer(), **kw)

def float_node(field, kw, kwWidget, form):
    return SchemaNode(Float(), **kw)

def bool_node(field, kw, kwWidget, form):
    return SchemaNode(Boolean(), **kw)

def htext_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",1000000))
    if not "widget" in kw:
        width = field.settings.get("width", 500)
        height = field.settings.get("height", 250)
        kw["widget"] = RichTextWidget(width=width, height=height, **kwWidget)
    return SchemaNode(String(), **kw)

def text_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",1000000))
    if not "widget" in kw:
        kw["widget"] = TextAreaWidget(rows=10, cols=60, **kwWidget)
    return SchemaNode(String(), **kw)

def code_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",1000000))
    if not "widget" in kw:
        kw["widget"] = CodeTextWidget(**kwWidget)
    return SchemaNode(String(), **kw)

def json_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",1000000))
    if not "widget" in kw:
        kw["widget"] = CodeTextWidget(**kwWidget)
    return SchemaNode(String(), **kw)

def file_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        kw["widget"] = FileUploadWidget2(**kwWidget)
    return SchemaNode(FileData2(), **kw)
    #    kw["widget"] = FileUploadWidget(tmpstore, **kwWidget)
    #    n = SchemaNode(FileData(), **kw)

def date_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        kw["widget"] = DateInputWidget(**kwWidget)
    #kw["options"] = {'dateFormat': 'yyyy/mm/dd', 'timeFormat': 'hh:mm:ss', 'separator': ' '}
    return SchemaNode(Date(), **kw)

def datetime_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        kw["widget"] = DateTimeInputWidget(**kwWidget)
    #kw["options"] = {'dateFormat': 'yyyy/mm/dd', 'timeFormat': 'hh:mm:ss', 'separator': ' '}
    return SchemaNode(DateTime(), **kw)

def list_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        v = form.app.root().LoadListItems(field, form.context)
        if field.settings and field.settings.get("addempty"):
            v.insert(0,{"id":u"","name":u""})
        values = [(a["id"],a["name"]) for a in v]
        kw["widget"] = SelectWidget(values=values, **kwWidget)
        if field.settings.get("controlset"):
            kw["widget"].template = 'select_controlset'
            kw["widget"].css_class = ''
    return SchemaNode(String(), **kw)

def radio_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        v = form.app.root().LoadListItems(field, form.context)
        values=[(a["id"],a["name"]) for a in v]
        kw["widget"] = RadioChoiceWidget(values=values, **kwWidget)
    return SchemaNode(String(), **kw)

def mselection_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        v = form.app.root().LoadListItems(field, form.context)
        values=[(a["id"],a["name"]) for a in v]
        kw["widget"] = SelectWidget(values=values, size=field.get("len", 4), **kwWidget)
    return SchemaNode(List(allow_empty=True), **kw)

def mcheckboxes_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        v = form.app.root().LoadListItems(field, form.context)
        values=[(a["id"],a["name"]) for a in v]
        kw["widget"] = CheckboxChoiceWidget(values=values, **kwWidget)
    return SchemaNode(List(allow_empty=True), **kw)

def lines_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",1000000))
    if not "widget" in kw:
        kw["widget"] = TextAreaWidget(rows=10, cols=60, **kwWidget)
    return SchemaNode(Lines(), **kw)

def email_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Email()
    if not "widget" in kw:
        kw["widget"] = TextInputWidget(size=field.get("len",50), **kwWidget)
    return SchemaNode(String(), **kw)

def url_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",255))
    kw["widget"] = TextInputWidget(size=field.get("len",50), **kwWidget)
    return SchemaNode(String(), **kw)

def urllist_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",1000000))
    kw["widget"] = TextAreaWidget(rows=10, cols=60, **kwWidget)
    return SchemaNode(String(), **kw)

def password_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(min=5, max=20)
    if not "widget" in kw:
        if field.settings.get("single",False):
            kw["widget"] = PasswordWidget(size=field.get("len",50), **kwWidget)
        else:    
            kw["widget"] = CheckedPasswordWidget(size=field.get("len",50), update=field.settings.get("update",False), **kwWidget)
    return SchemaNode(String(), **kw)

def unit_node(field, kw, kwWidget, form):
    return SchemaNode(Integer(), **kw)

def unitlist_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",255))
    if not "widget" in kw:
        kw["widget"] = TextInputWidget(size=field.get("len",50), **kwWidget)
    return SchemaNode(String(), **kw)

def timestamp_node(field, kw, kwWidget, form):
    # readonly
    return None

