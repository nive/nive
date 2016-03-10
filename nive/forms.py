# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

"""
nive Form description
------------------------
This class manages cms integration, field configuration, actions and form processing. 
Rendering, validation and data extraction is not included and requires a separate form 
library (nive.components.reform).

nive Forms can be connected to existing object or tool configurations and reuse all
therein defined fields for forms. To setup a form like this use ``Setup(subset='action to handled')`` 
to load fields, actions, subsets automatically from the objects configuration. 

A form does represent a single action but a set of form fields and multiple actions. nive forms can 
be rendered as ``subsets`` with a reduced selection of fields and different actions. 

This is an example to be used in object view code: ::

    form = ObjectForm(view=self, 
                      loadFromType=self.context.configuration)
    form.Setup(subset="edit") 
    # process and render the form.
    result, data, action = form.Process()

*view* must be an instance of `nive.views.BaseView`.  
*data* will contain the rendered HTML whether the is loaded for the first time, validated ok or 
not. *result* will be *false* if the form input did not validate. The *ObjectForm* already includes 
all necessary functions to load data initially, create an object and store data for existing objects.
All you have to do is switch the subset from *edit* to *create*. ::

    form = ObjectForm(view=self,
                      loadFromType=self.context.configuration)
    form.Setup(subset="create")
    # process and render the form.
    result, data, action = form.Process()

The configuration is loaded from the object configuration itself so all field settings are 
dynamically included. In fact the example above works for *any* object type.

Form action callback methods use the following footage: ::

    def Method(self, action, **kw):
        # ...
        return result, data

These callback methods are automatically looked up and executed in Process(). Use action.method to
link a method to a specific form action. Pass `user` as kw argument if the forms view attribute is 
None. If form.view is set view.User() is used to lookup the current user.

A custom HTMLForm example: ::

    form = HTMLForm(view=self)
    form.actions = [
        Conf(id="default",    method="StartForm",             name=u"Initialize",          hidden=True),
        Conf(id="create",     method="ReturnDataOnSuccess",   name=u"Create a new group",  hidden=False),
    ]
    form.fields = [
        FieldConf(id="id",   name=u"Group id",   datatype="string", size="20", required=True),
        FieldConf(id="name", name=u"Group name", datatype="string", size="40", required=True)
    ]
    def onsuccess(data):
        data["id"] = "prefix:"+data["id"]
    form.ListenEvent("success", onsuccess)
    form.Setup()
    data, html, action = form.Process()


Callback for dynamic list item loading: ::

    def loadGroups(fieldconf, object):
        return [{"id": id, "name":name}]


    FieldConf(..., listItems=loadGroups, ...)

The build in progress bar is activated by default with a delay of 500 milliseconds. So it will only
pop up if the form transmission takes some time e.g if a file upload is in progress. To disable the
progress bar or skip the delay set the attribute `HTMLForm.uploadProgressBar` to `none` or `always`.
::

    form = HTMLForm(view=self)
    # disable the progress bar
    form.uploadProgressBar = 'none' 


**Please note:** These form classes are for autogenerating forms. If you need more control over validation
or rendering it might be easier to use a form library directly.

HTML form options
-----------------
The following list describes all available form attributes and settings.

==================== ========================================================================================
Form attribute
==================== ========================================================================================
formid               (string) default = `upload`. The html element id applied to the form tag.
css_class            (string) default = `form`. The html element css class applied to the form tag.
actionPostfix        (string) default = `$`. Actions are triggered through form parameters. To prevent
                     overlapping with field names action names are extended with a postfix e.g. `create$`
method               (string) default = POST. Either POST or GET. The HTTP method used for teh form.
action               (string) default = empty. The forms action url.
anchor               (string) default = empty. Adds an anchor to urls if set.
uploadProgressBar    (string) default = auto. Either auto, none or always. Defines when the progress bar is
                     displayed.
use_ajax             (bool) default = False. Enable or disable ajax form submissions.
renderSuccess        (bool) default = True. If True the whole form will be rendered after successful
                     submission. If False messages only will be returned.
successResponseBody  (string/callback) This option enables you to overwrite the complete response body on
                     success. Use a callback to generate a dynamic response. The callback must take one
                     parameter: the form instance and return a unicode string.
redirectSuccess      (string/callback) Redirect the browser to a new location on success. See below for a
                     list of options.
redirectCancel       (string/callback) Redirect the browser to a new location on cancel. See below for a list
                     of options.
==================== ========================================================================================

Url placeholders to be used with `redirectCancel` and `redirectSuccess`. The placeholders are automatically resolved
to a valid url for the current context ::

- obj_url
- obj_folder_url
- parent_url
- page_url
- page_url_anchor

`redirectCancel` and `redirectSuccess` can also be a callable. It is called with two parameters
`context` and `view class instance`. E.g. ::

    def makeUrl(context, view):
        return view.GetUrl(context) + "?query=" + view.GetFormValue('query')


Form styling options
====================
By default 3 column form layouts are used. Each column can get a custom css class by setting e.g. ::

    form.widget.settings["column1_css"] = "span4"
    form.widget.settings["column2_css"] = "span8"
    form.widget.settings["column3_css"] = "none"

To switch to a one column layout use the following code: ::

    form.widget.item_template = "field_onecolumn"
    form.widget.action_template = "form_actions_onecolumn"

Replacing default widgets,schema or validators
==============================================
::

    FieldConf(id="ftext", datatype="text", size=1000, name="ftext",

          # pass in a custom widget and settings as kw argument
          widget="nive.components.reform.widget.FileToDataUploadWidget",

          settings={"base64": True},

          # pass in a custom schema as kw argument
          schema=String(),

          # pass in a custom validator
          validator=myValidator
    ),


Control sets for Select and Radio fields
========================================
Conditional sets can be automatically shown and hidden by setting a lists option `controlset:True`
and extending each listitem with a fields list. :: 

    FieldConf(id="flist",   
        datatype="list",   
        size=100,  
        name="flist", 
        settings={"controlset":True},
        listItems=[Conf(id="item 1", name="Item 1", 
                        fields=[FieldConf(id="ftext",datatype="text",size=10,name="ftext")]),
                   Conf(id="item 2", name="Item 2", 
                        fields=[FieldConf(id="fnum",datatype="number",size=8,name="fnum")])
        ]
    )

By default additional fields added as control fields will be treated as top level form fields. Control field data
can be accessed like any other fields data. The controlset option is primarily a visual extension to make
the more user friendly by showing some fields only in a certain context.

Example
=======
Internally the form uses a structure like in the following manually defined form example ::

    fields  = [
      FieldConf(id="ftext",   datatype="text",   size=1000, name="ftext", fulltext=1),
      FieldConf(id="fnumber", datatype="number", size=8,    name="fnumber", required=1),
      FieldConf(id="fdate",   datatype="datetime", size=8,  name="fdate"),
      FieldConf(id="flist",   datatype="list",   size=100,  name="flist", 
                listItems=[{"id": "item 1", "name":"Item 1"},
                           {"id": "item 2", "name":"Item 2"}]),
      FieldConf(id="fmselect", datatype="multilist", size=50, name="fmselect"),
    ]
    
    actions = [
      Conf(id="default",    method="StartForm", name="Initialize", hidden=True),
      Conf(id="defaultEdit",method="LoadUser",  name="Initialize", hidden=True),
      Conf(id="create",     method="AddUser",   name="Create",     hidden=False),
      Conf(id="edit",       method="Update",    name="Edit",       hidden=False)
    ]
    
    subsets = {
      "create": {"fields":  ["ftext", "fnumber", "fdate"], 
                 "actions": ["create"],
                 "defaultAction": "default"},
      "create2":{"fields":  ["ftext", "fnumber", "fdate", "flist", "fmselect"], 
                 "actions": ["create"],
                 "defaultAction": "default"},
      "edit":   {"fields":  ["ftext"], 
                 "actions": ["edit"],
                 "defaultAction": "defaultEdit"},
    }
    
    form = Form(view=self)
    form.fields = fields
    form.actions = actions
    form.subsets = subsets
    form.Setup(subset="create")
    # validating data
    result,data,errors = form.Validate(data)
    
"""

import copy, json
from types import StringType

from pyramid.url import static_url
from pyramid.httpexceptions import HTTPBadRequest

from nive.definitions import Conf, FieldConf, ConfigurationError
from nive.definitions import ISort
from nive.events import Events

from nive.i18n import _, translate
from nive.components import reform
from nive.components.reform.form import Form as ReForm
from nive.components.reform.schema import null, Invalid
from nive.components.reform.exception import ValidationFailure

from nive.components.reform.reformed import SchemaFactory
from nive.components.reform.reformed import zpt_renderer


"""
0.9.7 changed nive.Form:
- renamed parameter `redirect_success` to `redirectSuccess` and pass as **kw argument to functions
- form action method footage has changed: `def Method(self, action, **kw)`

0.9.4 changed nive.Form:
- __init__ parameters if view is not None: app, request, context are extracted from view context
- added Setup(subset) function
- removed LoadConfiguration()
- ObjectForm.AddTypeField() removed. Use Setup(addTypeField=True).
- form conf changed: object.configuration.forms = {"subset": {"fields": [...], "actions": [...]}}
- changed password widgets
"""

class Form(Events, ReForm):
    """
    Base form class.
    """
    defaultSchemaFactory = SchemaFactory
    default_renderer = zpt_renderer

    # form configuration values
    fields = None
    actions = None
    subsets = None
    subset = None
    loadFromType = None
    
    
    def __init__(self, view=None, loadFromType=None, context=None, request=None, app=None, **kw):
        """
        Initialize form context. If view is not None and context, request, app are automatically
        extracted from the view object. Form fields and actions are processed in Setup(). 
        
        Please note: `view` must be an instance of `nive.views.BaseView`  
        """
        # form context
        self.view = view
        self.context = context or view.context if view else None
        self.request = request or view.request if view else None
        if app is not None:
            self.app = app
        else:
            self.app = self.context.app if self.context else None
        
        if loadFromType:
            self.loadFromType = loadFromType

        # optional form parameters
        self.title = u""
        self.description = u""
        self.formid = u""
        self.startEmpty = False
        self.method = u"POST"
        
        # reform setup
        self._c_form = None
        self._c_fields = None
        self._c_actions = None
        super(Form, self).__init__(**kw)
        
        self.Signal("init")
            
            
    def Setup(self, subset=None):
        """
        1) Load fields from object definition
        2) Loads subsets and actions from object form definition
        
        Event
        - setup() after fields have been loaded
        """
        self._c_form = None
        self._c_fields = None
        self._c_actions = None
        self.subset=subset

        subsets=self.subsets
        config = None

        # load form fields
        if self.loadFromType:
            typeOrConfiguration = self.loadFromType
            if isinstance(typeOrConfiguration, basestring):
                config = self.app.GetObjectConf(typeOrConfiguration)
                if not config:
                    raise ConfigurationError, "Type not found (%s)" % (str(typeOrConfiguration))
            else:
                config = typeOrConfiguration
            self.loadFromType = config
            if not subsets:
                try:
                    # try to load subset names from configuration
                    self.subsets = subsets = config.forms
                except AttributeError:
                    pass
                
        
        # unconfigured form
        if not subset and not self.subsets and not self.fields:
            if not config or (not config.forms and not config.data):
                raise ConfigurationError, "No form fields defined"
        # unknown subset
        if subset and (not subsets or not subset in subsets):
            raise ConfigurationError, "Unknown form subset"

        # field lookup
        #(1) subsets[subset]["fields"]
        #(x) subsets[subset]
        #(3) type["form"][subset]["fields"]
        #(x) type["form"][subset]
        #(5) fields
        #(6) config.fields
        #(7) *fields.controlset=True -> field.listItems[].fields
        temp = None
        if subsets and subset in subsets and "fields" in subsets[subset]:
            #(1)
            temp = subsets[subset]["fields"]
        elif config and "forms" in config and config.forms and subset in config.forms and "fields" in config.forms[subset]:
            #(3)
            temp = config.forms[subset]["fields"]
        elif self.fields:
            temp = self.fields
        elif config and self.app:
            temp = list(self.app.GetAllMetaFlds(ignoreSystem = True)) + list(config.data)
        if not temp:
            raise ConfigurationError, "No form fields defined"
        # lookup field configurations
        self._c_fields = []
        for f in temp:
            if isinstance(f, basestring):
                fld = None
                if self.fields:
                    for a in config.data:
                        if a.id == f:
                            fld = a
                            break
                elif config:
                    for a in config.data:
                        if a.id == f:
                            fld = a
                            break
                if not fld:
                    fld = self.app.GetMetaFld(f)
                if not fld:
                    raise ConfigurationError, "Form field lookup failed: " + f
                f = fld
            self._c_fields.append(f)
            # add controlset fields
            if f.settings.get("controlset"):
                items = f.listItems
                if not isinstance(items, (list, tuple)):
                    items = items(f, self.context)
                for item in items:
                    if not item.get("fields"):
                        continue
                    for controlf in item.fields:
                        self._c_fields.append(controlf)
                    
        
        # action lookup
        #(1) subsets[subset]["actions"]
        #(2) type["form"][subset]["actions"]
        #(3) actions 
        temp = None
        if subsets and subset in subsets:
            if isinstance(subsets[subset], dict) and "actions" in subsets[subset]:
                #(1)
                temp = subsets[subset]["actions"]
        elif config and "forms" in config and config.forms and subset in config.forms:
            if isinstance(config.forms[subset], dict) and "actions" in config.forms[subset]:
                #(3)
                temp = config.forms[subset]["actions"]
        elif self.actions:
            temp = self.actions
        if temp:
            # lookup action configurations
            self._c_actions = []
            for a in temp:
                if isinstance(a, basestring):
                    action = None
                    if self.actions:
                        for v in self.actions:
                            if v.id == a:
                                action = v
                                break
                    if not action:
                        continue
                        # raise ConfigurationError, "Form action lookup failed: " + a
                    a = action
                self._c_actions.append(a)

        if subsets and subset in subsets and "options" in subsets[subset]:
            self.ApplyOptions(subsets[subset]["options"])

        self.Signal("setup")


    def ApplyOptions(self, settings):
        """
        Applies a set of form settings to the current form. You can also pass in
        widget settings py prefixing the key with `widget.` E.g. ::

            settings = {}
            settings["widget.item_template"] = "field_onecolumn"
            settings["widget.action_template"] = "form_actions_onecolumn"

        :param settings: dict with form settings
        :return: nothing
        """
        for k,v in settings.items():
            if k.startswith(u"widget."):
                setattr(self.widget, k[len(u"widget."):], v)
                del settings[k]
            if k == u"useAjax":
                # rename
                del settings[k]
                settings[u"use_ajax"] = v

        self.__dict__.update(settings)


    def _SetUpSchema(self, force=False):
        """
        set up form schema for configured configuration.
        """
        if self._c_form:
            return 
        fields = self.GetFields()
        actions = self.GetActions(True)
        schemaNodes, buttons = self.defaultSchemaFactory(fields, actions, force)
        # setup nodes
        for n in schemaNodes:
            self.add(n)
        self.buttons = buttons
        self._c_form = True
        return 


    # Data extraction and validation --------------------------------------------------------------------------------------------

    def Validate(self, data, removeNull=True):
        """
        Extracts fields from request, converts and validates
        
        Unlike the `ValidateSchema()` function `Validate()` validates html form widget 
        data fields and does not support raw data validation.   

        Event
        - validate(data) before validate is called
        - process(data)  after validate has succeeded, is not called if validate failed
        
        returns bool, dictionary, list (result,data,errors)
        """
        self._SetUpSchema()
        error = None
        try:
            self.Signal("validate", data=data)
            data = self.validate(data)
        except ValidationFailure, e:
            return False, e.cstruct, e
        if removeNull:
            data = dict(filter(lambda d: d[1] != null, data.items()))
        self.Signal("process", data=data)
        return True, data, None


    def ValidateSchema(self, data, removeNull=True):
        """
        Extracts fields from source data dictionary, converts and
        validates. 
        
        Unlike the `Validate()` function `ValidateSchema()` validates raw data
        and does not support html form widget data fields.   
        
        Event
        - validate(data) before validate is called
        
        returns bool, dictionary, list (result,data,errors)
        """
        self._SetUpSchema()
        self.Signal("validate", data=data)
        errors = None
        result = True
        try:
            data = self.schema.deserialize(data)
        except Invalid, e:
            errors = e.children
            result = False
        
        if removeNull:
            data = dict(filter(lambda d: d[1] != null, data.items()))
        return result, data, errors

        
    def Extract(self, data, removeNull=True, removeEmpty=False):
        """
        Extract fields from request or source data dictionary and convert
        data types without validation. 
        
        returns bool, dictionary (result, data)
        """
        self._SetUpSchema()
        result = True
        try:
            data = self.validate(data)
        except ValidationFailure, e:
            result = False
            data = e.cstruct
        except ValueError:
            return self.ExtractDeserialized(data, removeNull)

        if removeNull:
            data = dict(filter(lambda d: d[1] != null, data.items()))
        if removeEmpty:
            data = dict(filter(lambda d: d[1] not in (u"",[],()), data.items()))
        
        return result, data
    
        
    def ExtractSchema(self, data, removeNull=False, removeEmpty=False):
        """
        Extract fields from request or source data dictionary and convert
        data types without validation. 
        
        returns bool, dictionary (result, data)
        """
        self._SetUpSchema()
        errors = None
        result = True
        try:
            data = self.schema.deserialize(data)
        except Invalid, e:
            result = False

        if removeNull:
            data = dict(filter(lambda d: d[1] != null, data.items()))
        if removeEmpty:
            data = dict(filter(lambda d: d[1] not in (u"",[],()), data.items()))

        return result, data


    # Loading initital data --------------------------------------------------------------------------------------------

    def LoadObjData(self, obj=None):
        """
        Load data from existing object
        
        Event
        - loadDataObj(data, obj) after data has been looked up
        
        returns dict
        """
        if not obj:
            obj = self.context
        data = {}
        for f in self.GetFields():
            # data
            if f.datatype == "file":
                data[f.id] = obj.files[f.id]
            if f.datatype == "password":
                data[f.id] = u""
            else:
                if obj.data.has_key(f.id):
                    data[f.id] = obj.data[f.id]
                elif obj.meta.has_key(f.id):
                    data[f.id] = obj.meta[f.id]
        self.Signal("loadDataObj", data=data, obj=obj)
        return data


    def LoadDefaultData(self):
        """
        Load default data from configuration
        
        Event
        - loadDefault(data) after data has been looked up
        
        returns dict
        """
        data = dict(filter(lambda y: y[1]!=None, 
                           map(lambda x: (x["id"],x["default"]), self.GetFields())))
        self.Signal("loadDefault", data=data)
        return data


    # Field definitions and configuration --------------------------------------------------------------------------------------------

    def GetFields(self, removeReadonly=True):
        """
        Returns the list of field definitions. Readonly fields are removed by default.
        
        returns list
        """
        if not self._c_fields:
            return ()
        elif not removeReadonly:
            return self._c_fields
        return filter(lambda field: not (removeReadonly and field.readonly), self._c_fields)


    def GetActions(self, removeHidden=False):
        """
        Returns the list of form actions. Hidden actions are removed by default.
        
        returns list
        """
        if not self._c_actions:
            return ()
        elif not removeHidden:
            return self._c_actions
        return filter(lambda a: not (removeHidden and a.get("hidden",False)), self._c_actions)

    
    def GetField(self, fieldid):
        """
        Get the field configuration by field id.
        
        returns configuration or None
        """
        for f in self._c_fields:
            if f.id == fieldid:
                return f
        return None


    # form values --------------------------------------------------------------------------------------------

    def GetFormValue(self, key, request=None, method=None):
        """
        Extract single value from request
        
        returns value
        """
        if not request:
            request = self.request
        if isinstance(request, dict):
            return request.get(key)
        if not method:
            method = self.method
        try:
            if method == "POST":
                value = request.POST.getall(key)
            elif method == "GET":
                value = request.GET.getall(key)
            else:
                value = request.POST.getall(key)
                if not value:
                    value = request.GET.getall(key)
            if type(value)==StringType:
                value = unicode(value, self.app.configuration.frontendCodepage)
        except (AttributeError,KeyError):
            if method == "POST":
                value = request.POST.get(key)
            elif method == "GET":
                value = request.GET.get(key)
            else:
                value = request.POST.get(key)
                if not value:
                    value = request.GET.get(key)
            if type(value)==StringType:
                value = unicode(value, self.app.configuration.frontendCodepage)
            return value
        if not len(value):
            return None
        elif len(value)==1:
            return value[0]
        return value


    def GetFormValues(self, request=None, method=None):
        """
        Extract all values from request
        
        returns sict
        """
        if not request:
            request = self.request
        if not method:
            method = self.method
        try:
            if method == "POST":
                values = request.POST.mixed()
            elif method == "GET":
                values = request.GET.mixed()
            else:
                values = request.GET.mixed()
                values.update(request.POST.mixed())
        except AttributeError:
            try:
                if method == "POST":
                    values = request.POST
                elif method == "GET":
                    values = request.GET
                else:
                    values = {}
                    values.update(request.GET)
                    values.update(request.POST)
            except AttributeError:
                values = request
        if not values:
            return {}
        # should be unicode ?
        #cp=self.app.configuration.frontendCodepage
        #for k in values.items():
        #    if type(k[1]) == StringType:
        #        values[k[0]] = unicode(values[k[0]], cp)
        return values


    def ConvertFileUpload(self, key, method="post"):
        """
        Convert a file upload to the internal File object
        """
        value = self.GetFormValue(key, self.request, method=method)
        # prepare file
        file = self.app.db.GetFileClass()()
        file.filename = value.get('filename','')
        file.file = value.get('file')
        file.filekey = value.get('filekey')
        file.mime = value.get('mimetype')
        file.size = value.get('size')
        file.tempfile = True
        return file



class HTMLForm(Form):
    """
    Basic HTML Form
    """
    # form setup: element id, css classes, url
    formid = u"upload"
    css_class = u"form"
    actionPostfix = u"$"
    action = u""
    anchor = u""

    # display options
    uploadProgressBar = u"auto" # other possible values: none or always

    # ajax forms
    use_ajax = False

    # from defaults
    defaults = None
    defaultAction = None

    # success options
    renderSuccess = True
    successResponseBody = None   # either string or callback
    redirectSuccess = u""        # either string or callback

    # redirect urls
    redirectCancel = u""         # either string or callback

    actions = [
        Conf(id=u"default", method="StartForm",    name=u"Initialize", hidden=True,  css_class=u"",                 html=u"", tag=u""),
        Conf(id=u"edit",    method="ProcessForm",  name=u"Save",       hidden=False, css_class=u"btn btn-primary",  html=u"", tag=u""),
    ]
    subsets = {
        "edit":   {"actions": [u"edit"],    "defaultAction": "default"}
    }


    # Form actions --------------------------------------------------------------------------------------------

    def Process(self, **kw):
        """
        Processes the request and calls the required actions. kw parameter ::
        
            defaultAction: default action if none found in request. Can also be configured in subset

        `redirectSuccess` can be used to redirect on action success.

        If `renderSuccess` is set to False the form itself will not be rendered if
        the action succeeds. Only the feedback message will be rendered.
         
        Action definitions must define a callback method to process the action. 
        The callback takes two parameters: ::
    
            method(action, **kw)

        returns bool, html, dict (result, data, action)
        """
        # bw 0.9.13
        if u"renderSuccess" in kw:
            self.renderSuccess = kw[u"renderSuccess"]
        if u"redirectSuccess" in kw:
            self.redirectSuccess = kw[u"redirectSuccess"]

        # find default action
        defaultAction = None
        if self.subset:
            defaultAction = self.subsets[self.subset].get("defaultAction")
        if not defaultAction:
            defaultAction = kw.get("defaultAction") or self.defaultAction or "default"

        # find action
        action = None
        formValues = self.GetFormValues(self.request)
        actions = self.GetActions()
        for a in actions:
            if a["id"]+self.actionPostfix in formValues.keys():
                action = a
                break

        if not action and defaultAction:
            # lookup default action 
            if isinstance(defaultAction, basestring):
                for a in list(self.actions) + list(self.GetActions()):
                    if a["id"]==defaultAction:
                        action = a
                        break
            else:
                action = defaultAction

        # no action -> raise exception
        if not action:
            raise ConfigurationError, "No action to process the form found"

        # call action
        if isinstance(action["method"], basestring):
            method = getattr(self, action["method"])
        else:
            method = action["method"]
        
        # lookup and merge keyword parameter for action call
        methodKws = action.get("options")
        if methodKws:
            callKws = methodKws.copy()
            callKws.update(kw)
        else:
            callKws = kw
        result, html = method(action, **callKws)
        #try:
        #    result, html = method(action, **callKws)
        #except ValueError, e:
        #    # handle value errors as client errors, not server errors.
        #    # return a 400 Invalid request exception.
        #    raise HTTPBadRequest(str(e))
        return result, html, action


    def IsRequestAction(self, action):
        """
        Check request for the given action.
        
        returns bool
        """
        formValues = self.GetFormValues(self.request)
        return action+self.actionPostfix in formValues.keys()


    def RemoveActionsFromRequest(self):
        """
        Removes all actions from the request. If called before processing the form
        the default action will be used and the form never processed.
        """
        actions = self.GetActions()
        formValues = self.GetFormValues(self.request)
        for a in actions:
            if a["id"]+self.actionPostfix in formValues.keys():
                action = a
                try:
                    del self.request.POST[a["id"]+self.actionPostfix]
                except (AttributeError, KeyError):
                    pass
                try:
                    del self.request.GET[a["id"]+self.actionPostfix]
                except (AttributeError, KeyError):
                    pass
            

    def StartForm(self, action, **kw):
        """
        Default action. Use this function to initially render a form if:
        - startEmpty is True
        - defaultData is passed in kw
        - load form default data

        Event
        - loadDefault(data) after data has been looked up

        returns bool, html
        """
        if self.startEmpty:
            data = {}
        elif "defaultData" in kw:
            data = kw["defaultData"]
            self.Signal("loadDefault", data=data)
        else:
            data = self.LoadDefaultData()
        return True, self.Render(data)


    def StartRequestGET(self, action, **kw):
        """
        Default action. Initially loads data from request GET values.
        Loads default data for initial from display on object creation.
        
        returns bool, html
        """
        data = self.GetFormValues(self.request, method="GET")
        return True, self.Render(data)


    def StartRequestPOST(self, action, **kw):
        """
        Default action. Initially loads data from request POST values.
        Loads default data for initial from display on object creation.

        returns bool, html
        """
        data = self.GetFormValues(self.request, method="POST")
        return True, self.Render(data)


    def ReturnDataOnSuccess(self, action, **kw):
        """
        Process request data and returns validated data as `result` and rendered
        form as `data`. If validation fails `result` is False. `redirectSuccess`
        is ignored.
        
        A custom success message can be passed as success_message as keyword.

        returns bool, html
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            if kw.get("success_message"):
                msgs.append(kw.get("success_message"))
            # disabled default message. msgs.append(_(u"OK."))
            errors = None
            result = data
            self.Signal("success", data=data)
        return result, self.Render(data, msgs=msgs, errors=errors)


    def ProcessForm(self, action, **kw):
        """
        Process request data and returns validated data as `result` and rendered
        form as `data`. If validation fails `result` is False. `redirectSuccess`
        is ignored.
        
        A custom success message can be passed as success_message as keyword.

        returns bool, html
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            if kw.get("success_message"):
                msgs.append(kw.get("success_message"))
            # disabled default message. msgs.append(_(u"OK."))
            errors = None
            result = data
            self.Signal("success", data=data)
        return self._FinishFormProcessing(result, data, msgs, errors, **kw)
    
    def Cancel(self, action, **kw):
        """
        Cancel form action
        
        Event
        - cancel() before validate is called

        Used options:
        - redirectCancel

        returns bool, string
        """
        self.Signal("success")
        if self.view and self.redirectCancel:
            redirectCancel = self.view.ResolveUrl(url=self.redirectCancel)
            return self.view.Redirect(redirectCancel, raiseException=True, refresh=True)
        return True, ""


    # Data extraction and validation --------------------------------------------------------------------------------------------

    def Validate(self, data, removeNull=True):
        """
        Extracts fields from request or source data dictionary, converts and
        validates. 
        
        Event
        - validate(data) before validate is called
        - process(data)  after validate has succeeded, is not called if validate failed
        
        returns bool, dict, list (result,data,errors)
        """
        if not isinstance(data, dict):
            data = self.GetFormValues(data)
        result,data,errors = Form.Validate(self, data, removeNull)
        return result,data,errors

    
    def Extract(self, data, removeNull=False, removeEmpty=False):
        """
        Extracts fields from request or source data dictionary and converts
        data types without validation and error checking. 
        
        returns bool, dict (result, data)
        """
        if not isinstance(data, dict):
            data = self.GetFormValues(data)
        self._SetUpSchema()
        result, data = Form.Extract(self, data, removeNull, removeEmpty)
        return result, data


    # Form view functions --------------------------------------------------------------------------------------------

    def Render(self, data, msgs=None, errors=None, messagesOnly=False, result=None):
        """
        renders the form with data, messages
        
        messagesOnly=True will skip form and error rendering on just render the messages as 
        html block.

        Event
        - render(data) before the form is rendered
        """
        if messagesOnly:
            return self._Msgs(msgs=msgs, result=result)

        self._SetUpSchema()
        if errors:
            html = self._Msgs(msgs=msgs, result=result)
            return html + errors.render()
            #return html + exception.ValidationFailure(self._form, data, errors).render()

        self.Signal("render", data=data)
        html = self.render(data, msgs=msgs, result=result)
        return html


    def RenderBody(self, data, msgs=None, errors=None, result=None):
        """
        renders the form without header and footer
        """
        self._SetUpSchema()
        html = self._Msgs(msgs=msgs, result=result)
        if errors:
            return html + errors.render()
        self.widget.template = "form_body"
        html += self.render(data)
        self.widget.template = "form"
        return html

    
    def HTMLHead(self, ignore=(u"jquery.js",u"jquery-ui.js")):
        """
        Get necessary includes (js and css) for html header.
        Jquery and Jquery-ui are included by default in cmsview editor pages. So by default these two
        will be ignored. 
        """
        self._SetUpSchema()
        resources = self.get_widget_resources()
        js_resources = resources.get('js')
        css_resources = resources.get('css')
        resources = resources.get('seq')
                
        # js and css
        req = self.request
        js_links = []
        css_links = []
        # use view.StaticUrl if self.view is set
        if self.view:
            if js_resources:
                js_links = [self.view.StaticUrl(r) for r in filter(lambda v: v not in ignore, js_resources)]
            if css_resources:
                css_links = [self.view.StaticUrl(r) for r in filter(lambda v: v not in ignore, css_resources)]
            # seq
            if resources:
                js_links.extend([self.view.StaticUrl(r[1]) for r in filter(lambda v: v[0] not in ignore and v[1].endswith(u".js"), resources)])
                css_links.extend([self.view.StaticUrl(r[1]) for r in filter(lambda v: v[0] not in ignore and v[1].endswith(u".css"), resources)])
        else:
            if js_resources:
                js_links = [static_url(r, req) for r in filter(lambda v: v not in ignore, js_resources)]
            if css_resources:
                css_links = [static_url(r, req) for r in filter(lambda v: v not in ignore, css_resources)]
            # seq
            if resources:
                js_links.extend([static_url(r[1], req) for r in filter(lambda v: v[0] not in ignore and v[1].endswith(u".js"), resources)])
                css_links.extend([static_url(r[1], req) for r in filter(lambda v: v[0] not in ignore and v[1].endswith(u".css"), resources)])
        js_tags = [u'<script src="%s" type="text/javascript"></script>' % link for link in js_links]
        css_tags = [u'<link href="%s" rel="stylesheet" type="text/css" media="all">' % link for link in css_links]
        return (u"\r\n").join(css_tags + js_tags)
    
        
    def _FinishFormProcessing(self, result, data, msgs, errors, **kw):
        """
        Handles the default form processing after the action has been executed
        based on passed keywords and result:
        
        Used kw arguments:
        - redirectSuccess

        """
        if not result:
            if self.use_ajax:
                # return only the rendered form back to the user. stops the request
                # processing at this point
                return self.view.SendResponse(data=self.Render(data, msgs=msgs, errors=errors), headers=[("X-Result", "false")])
            return result, self.Render(data, msgs=msgs, errors=errors)
    
        redirectSuccess = self.view.ResolveUrl(url=self.redirectSuccess)
        if redirectSuccess:
            # raises HTTPFound
            return result, self.view.Redirect(redirectSuccess, messages=msgs, raiseException=True, refresh=True)

        if self.successResponseBody is not None:
            if callable(self.successResponseBody):
                body = self.successResponseBody(self)
            else:
                body = self.successResponseBody
            return self.view.SendResponse(data=body, headers=[("X-Result", "true")])

        self.Signal("messages", messages=msgs, result=result)
        if not self.renderSuccess:
            html = self._Msgs(msgs=msgs,result=result)
        else:
            html = self.Render(data, msgs=msgs, errors=errors, result=result)
        if self.use_ajax:
            # return only the rendered form back to the user. stops the request
            # processing at this point
            return self.view.SendResponse(data=html, headers=[("X-Result", "true")])
        return result, html

    def _Msgs(self, **values):
        err = values.get("errors")!=None or values.get("result")==False
        msgs = values.get("msgs")
        if not msgs:
            return u""
        h = []
        if isinstance(msgs, basestring):
            msgs = [msgs]
        for m in msgs:
            h.append(u"""<p>%s</p>""" % (translate(m, self.view.request)))
        css = u"alert alert-success"
        if err:
            css = u"alert alert-warning"
        return u"""<div class="%s">%s</div>
        """ % (css, u"".join(h))




# Preconfigured forms -----------------------------------------------------------------

class ObjectForm(HTMLForm):
    """
    Contains actions for object creation and updates.
    
    Supports sort form parameter *pepos*.
    """
    actions = [
        Conf(id=u"default",    method="StartFormRequest",  name=u"Initialize", hidden=True,  css_class=u"",            html=u"", tag=u""),
        Conf(id=u"create",     method="CreateObj",  name=u"Create",     hidden=False, css_class=u"btn btn-primary",  html=u"", tag=u""),
        Conf(id=u"defaultEdit",method="StartObject",name=u"Initialize", hidden=True,  css_class=u"",            html=u"", tag=u""),
        Conf(id=u"edit",       method="UpdateObj",  name=u"Save",       hidden=False, css_class=u"btn btn-primary",  html=u"", tag=u""),
        Conf(id=u"cancel",     method="Cancel",     name=u"Cancel",     hidden=False, css_class=u"buttonCancel",html=u"", tag=u"")
    ]
    subsets = {
        "create": {"actions": [u"create"],  "defaultAction": "default"},
        "edit":   {"actions": [u"edit"],    "defaultAction": "defaultEdit"}
    }


    def Setup(self, subset=None, addTypeField=False): #, addPosField=True
        """
        Calls Form.Setup() with the addition to automatically add the pool_type field. 
        
        1) Load fields from object definition
        2) Loads subsets and actions from object form definition
        
        Event
        - setup() after fields have been loaded
        """
        Form.Setup(self, subset)
        if not addTypeField:
            return
        #add type field 
        #opt
        pos = 0
        for field in self._c_fields:
            if field.id == "pool_type":
                if field.readonly:
                    # replace readonly field
                    type_fld = FieldConf(id="pool_type",datatype="string",hidden=1)
                    del self._c_fields[pos]
                    self._c_fields.append(type_fld)
                return
            pos += 1
        type_fld = FieldConf(id="pool_type",datatype="string",hidden=1)
        self._c_fields.append(type_fld)
        # insert at position
        if ISort.providedBy(self.context):
            #if addPosField:
            pepos = self.GetFormValue(u"pepos", method=u"ALL")
            if pepos:
                pos_fld = FieldConf(id="pepos",datatype="string",hidden=1)
                self._c_fields.append(pos_fld)


    def StartForm(self, action, **kw):
        """
        Default action. Use this function to initially render a form if:
        - startEmpty is True
        - defaultData is passed in kw
        - load form default data

        Event
        - loadDefault(data) after data has been looked up

        returns bool, html
        """
        if self.startEmpty:
            data = {}
        elif "defaultData" in kw:
            data = kw["defaultData"]
            self.Signal("loadDefault", data=data)
        else:
            data = self.LoadDefaultData()
        if isinstance(self.loadFromType, basestring):
            data["pool_type"] = self.loadFromType
        else:
            data["pool_type"] = self.loadFromType.id
        # insert at position
        if ISort.providedBy(self.context):
            pepos = self.GetFormValue(u"pepos", method=u"ALL")
            if pepos:
                data["pepos"] = pepos
        return True, self.Render(data)


    def StartFormRequest(self, action, **kw):
        """
        Default action. Called if no action in request or self.actions.default set.
        Loads default data from request for initial from display on object creation.
        
        You can also pass additional default values for form fields as dictionary as
        `kw['defaults']`.

        returns bool, html
        """
        if self.startEmpty:
            data = {}
        elif self.defaults is not None:
            data = self.defaults
            if callable(data):
                data = data(self)
        else:
            data = self.LoadDefaultData()
            r, d = self.ExtractSchema(self.GetFormValues(method=u"ALL"), removeNull=True, removeEmpty=True)
            data.update(d)
        if isinstance(self.loadFromType, basestring):
            data["pool_type"] = self.loadFromType
        else:
            data["pool_type"] = self.loadFromType.id
        # insert at position
        if ISort.providedBy(self.context):
            pepos = self.GetFormValue(u"pepos", method=u"ALL")
            if pepos:
                data["pepos"] = pepos
        return True, self.Render(data)


    def StartObject(self, action, **kw):
        """
        Initially load data from object. 
        context = obj
        
        returns bool, html
        """
        data = self.LoadObjData(kw.get("obj"))
        return data is not None, self.Render(data)


    def UpdateObj(self, action, **kw):
        """
        Process request data and update object.
        
        You can also pass additional values not used as form fields to be stored
        when the object is updated. Pass a dictionary as `kw['values']`.

        `Process()` returns the form data as result if update succeeds.

        Event
        - success(obj) after data has been successfully committed

        returns form data or false, html or redirects
        """
        msgs = []
        obj=self.context
        result,data,errors = self.Validate(self.request)
        if result:
            user = kw.get("user") or self.view.User()
            values = kw.get("values")
            if values is not None:
                data.update(values)
            result = obj.Update(data, user)
            if result:
                #obj.Commit(user)
                msgs.append(_(u"OK. Data saved."))
                self.Signal("success", obj=obj)
                result = obj

        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


    def CreateObj(self, action, **kw):
        """
        Process request data and create object as child for current context.
        
        Pass `kw['pool_type']` to specify type to be created. If not passed pool_type
        will be extracted from data dictionary.

        You can also pass additional values not used as form fields to be stored
        when the object is created. Pass a dictionary as `kw['values']`.

        `Process()` returns the new object as result if create succeeds.

        Event
        - success(obj) after data has been successfully committed

        returns new object or none, html or redirects
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            if "pool_type" in kw:
                objtype = kw["pool_type"]
            else:
                objtype = data.get("pool_type")

            values = kw.get("values")
            if values is not None:
                data.update(values)
                
            user=kw.get("user") or self.view.User()
            result = self.context.Create(objtype, data, user)
            if result:
                if ISort.providedBy(self.context):
                    # insert at position
                    pepos = self.GetFormValue(u"pepos")
                    if pepos:
                        self.context.InsertAtPosition(result, pepos, user=user)
                msgs.append(_(u"OK. Data saved."))
                self.Signal("success", obj=result)

        return self._FinishFormProcessing(result, data, msgs, errors, **kw)


class ToolForm(HTMLForm):
    """
    Contains default actions for tool form processing.

    Example ::

        tool = app.GetTool("tool id", contextObject=app)
        form = ToolForm(view=self, context=tool, loadFromType=tool.configuration)
        form.Setup()
        result, data, action = form.Process()

    A simple example to render a tool form and execute it.
    """
    actions = [
        Conf(id=u"default", method="StartForm", name=u"Initialize", hidden=True,  css_class=u"", html=u"", tag=u""),
        Conf(id=u"run",     method="RunTool",   name=u"Start",      hidden=False, css_class=u"", html=u"", tag=u""),
    ]

    def Setup(self, subset=None):
        """
        1) Load fields from tool definition
        2) Loads subsets and actions from tool form definition
        
        Event
        - setup() after fields have been loaded
        """
        self._c_form = None
        self._c_fields = None
        self._c_actions = None
        self.subset=subset

        subsets=self.subsets
        config = None

        # load form fields
        if self.loadFromType:
            typeOrConfiguration = self.loadFromType
            if isinstance(typeOrConfiguration, basestring):
                config = self.app.GetToolConf(typeOrConfiguration)
                if not config:
                    raise ConfigurationError, "Tool not found (%s). Use configuration instance instead of a string." % (str(typeOrConfiguration))
            else:
                config = typeOrConfiguration
            self.loadFromType = config
        
        # unconfigured form
        if not subset and not subsets and not config and not self.fields:
            raise ConfigurationError, "No form fields defined."
        # unknown subset
        if subset and (not subsets or not subset in subsets):
            raise ConfigurationError, "Unknown subset."

        # field lookup
        #(1) subsets[subset]["fields"]
        #(3) tool["form"][subset]["fields"]
        #(5) fields
        #(6) config.fields
        temp = None
        if subsets and subset in subsets and "fields" in subsets[subset]:
            #(1)
            temp = subsets[subset]["fields"]
        elif config and "forms" in config and config.forms and subset in config.forms and "fields" in config.forms[subset]:
            #(3)
            temp = config.forms[subset]["fields"]
        elif self.fields:
            temp = self.fields
        elif config and self.app:
            temp = config.data
        #if not temp:
        #    raise ConfigurationError, "No form fields defined."
        # lookup field configurations
        self._c_fields = []
        for f in temp:
            if isinstance(f, basestring):
                fld = None
                if self.fields:
                    for a in config.data:
                        if a.id == f:
                            fld = a
                            break
                elif config:
                    for a in config.data:
                        if a.id == f:
                            fld = a
                            break
                if not fld:
                    raise ConfigurationError, "Form field lookup failed: " + f
                f = fld
            self._c_fields.append(f)
        
        # action lookup
        #(1) subsets[subset]["actions"]
        #(2) tool["form"][subset]["actions"]
        #(3) actions 
        temp = None
        if subsets and subset in subsets:
            if isinstance(subsets[subset], dict) and "actions" in subsets[subset]:
                #(1)
                temp = subsets[subset]["actions"]
        elif config and "forms" in config and config.forms and subset in config.forms:
            if isinstance(config.forms[subset], dict) and "actions" in config.forms[subset]:
                #(3)
                temp = config.forms[subset]["actions"]
        elif self.actions:
            temp = self.actions
        if temp:
            # lookup action configurations
            self._c_actions = []
            for a in temp:
                if isinstance(a, basestring):
                    action = None
                    if self.actions:
                        for v in self.actions:
                            if v.id == a:
                                action = v
                                break
                    if not action:
                        raise ConfigurationError, "Form action lookup failed: " + a
                    a = action
                self._c_actions.append(a)
                
        self.Signal("setup")
        
            
    def RunTool(self, action, **kw):
        """
        Process request data and run tool. 

        returns bool, html
        """
        msgs = []
        validated,data,errors = self.Validate(self.request)
        if validated:
            return self.context.Run(request=self.request,**data)
        return False, self.Render(data, msgs=msgs, errors=errors)




class WorkflowForm(HTMLForm):
    """
    Contains default actions for workflow transition form processing
    Requires Form, HTMLForm or TemplateForm
    """

    def CallWf(self, action, **kw):
        """
        process request data and call workflow transition for object. 
        context = obj
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            wfa = ""
            wft = ""
            user = kw.get("user") or self.view.User()
            if not self.context.WfAction(action=wfa, transition=wft, user = user):
                result = False

        return self._FinishFormProcessing(result, data, msgs, errors, **kw)
        


class JsonMappingForm(HTMLForm):
    """
    Maps form fields to a single dumped json text field
    json data is always stored as dictionary. ::
    
        jsonDataField = the field to merge data to
        mergeContext = if true the database values will be updated
                       by form values
                       
    `Process()` returns the form data as dictionary on success.
    
    """
    jsonDataField = "data"
    mergeContext = True

    actions = [
        Conf(id=u"default",    method="StartObject",name=u"Initialize", hidden=True,  css_class=u"",                 html=u"", tag=u""),
        Conf(id=u"edit",       method="UpdateObj",  name=u"Save",       hidden=False, css_class=u"btn btn-primary",  html=u"", tag=u""),
    ]

    def Validate(self, data, removeNull=True):
        """
        Extracts fields from request or source data dictionary, converts and
        validates. 
        
        Event
        - validate(data) before validate is called
        - process(data)  after validate has succeeded, is not called if validate failed
        
        returns bool, dict, list (result,data,errors)
        """
        if not isinstance(data, dict):
            data = self.GetFormValues(data)
        result,data,errors = Form.Validate(self, data, removeNull)
        if not result:
            return result,data,errors
        # merge existing data
        if self.mergeContext and self.context:
            jdata = self.context.data[self.jsonDataField] or {}
            jdata.update(data)
            data = jdata
        return result,data,errors

    
    def Extract(self, data, removeNull=False, removeEmpty=False):
        """
        Extracts fields from request or source data dictionary and converts
        data types without validation and error checking. 
        
        returns bool, dict (result, data)
        """
        if not isinstance(data, dict):
            data = self.GetFormValues(data)
        self._SetUpSchema()
        result, data = Form.Extract(self, data, removeNull, removeEmpty)
        # merge existing data
        if self.mergeContext and self.context:
            jdata = self.context.data[self.jsonDataField]
            jdata.update(data)
            data = jdata
        return result,data


    def StartObject(self, action, **kw):
        """
        Initially load data from configured object json data field. 
        context = obj
        
        returns bool, html
        """
        data = self.context.data.get(self.jsonDataField) or {}
        return data!=None, self.Render(data)


    def UpdateObj(self, action, **kw):
        """
        Process request data and update object.
        
        Event
        - success(data) after data has been successfully committed

        returns bool, html
        """
        msgs = []
        obj=self.context
        result,data,errors = self.Validate(self.request)
        if result:
            user = kw.get("user") or self.view.User()
            result = obj.Update({self.jsonDataField: data}, user)
            if result:
                #obj.Commit(user)
                msgs.append(_(u"OK. Data saved."))
                result = data
                self.Signal("success", data=data)

        return self._FinishFormProcessing(result, data, msgs, errors, **kw)
        
        

class JsonSequenceForm(HTMLForm):
    """
    Maps form fields as sequence to a single dumped json text field
    the sequence is always stored as list, json data as dictionary. 
    
    The form fields/values can be stored multiple times as sequence and
    the template offers options to add, delete and edit single items.
    Items in read only mode are not rendered by the form. 
    
    Sequence items are referenced by list position starting by 1.
    ::
    
        jsonDataField = the field to merge data to
                       
    `Process()` returns the form data as dictionary on success.
    
    """
    jsonDataField = u"data"
    jsonUniqueID = u"name"
    delKey = u"aa876352"
    editKey = u"cc397785"
    
    actions = [
        Conf(id=u"default",    method="StartObject",name=u"Initialize", hidden=True,  css_class=u"",                 html=u"", tag=u""),
        Conf(id=u"edit",       method="UpdateObj",  name=u"Save",       hidden=False, css_class=u"btn btn-primary",  html=u"", tag=u""),
    ]
    editKeyFld = FieldConf(id=editKey, name=u"indexKey", datatype="number", hidden=True, default=u"")
    
    def Init(self):
        self.ListenEvent("setup", "AddKeyFld")
        
    def AddKeyFld(self):
        self._c_fields.append(self.editKeyFld)


    def StartObject(self, action, **kw):
        """
        Initially load data from configured object json data field. 
        context = obj
        
        Event
        - delete(data) after data has been deleted

        returns bool, html
        """
        sequence = self.context.data.get(self.jsonDataField)
        if sequence in (u"", None):
            sequence = []
        # process action
        msgs = []
        if self.GetFormValue(self.editKey, self.request, "GET"):
            seqindex = int(self.GetFormValue(self.editKey, self.request, "GET"))
            if not seqindex or seqindex > len(sequence):
                data = []
            else:
                data = sequence[seqindex-1]
                data[self.editKey] = seqindex
        elif self.GetFormValue(self.delKey, self.request, "GET"):
            seqindex = int(self.GetFormValue(self.delKey, self.request, "GET"))
            if not seqindex or seqindex > len(sequence):
                data = []
            else:
                del sequence[seqindex-1]
                self.context.data[self.jsonDataField] = sequence
                self.context.Commit(kw.get("user") or self.view.User())
                self.context.data[self.jsonDataField] = sequence
                msgs=[_(u"Item deleted!")]
                data = []
                self.Signal("delete", data=sequence)
        else:
            data = []
        return data!=None, self.Render(data, msgs=msgs)


    def UpdateObj(self, action, **kw):
        """
        Process request data and update object.
        
        Event
        - success(data) after data has been successfully committed

        returns bool, html
        """
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            user = kw.get("user") or self.view.User()
            # merge sequence list with edited item
            sequence = self.context.data.get(self.jsonDataField)
            if sequence in (u"", None):
                sequence = []
            elif isinstance(sequence, tuple):
                sequence = list(sequence)
            try:
                seqindex = int(data.get(self.editKey))
            except:
                seqindex = 0
            if seqindex == 0 and data[self.jsonUniqueID] in [i[self.jsonUniqueID] for i in sequence]:
                # item already in list and not edit clicked before
                msgs=[_(u"Item exists!")]
                return False, self.Render(data, msgs=msgs, errors=errors)
                
            if self.editKey in data:
                del data[self.editKey]
            if not seqindex or seqindex > len(sequence):
                append = 1
                # replace existing key
                if self.jsonUniqueID:
                    for item in sequence:
                        if item[self.jsonUniqueID] == data[self.jsonUniqueID]:
                            item.update(data)
                            append=0
                            break
                if append:
                    sequence.append(data)
            else:
                sequence[seqindex-1] = data
            self.context.data[self.jsonDataField] = sequence
            self.context.Commit(user)
            self.context.data[self.jsonDataField] = sequence
            msgs.append(_(u"OK. Data saved."))
            self.Signal("success", data=sequence)
            data = {}

        return result, self.Render(data, msgs=msgs, errors=errors)
        
        
def MakeCustomizedViewForm(view, forContext, formSettingsOrSubset, typeconf=None, formClass=None,
                           actions=None, defaultAction=None, defaultSettings=None, loadFromViewModuleConf=None):
    """
    Sets up from instances by looking up form sonfiguration settings in the various customization slots.

    1) typeconf.form defintion (if formSettingsOrSubset is a string)
    2) loadFromViewModuleConf.form
    3) actions and defaultAction
    4) defaultSettings
    5) formSettingsOrSubset (if it is a dict or configuration)

    :param view: view class instance.
    :param forContext: the context the view/for is rendered for
    :param formSettingsOrSubset: form setup configuration or a subset name as string. If a string the subset is loaded
                                 from `typeconf.form.subset`.
    :param typeconf: type configuration to load form fields referenced as string
    :param formClass: on instantiated form class. defaults to `nive.forms.ObjectForm`
    :param actions: list of possible actions to be used with the form. This has to be a list of action definitions.
    :param defaultAction: the initial default action to be triggered if processed for the first time. Either a action
                          definition or a string.
    :param defaultSettings: a dict with default for the form. Can be oerriden by formSettings.
    :param loadFromViewModuleConf: pass the view module configuration to load default form settings from
                                   `ViewModuleConf.form`.
    :return: instantiated form class, subset name if used or None
    """
    # form rendering settings
    formClass = formClass or ObjectForm
    form = formClass(view=view, context=forContext, loadFromType=typeconf)

    # load view module configuration form settings
    if loadFromViewModuleConf is not None:
        formsettings = loadFromViewModuleConf.get("form")
        if isinstance(formsettings, dict):
            form.ApplyOptions(formsettings)

    # set default actions
    if actions is not None:
        form.actions = actions
    if defaultAction is not None:
        form.defaultAction = defaultAction

    # apply defaults
    if defaultSettings is not None:
        form.ApplyOptions(defaultSettings)

    # load form settings
    if isinstance(formSettingsOrSubset, basestring):
        form.subset = formSettingsOrSubset
        form.subsets = typeconf.forms
        subset = formSettingsOrSubset
    else:
        # load the form without subset. add fields and action directly.
        form.ApplyOptions(formSettingsOrSubset)
        subset = None

    return form, subset


class ValidationError(Exception):
    """
    Used for validation failures
    """

