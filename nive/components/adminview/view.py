# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Administration interface module
"""

from pyramid.renderers import get_renderer, render_to_response, render
from zope.interface import Interface

from nive.i18n import _
from nive.definitions import ViewConf, ViewModuleConf, FieldConf, WidgetConf, Conf
from nive.definitions import IApplication, IUser, IUserDatabase, IPersistent, IModuleConf, IViewModuleConf

from nive.views import BaseView
from nive.extensions.persistentRoot import IPersistentRoot
from nive.utils.utils import SortConfigurationList, ConvertDictToStr

from nive.components.reform.forms import ValidationError, HTMLForm



class IAdminWidgetConf(Interface):
    """
    IAdminWidgetConf refers to the nive.components.adminview tab plugin point. Use IAdminWidgetConf as widgetType
    in your WidgetConf() to link a new tab to the nive admin header.
    """



# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf(
    id = "administration",
    name = _("System"),
    context = IApplication,
    view = "nive.components.adminview.view.AdminView",
    templates = "nive.components.adminview:",
    template = "index.pt",
    permission = "administration",
    adminLink = "app_folder_url/system",
    static = "nive.components.adminview:static",
    assets = [
        ('bootstrap.min.css', 'nive.components.adminview:static/mods/bootstrap-4.3.1-dist/css/bootstrap.css'),
        ('adminview.css', 'nive.components.adminview:static/adminview.css'),   # nive css
        ('jquery.js', 'nive.components.adminview:static/mods/jquery-3.3.1.slim.min.js'),
        ('bootstrap.min.js', 'nive.components.adminview:static/mods/bootstrap-4.3.1-dist/js/bootstrap.bundle.js'),
    ],
)
t = configuration.templates
configuration.views = [
    # User Management Views
    ViewConf(name = "system",       attr = "editbasics", renderer = t+"form.pt"),
    ViewConf(name = "sys-tools",    attr = "tools",      renderer = t+"tools.pt"),
    ViewConf(name = "sys-modules",  attr = "view",       renderer = t+"modules.pt"),
    ViewConf(name = "sys-views",    attr = "view",       renderer = t+"views.pt"),
    # ViewConf(name = "sys-rootsettings",attr = "editroot",    renderer = t+"form.pt"),
    # ViewConf(name = "portal",   attr = "editportal", renderer = t+"form.pt"),
]

configuration.widgets = [
    WidgetConf(name=_("Basics"),    viewmapper="system",         id="admin.system",       sort=1000,   apply=(IApplication,), widgetType=IAdminWidgetConf),
    WidgetConf(name=_("Tools"),     viewmapper="sys-tools",      id="admin.sys-tools",    sort=5000,   apply=(IApplication,), widgetType=IAdminWidgetConf),
    WidgetConf(name=_("Modules"),   viewmapper="sys-modules",    id="admin.sys-modules",  sort=10000,  apply=(IApplication,), widgetType=IAdminWidgetConf,
               description=_("Read only listing of all registered modules and settings.")),
    WidgetConf(name=_("Views"),     viewmapper="sys-views",      id="admin.sys-views",    sort=15000,  apply=(IApplication,), widgetType=IAdminWidgetConf,
               description=_("Read only listing of all registered views grouped by view modules.")),
    # WidgetConf(name=_("Root"),      viewmapper="sys-rootsettings",id="admin.sys-rootsettings",sort=1100,   apply=(IApplication,), widgetType=IAdminWidgetConf),
    # WidgetConf(name=_("Global"),    viewmapper="sys-portal",     id="admin.sys-portal",   sort=300,    apply=(IApplication,), widgetType=IAdminWidgetConf),
]


"""
dbAdminConfiguration
--------------------
managing database settings through the web interface makes sense if the values are
stored outside the database.
"""
#@nive_module
dbAdminConfiguration = ViewModuleConf(
    id = "databaseAdministration",
    name = _("Database Administration"),
    static = "",
    context = IApplication,
    view = "nive.components.adminview.view.AdminView",
    templates = "nive.components.adminview:",
    permission = "administration",
    views = [
        # Database Management Views
        ViewConf(name = "database", attr = "editdatabase",   renderer = "nive.components.adminview:form.pt"),
    ],
    widgets = [
        WidgetConf(name=_("Database"),  viewmapper="database",   id="admin.database", sort=200,   apply=(IApplication,), widgetType=IAdminWidgetConf),
    ]
)

        
    
# view and form implementation ------------------------------------------------------------------


class ConfigurationForm(HTMLForm):
    
    actions = [
        Conf(id="default",    method="Start",   name="Initialize", hidden=True,  css_class="",                 html="", tag=""),
        Conf(id="edit",       method="Update",  name=_("Save"),    hidden=False, css_class="btn btn-primary",  html="", tag=""),
    ]
    
    def Start(self, action, **kw):
        """
        Initially load data from object. 
        context = obj
        
        returns bool, html
        """
        conf = self.context
        data = {}
        for f in self.GetFields():
            # data
            if f.id in conf:
                if f.datatype=="password":
                    continue
                data[f.id] = conf.get(f.id,"")
        return data!=None, self.Render(data)


    def Update(self, action, **kw):
        """
        Process request data and update object.
        
        returns bool, html
        """
        redirectSuccess = kw.get("redirectSuccess")
        msgs = []
        conf=self.context
        result,data,errors = self.Validate(self.request)
        if result:
            # lookup persistent manager for configuration
            storage = self.app.NewModule(IModuleConf, "persistence")
            if storage:
                storage(app=self.app, configuration=conf).Save(data)
                msgs.append(_("OK. Data saved."))
            else:
                msgs.append(_("No persistent storage for configurations activated. Nothing saved."))
                result = False
            errors=None
            if self.view and redirectSuccess:
                redirectSuccess = self.view.ResolveUrl(redirectSuccess, self.context)
                if self.use_ajax:
                    self.view.Relocate(redirectSuccess, messages=msgs, raiseException=True)
                else:
                    self.view.Redirect(redirectSuccess, messages=msgs, raiseException=True)
        return result, self.Render(data, msgs=msgs, errors=errors)    


from nive.components.reform.schema import Invalid

def RootnameValidator(node, value):
    """
    Makes sure the new name does not exist.
    """
    # lookup name in database
    app = node.widget.form.context.app
    for root in app.configurationQuery.GetAllRootConfs():
        if root.id == value:
            # check if its the context
            if app.GetRoot(root.id)!=node.widget.form.context:
                err = _("'${name}' already in use. Please choose a different name.", mapping={'name':value})
                raise Invalid(node, err)

class RootForm(HTMLForm):

    actions = [
        Conf(id="default",    method="Start",   name="Initialize", hidden=True,  css_class="",            html="", tag=""),
        Conf(id="edit",       method="Update",  name="Save",       hidden=False, css_class="btn btn-primary",  html="", tag=""),
    ]

    def Start(self, action, **kw):
        """
        Initially load data from root object.
        context = root

        returns bool, html
        """
        root = self.context
        data = {}
        for f in self.GetFields():
            # data
            if f.datatype=="password":
                continue

            if f.id in root.data:
                data[f.id] = root.data.get(f.id,"")
            elif f.id in root.meta:
                data[f.id] = root.meta.get(f.id,"")

        return data!=None, self.Render(data)


    def Update(self, action, **kw):
        """
        Process request data and update object.

        returns bool, html
        """
        redirectSuccess = kw.get("redirectSuccess")
        msgs = []
        result,data,errors = self.Validate(self.request)
        if result:
            # lookup persistent manager for configuration
            root = self.context
            root.Update(data, user=self.view.User())
            msgs.append(_("OK. Data saved."))
            errors=None
            if self.view and redirectSuccess:
                redirectSuccess = self.view.ResolveUrl(redirectSuccess, self.context)
                if self.use_ajax:
                    self.view.Relocate(redirectSuccess, messages=msgs, raiseException=True)
                else:
                    self.view.Redirect(redirectSuccess, messages=msgs, raiseException=True)
        return result, self.Render(data, msgs=msgs, errors=errors)


class AdminBasics(BaseView):

    def __init__(self, context, request):
        super(AdminBasics, self).__init__(context, request)

    def view(self):
        return {}

    def GetAdminWidgets(self):
        app = self.context.app
        widgets = app.configurationQuery.QueryConf(IAdminWidgetConf, app)
        confs = []
        if not widgets:
            return confs
        for n,w in widgets:
            confs.append(w)
        return SortConfigurationList(confs, "sort")

    def RenderConf(self, c):
        return """<strong><a onclick="$('#%d').toggle()" style="cursor:pointer">%s</a></strong><br>%s""" % (
                abs(id(c)), 
                str(c).replace("<", "&lt;").replace(">", "&gt;"),
                self.Format(c, str(abs(id(c))))
                )
        
        
    def Format(self, conf, ref):
        """
        Format configuration for html display
        
        returns string
        """
        v=["<table id='%s' class='table table-sm' style='display:none'>"%(ref)]
        for d in list(conf.__dict__.items()):
            if d[0]=="_empty":
                continue
            if d[0]=="_parent" and not d[1]:
                continue
            value = d[1]
            if value is None:
                try:
                    value = conf.parent.get(d[0])
                except:
                    pass
            if isinstance(value, str):
                pass
            elif isinstance(value, (tuple, list)):
                a=[""]
                for i in value:
                    if hasattr(i, "ccc"):
                        a.append(self.RenderConf(i))
                    else:
                        a.append(str(i).replace("<", "&lt;").replace(">", "&gt;")+"<br>")
                value = "".join(a)
            elif isinstance(value, dict):
                if "password" in value:
                    value = value.copy()
                    value["password"] = "*****"
                value = ConvertDictToStr(value, "<br>")
            else:
                value = str(value).replace("<", "&lt;").replace(">", "&gt;")
            v.append("<tr><th>%s</th><td>%s</td></tr>\r\n" % (d[0], value))
        v.append("</table>")
        return "".join(v)


    def AdministrationLinks(self, context=None):
        if context is not None:
            apps = (context,)
        else:
            apps = self.context.app.portal.GetApps()
        links = []
        for app in apps:
            if not hasattr(app, "registry"):
                continue

            # search all view modules for admin links
            for vm in app.configurationQuery.QueryConf(IViewModuleConf):
                if not vm.get("adminLink"):
                    continue
                if not self.Allowed(vm.permission, app):
                    continue
                url = self.ResolveUrl(vm.get("adminLink"), app)
                links.append({"href":url, "title":app.configuration.title + ": " + vm.name})

        return links
                
    

class AdminView(AdminBasics):
    
    def editbasics(self):
        fields = (
            FieldConf(id="title",           datatype="string", size=255,  required=0, name=_("Application title")),
            FieldConf(id="description",     datatype="text",   size=5000, required=0, name=_("Application description")),
            FieldConf(id="workflowEnabled", datatype="bool",   size=2,    required=0, name=_("Enable workflow engine")),
            FieldConf(id="fulltextIndex",   datatype="bool",   size=2,    required=0, name=_("Enable fulltext index")),
            FieldConf(id="frontendCodepage",datatype="string", size=10,   required=1, name=_("Codepage used in html frontend")),
        )
        form = ConfigurationForm(view=self, context=self.context.configuration, app=self.context)
        form.fields = fields
        form.Setup() 
        # process and render the form.
        result, data, action = form.Process()
        return {"content": data, "result": result, "head": form.HTMLHead()}


    def editroot(self):
        root = self.context.app.GetRoot(name="")
        if not IPersistentRoot.providedBy(root):
            return {"content": _("The default root does not support persistent data storage."), "result": False, "head": ""}
        fields = (
            FieldConf(id="pool_filename",   datatype="string", size=30,   required=1, name=_("Root url name"),
                      settings={"validator": RootnameValidator}, default=root.configuration.id),
            FieldConf(id="title",           datatype="string", size=255,  required=0, name=_("Root title"), default=root.configuration.name),
            FieldConf(id="description",     datatype="text",   size=5000, required=0, name=_("Root description")),
            FieldConf(id="pool_groups",      datatype="checkbox", size=250, default="", name=_("Permission"),
                      description=_("Only displayed to users in the selected group"))
        )
        form = RootForm(view=self, context=root, app=self.context)
        form.fields = fields
        form.Setup()
        # process and render the form.
        result, data, action = form.Process()
        return {"content": data, "result": result, "head": form.HTMLHead()}


    def editdatabase(self):
        dbtypes=[{"id":"MySql","name":"MySql"},{"id":"Sqlite3","name":"Sqlite3"}]
        fields = (
            FieldConf(id="context",  datatype="list",   size=20,   required=1, name=_("Database type to be used"), listItems=dbtypes,
                      description=_("Supports 'Sqlite3' and 'MySql' by default. MySql requires python-mysqldb installed.")),
            FieldConf(id="fileRoot", datatype="string", size=500,  required=0, name=_("Relative or absolute root directory for files")),
            FieldConf(id="dbName",   datatype="string", size=500,  required=1, name=_("Database file path or name"),
                      description=_("Sqlite3=database file path, MySql=database name")),
            FieldConf(id="host",     datatype="string", size=100,  required=0, name=_("Database server host")),
            FieldConf(id="port",     datatype="number", size=8,    required=0, name=_("Database server port")),
            FieldConf(id="user",     datatype="string", size=100,  required=0, name=_("Database server user")),
            FieldConf(id="password", datatype="password", size=100,required=0, name=_("Database server password")),
        )
        form = ConfigurationForm(view=self, context=self.context.dbConfiguration, app=self.context)
        form.fields = fields
        form.Setup()
        # process and render the form.
        result, data, action = form.Process()
        return {"content": data, "result": result, "head": form.HTMLHead()}


    def editportal(self):
        fields = (
            FieldConf(id="portalDefaultUrl", datatype="string", size=200, required=1, name=_("Redirect for portal root (/) requests")),
            FieldConf(id="favicon",      datatype="string", size=200,  required=0, name=_("Favicon asset path")),
            FieldConf(id="robots",       datatype="text",   size=10000,required=0, name=_("robots.txt contents")),
            FieldConf(id="loginUrl",     datatype="string", size=200,  required=1, name=_("Login form url")),
            FieldConf(id="forbiddenUrl", datatype="string", size=200,  required=1, name=_("Redirect for unauthorized requests")),
            FieldConf(id="logoutUrl",    datatype="string", size=200,  required=1, name=_("Redirect on logout")),
            FieldConf(id="accountUrl",   datatype="string", size=200,  required=0, name=_("User account page url")),
        )
        form = ConfigurationForm(view=self, context=self.context.portal.configuration, app=self.context)
        form.fields = fields
        form.Setup() 
        # process and render the form.
        result, data, action = form.Process()
        return {"content": data, "result": result, "head": form.HTMLHead()}

    
    def tools(self):
        app = self.context.app
        head = data = ""
        
        selected = self.GetFormValue("tag")
        if selected:
            tool = app.GetTool(selected, contextObject=app)
            data = self.RenderView(tool)
            # pyramid bug? reset the active view in request
            self.request.__dict__['__view__'] = self
            return {"content": data, "tools": [], "tool":tool}

        t = app.configurationQuery.GetAllToolConfs(contextObject=app)
        return {"content": data, "tools": t, "tool":None}
    
    
    def doc(self):
        return {}

    
