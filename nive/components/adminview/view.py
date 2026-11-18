# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Administration interface module
"""


from nive.i18n import _
from nive.definitions import ViewConf, ViewModuleConf, FieldConf, Conf
from nive.definitions import IApplication, IPortal, IModuleConf
from nive.definitions import IViewModuleConf

from nive.extensions.persistentRoot import IPersistentRoot
from nive.utils.utils import ConvertDictToStr

from nive.components.reform.forms import HTMLForm
from nive.components.iface.view import IFaceView

from .iface import configuration as ifaceConf


# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf("nive.components.iface.view.configuration",
    id = "admin",
    name = _("System"),
    context = IApplication,
    containment = IPortal,
    view = "nive.components.adminview.view.AdminView",
    templates = "nive.components.adminview:templates/",
    permission = "administration",
    adminLink = "app_folder_url/system",
    static = (
        {"path":"nive.components.iface:static/","name":"s-iface"},
        {"path":"nive.components.adminview:static/","name":"s-admin"}
    ),
    ifaceConf = ifaceConf,
    template = "nive.components.iface:templates/index.pt",
    assetsCustom = [ ],
    utilities=Conf()
)

configuration.views = [
    # User Management Views
    ViewConf(name = "system",       attr = "basics", renderer = configuration.templates+"form.pt"),
    ViewConf(name = "sys-tools",    attr = "tools",  renderer = configuration.templates+"tools.pt"),
    ViewConf(name = "sys-modules",  attr = "modules",renderer = configuration.templates+"modules.pt"),
    ViewConf(name = "sys-views",    attr = "views",  renderer = configuration.templates+"views.pt"),

    # ViewConf(name = "database",     attr = "editdatabase", renderer=t+"form.pt"),
    # ViewConf(name = "sys-rootsettings",attr = "editroot",    renderer = t+"form.pt"),
    # ViewConf(name = "portal",   attr = "editportal", renderer = t+"form.pt"),
]


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






class AdminView(IFaceView):
    viewModuleID = "admin"

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


    def adminoptions(self, context=None):
        """
        Renders Admin Links if iface.headoptions is empty

        :param self:
        :param context:
        :return:
        """
        if context is not None:
            apps = (context,)
        else:
            apps = self.context.app.portal.GetApps()
        html = []
        for app in apps:
            if not hasattr(app, "registry"):
                continue

            # search all view modules for admin links
            for vm in app.configurationQuery.QueryConf(IViewModuleConf):
                if not vm.get("adminLink"):
                    continue
                if not self.Allowed(vm.permission, app):
                    continue
                link = Conf(id=self.ResolveUrl(vm.get("adminLink"), app), name=app.configuration.title + ": " + vm.name)
                html.append(self.head_link(link, cls="dropdown-item"))
        return "".join(html)
    headoptions = adminoptions # map dropdown links


    def basics(self):
        self.request.currentSection = "system"
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
        self.request.currentSection = "sys-root"
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
        self.request.currentSection = "sys-db"
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
        self.request.currentSection = "sys-portal"
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
        self.request.currentSection = "sys-tools"
        app = self.context.app
        data = ""
        
        selected = self.GetFormValue("tag")
        if selected:
            tool = app.GetTool(selected, contextObject=app)
            data = self.RenderView(tool)
            # pyramid bug? reset the active view in request
            self.request.__dict__['__view__'] = self
            return {"content": data, "tools": [], "tool":tool}

        t = app.configurationQuery.GetAllToolConfs(contextObject=app)
        return {"content": data, "tools": t, "tool":None}
    
    
    def modules(self):
        self.request.currentSection = "sys-modules"
        return {}

    def views(self):
        self.request.currentSection = "sys-views"
        return {}

    def doc(self):
        self.request.currentSection = "sys-doc"
        return {}

    
