
"""
FormWorker for reform
---------------------
This is the connection between nive.Form and reform and maps FieldConf()
to schema nodes. 
"""

from pkg_resources import resource_filename
from nive.components.reform.template import ZPTRendererFactory

from nive.i18n import translate
from nive.definitions import ModuleConf, ViewModuleConf
from nive.helper import LoadListItems, ResolveName

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

    nodes = []
    for field in fields:
        # use field configuration node: node must be a valid 
        # SchemaNode 
        if field.get("node") and not force:
            nodes.append(field.node)
            continue
        
        # Default node setup
        # Basic values for all fields and widgets
        kw = {
            "name": field.id,
            "title": field.name,
            "description": field.description,
            "configuration": field
        }
        kwWidget = {
            "form": form,
            "configuration": field
        }
        if field.settings and isinstance(field.settings, dict):
            kwWidget.update(field.settings)

        # ----------------------------------------------------------
        # bw 0.9.12 -> moved from `field.settings` to `field`
        # to be removed in future. use field.widget and field.validator instead. 
        if field.settings and field.settings.get("validator"):
            kw["validator"] = field.settings["validator"]
        if field.settings and field.settings.get("widget"):
            kw["widget"] = field.settings["widget"]
        # ----------------------------------------------------------

        # custom validator
        if field.get("validator"):
            kw["validator"] = field.validator
        # custom widget
        if field.get("widget"):
            kw["widget"] = field.widget

        # setup custom widgets
        if "widget" in kw and kw["widget"]:
            widget = kw["widget"]
            if isinstance(widget, basestring):
                widget = ResolveName(widget)
                kw["widget"] = widget(**kwWidget)
            elif callable(widget):
                kw["widget"] = widget(**kwWidget)
            else:
                widget.form = form
                widget.configuration = field
                kw["widget"] = widget

        # setup custom validator
        if "validator" in kw and kw["validator"]:
            validator = kw["validator"]
            if isinstance(validator, basestring):
                validator = ResolveName(validator)
            kw["validator"] = validator

        # setup missing and default value
        if not field.required:
            kw["missing"] = null # or "" ?
        if field.default is not None:
            kw["default"] = field.default

        if field.get("schema"):
            n = SchemaNode(field.get("schema"), **kw)
            
        elif field.hidden:
            n = hidden_node(field, kw, kwWidget, form)

        else:
            n = apply(nodeMapping[field.datatype], (field, kw, kwWidget, form))
            
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
        kw["widget"] = TextInputWidget(**kwWidget)
    return SchemaNode(String(), **kw)

def number_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        kw["widget"] = TextInputWidget(**kwWidget)
    return SchemaNode(Integer(), **kw)

def float_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        kw["widget"] = TextInputWidget(**kwWidget)
    return SchemaNode(Float(), **kw)

def bool_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        kw["widget"] = CheckboxWidget(**kwWidget)
    return SchemaNode(Boolean(), **kw)

def htext_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",1000000))
    if not "widget" in kw:
        kw["widget"] = RichTextWidget(**kwWidget)
    return SchemaNode(String(), **kw)

def text_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",1000000))
    if not "widget" in kw:
        kw["widget"] = TextAreaWidget(**kwWidget)
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
    return SchemaNode(Date(), **kw)

def datetime_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        kw["widget"] = DateTimeInputWidget(**kwWidget)
    return SchemaNode(DateTime(), **kw)

def time_node(field, kw, kwWidget, form):
    if not "widget" in kw:
        kw["widget"] = TextInputWidget(**kwWidget)
    return SchemaNode(Time(), **kw)

def list_node(field, kw, kwWidget, form):
    v = LoadListItems(field, app=form.app, obj=form.context)
    if field.settings and field.settings.get("addempty"):
        # copy the list and add empty entry
        v = list(v)
        v.insert(0,{"id":u"","name":u""})
    if not "widget" in kw:
        values = [(a["id"],a["name"]) for a in v]
        kw["widget"] = SelectWidget(values=values, **kwWidget)
        if field.settings.get("controlset"):
            kw["widget"].template = 'select_controlset'
            kw["widget"].css_class = ''
    return SchemaNode(CodeList(allowed=[e["id"] for e in v]), **kw)

def radio_node(field, kw, kwWidget, form):
    v = LoadListItems(field, app=form.app, obj=form.context)
    if not "widget" in kw:
        values=[(a["id"],a["name"]) for a in v]
        kw["widget"] = RadioChoiceWidget(values=values, **kwWidget)
    return SchemaNode(CodeList(allowed=[e["id"] for e in v]), **kw)

def multilist_node(field, kw, kwWidget, form):
    v = LoadListItems(field, app=form.app, obj=form.context)
    if not "widget" in kw:
        values=[(a["id"],a["name"]) for a in v]
        if field.settings.get("controlset"):
            kw["widget"] = SelectWidget(values=values, size=1, **kwWidget)
            kw["widget"].template = 'select_controlset'
            kw["widget"].css_class = ''
        else:
            kw["widget"] = SelectWidget(values=values, **kwWidget)
    return SchemaNode(List(allow_empty=True, allowed=[e["id"] for e in v]), **kw)

def checkbox_node(field, kw, kwWidget, form):
    v = LoadListItems(field, app=form.app, obj=form.context)
    if not "widget" in kw:
        values=[(a["id"],a["name"]) for a in v]
        kw["widget"] = CheckboxChoiceWidget(values=values, **kwWidget)
    return SchemaNode(List(allow_empty=True, allowed=[e["id"] for e in v]), **kw)

def lines_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",1000000))
    if not "widget" in kw:
        kw["widget"] = TextAreaWidget(**kwWidget)
    return SchemaNode(Lines(), **kw)

def email_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Email()
    if not "widget" in kw:
        kw["widget"] = TextInputWidget(**kwWidget)
    return SchemaNode(String(), **kw)

def url_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",255))
    kw["widget"] = TextInputWidget(**kwWidget)
    return SchemaNode(String(), **kw)

def urllist_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",1000000))
    kw["widget"] = TextAreaWidget(**kwWidget)
    return SchemaNode(String(), **kw)

def password_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(min=5, max=20)
    if not "widget" in kw:
        if field.settings.get("single",False):
            kw["widget"] = PasswordWidget(**kwWidget)
        else:
            if not "update" in kwWidget:
                kwWidget["update"] = field.settings.get("update",False)
            kw["widget"] = CheckedPasswordWidget(**kwWidget)
    return SchemaNode(String(), **kw)

def unit_node(field, kw, kwWidget, form):
    return SchemaNode(Integer(), **kw)

def unitlist_node(field, kw, kwWidget, form):
    if not "validator" in kw:
        kw["validator"] = Length(max=field.get("size",255))
    if not "widget" in kw:
        kw["widget"] = TextInputWidget(**kwWidget)
    return SchemaNode(Lines(), **kw)

def timestamp_node(field, kw, kwWidget, form):
    # readonly
    return None

def nlist_node(field, kw, kwWidget, form):
    # unused
    return None

def binary_node(field, kw, kwWidget, form):
    # unused
    return None

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
    "time": time_node,
    "list": list_node,
    "radio": radio_node,
    "multilist": multilist_node,
    "checkbox": checkbox_node,
    "lines": lines_node,
    "email": email_node,
    "url": url_node,
    "urllist": urllist_node,
    "password": password_node,
    "unit": unit_node,
    "unitlist": unitlist_node,
    "timestamp": timestamp_node,
    "nlist": nlist_node,
    "binary": binary_node,
    # bw 0.9.23
    "mselection": multilist_node,
    "mcheckboxes": checkbox_node,
}

