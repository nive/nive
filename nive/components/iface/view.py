
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound

from nive.definitions import IObjectConf, IConf, Conf
from nive.definitions import IObject, IContainer, INonContainer, IRoot
from nive.definitions import ViewConf, ViewModuleConf

from nive.views import BaseView
from nive.components.reform.forms import ObjectForm, HTMLForm
from nive.security import Allow
from nive.helper import ResolveName
from nive.workflow import WorkflowNotAllowed

from .search import Search
from .parts import Parts
from .cutcopy import CopyView
from .definitions import AllTypeDataFlds, AllTypeMetaFlds

from nive.i18n import _, translator

# view module definition ------------------------------------------------------------------

#@nive_module
configuration = ViewModuleConf(
    id = "ifaceconf",
    name = "Pool management interface",
    containment = "nive.components.iface.definitions.IIFaceRoot",
    view = "nive.components.iface.view.IFaceView",
    static = (("s-iface","nive.components.iface:static/"),),
    templates = "nive.components.iface:templates/",
    template = "nive.components.iface:templates/index.pt",
    ifaceConf = None,
    permission = "view",
    acl = [
        (Allow, "group:editor", "iface_view"),
        (Allow, "group:editor", "iface_edit"), 
        (Allow, "group:editor", "iface_add"),
        (Allow, "group:editor", "iface_delete"),
        (Allow, "group:editor", "iface_wf"),
        (Allow, "group:editor", "iface_tools")
    ],
    assets = [
        ('bootstrap.min.css', 'nive.components.iface:static/mods/bootstrap-4.3.1-dist/css/bootstrap.css'),
        ('glyphicon.css', 'nive.components.iface:static/mods/glyphicons/css/glyphicon.css'),   # nive css
        #('adminview.css', 'nive.components.iface:static/adminview.css'),   # nive css
        ('iface.css', 'nive.components.iface:static/iface.css'),
        ('jquery.js', 'nive.components.iface:static/mods/jquery-3.3.1.min.js'),
        ('bootstrap.min.js', 'nive.components.iface:static/mods/bootstrap-4.3.1-dist/js/bootstrap.bundle.js'),
        ('iface.js', 'nive.components.iface:static/iface.js'),
    ]
)

# shortcuts
#_Object = "nive.components.iface.view.ObjectIFace"
#_Container = "nive.components.iface.view.ContainerIFace"
#_Root = "nive.components.iface.view.RootIFace"
t = configuration.templates

configuration.views = [
    # Root views --------------------------------------------------------------------------------------
    ViewConf(name="", attr="default", context=IRoot),
    ViewConf(name="base", attr="base", context=IRoot, renderer=t + "base.pt"),
    ViewConf(name="open", attr="open", context=IRoot),
    ViewConf(name="search", attr="viewsearch", context=IRoot, renderer=t + "search.pt"),
    ViewConf(name="settings", attr="settings", context=IRoot, renderer=t + "settings.pt"),
    ViewConf(name="slot", attr="slot", context=IRoot, renderer=t + "settings.pt"),

    # ViewConf(name = "options",attr = "options", context = IRoot,    renderer = t+"options.pt"),
    ViewConf(name="tool", attr="tool", context=IRoot, renderer=t + "tool.pt"),

    # Object views -----------------------------------------------------------------------------------
    # view
    ViewConf(name="", attr="default", context=IObject),
    # container object view
    # ViewConf(name = "",     attr = "view",  context = IContainer, renderer = t+"list.pt"),
    ViewConf(name="viewlist", attr="viewlist", context=IContainer, renderer=t + "list.pt"),
    ViewConf(name="open", attr="open", context=IContainer),
    # non container object view
    # ViewConf(name = "",     attr = "view",  context = INonContainer, renderer = t+"view.pt"),
    ViewConf(name="view", attr="view", context=INonContainer, renderer=t + "view.pt"),
    ViewConf(name="open", attr="open", context=INonContainer),

    # object pages
    ViewConf(name="edit", attr="edit", context=IObject, renderer=t + "edit.pt", permission="edit"),
    ViewConf(name="meta", attr="meta", context=IObject, renderer=t + "meta.pt"),
    ViewConf(name="options", attr="options", context=IObject, renderer=t + "options.pt"),
    ViewConf(name="file", attr="file", context=IObject),
    ViewConf(name="deleteo", attr="delete", context=IObject, renderer=t + "delete.pt", permission="delete"),
    ViewConf(name="@delfile", attr="delfile", context=IObject, permission="delete"),

    ViewConf(name="wf", attr="wf", context=IObject, renderer=t + "wf.pt", permission="edit"),
    ViewConf(name="wfa", attr="action", context=IObject, renderer=t + "form-workflow.pt", permission="edit"),
    ViewConf(name="wfa-i", attr="action", context=IObject, renderer=t + "form-workflow-inline.pt", permission="edit"),
    ViewConf(name="wft", attr="transition", context=IObject, permission="edit"),

    # container add, delete
    ViewConf(name="add", attr="add", context=IContainer, renderer=t + "add.pt", permission="add"),
    ViewConf(name="deletec", attr="deletelist", context=IContainer, renderer=t + "delete.pt", permission="delete"),
    ViewConf(name="duplicate", attr="duplicate", context=IObject, permission="add"),
    ViewConf(name="tool", attr="tool", context=IObject, renderer=t + "tool.pt", permission="tools"),

    # cut, copy, paste
    ViewConf(name="@cut",   attr = "cut",   context = IContainer, permission="edit"),
    ViewConf(name="@copy",  attr = "copy",  context = IContainer, permission="edit"),
    ViewConf(name="@paste", attr = "paste", context = IContainer, permission="add"),

    ViewConf(name="profile", attr="profile", context=IRoot, renderer=t + "profile.pt", permission="iface"),
]


class IFaceView(Parts, Search, CopyView, BaseView):
    """
    Basic peak interface view implementation
    Provides default functionality for data management and interface configuration.
    
    search and parts are required for html rendering. For Configuration an instance of IFace
    is loaded from context.
    
    Views:
    - default
    - open
    - Object view
    - Object edit form
    - Object duplicate
    - Object meta field list
    - Object workflow
    - Object options
    - Object tool
    - Container contents list
    - Container subitem delete
    - Container subitem add
    - Root base
    - Root settings
    
    Permissions:
    - iface_view
    - iface_edit
    - iface_delete
    - iface_add
    - iface_wf
    - iface_tools 
    """
    
    actionid = None
    
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        self.ifaceConf = self.configuration.ifaceConf
        # default static routing for iface assets
        self.static = self.ifaceConf.get("static", "")
        if ":" in self.static:
            self.static = self.StaticUrl(self.static)

    # Get conf values -------------------------------------------------------------------

    def GetFlds(self, flds, container, addtype):
        flds = self._ResolveFlds(flds, object=None, addtype=addtype, addHidden=1, addReadonly=0)
        return self._LoadFldsConf(flds, container, addtype)


    def GetFldsAdd(self, container, addtype):
        flds = []
        typedef = self.context.app.configurationQuery.GetObjectConf(addtype)
        if addtype in self.ifaceConf.addflds:
            flds = self.ifaceConf.addflds[addtype]["fields"]
        else:
            conf = self._GetFirstByInterfaces(typedef, self.ifaceConf.addflds)
            if conf:
                flds = conf["fields"]
        if not flds:
            # use type configuration
            if typedef.get("forms") and typedef.forms.get("create"):
                flds = typedef.forms["create"].get("fields", [])
        flds = self._ResolveFlds(flds, object=None, addtype=addtype, addHidden=1, addReadonly=0)
        return self._LoadFldsConf(flds, container, addtype)
    
    
    def GetFldsEdit(self, object):
        flds = []
        if object.GetTypeID() in self.ifaceConf.editflds:
            flds = self.ifaceConf.editflds[object.GetTypeID()]["fields"]
        else:
            conf = self._GetFirstByInterfaces(object, self.ifaceConf.editflds)
            if conf:
                flds = conf["fields"]
        if not flds:
            # use type configuration
            conf = object.configuration
            if conf.get("forms") and conf.forms.get("edit"):
                flds = conf.forms["edit"].get("fields", [])
        flds = self._ResolveFlds(flds, object=object, addtype=None, addHidden=1, addReadonly=0)
        return self._LoadFldsConf(flds, object)
    
    
    def GetFldsMetaView(self, object):
        flds = []
        if not self.ifaceConf.metaflds:
            return flds
        if object.GetTypeID() in self.ifaceConf.metaflds:
            flds = self.ifaceConf.metaflds[object.GetTypeID()]["fields"]
        else:
            conf = self._GetFirstByInterfaces(object, self.ifaceConf.metaflds)
            if not conf:
                return flds
            flds = conf["fields"]
        flds = self._ResolveFlds(flds, object=object, addtype=None, addHidden=0, addReadonly=1)
        return self._LoadFldsConf(flds, object)


    def GetFldsDataView(self, object, files=None):
        flds = []
        if not self.ifaceConf.dataflds:
            return flds
        if object.GetTypeID() in self.ifaceConf.dataflds:
            flds = self.ifaceConf.dataflds[object.GetTypeID()]["fields"]
        else:
            conf = self._GetFirstByInterfaces(object, self.ifaceConf.dataflds)
            if not conf:
                return flds
            flds = conf["fields"]
        flds = self._ResolveFlds(flds, object=object, addtype=None, addHidden=0, addReadonly=1)
        flds = self._LoadFldsConf(flds, object)
        if files!=None:
            flds2 = []
            if files:
                for f in flds:
                    if f.datatype=="file":
                        flds2.append(f)
            else:
                for f in flds:
                    if f.datatype != "file":
                        flds2.append(f)
            flds=flds2
        return flds

    
    def GetTabs(self, object):
        tabs = self._GetAllByInterfaces(object, self.ifaceConf.tabs)
        return tabs
    
    
    def GetSettings(self, object):
        tabs = self._GetAllByInterfaces(object, self.ifaceConf.settings)
        return tabs


    def GetShortcuts(self, object):
        sc = self._GetAllByInterfaces(object, self.ifaceConf.shortcuts)
        return sc
    

    def GetSearchConf(self, searchid, container):
        if searchid and str(searchid) in self.ifaceConf.searchconf:
            c = self.ifaceConf.searchconf[searchid]
        else:
            c = self._GetFirstByInterfaces(container, self.ifaceConf.searchconf)
        if c:
            c["fields"] = self._GetFldsList(c["fields"], container, c["type"])
            c["form"] = self._GetFldsSearch(c["form"], container, c["type"])
            return c
        return {}


    # Redirects and navigation ------------------------------------------------------------

    def GetRedirect(self, action, view):
        if action == "default":
            v = "view"
            for d in self.ifaceConf.defaultviews:
                if self._ProvidesOne(view.context, d.get("interfaces")):
                    v = d["id"]
                    break
            return view.FolderUrl(view.context)+v
        
        elif action == "duplicate":
            return view.FolderUrl(view.context)+"edit"

        elif action == "deletelist":
            ref = self.GetFormValue("ref")
            return ref or view.PageUrl(view.context)

        return "parent"
    

    # current url / section -------------------------------------------------------------------------
    
    def IsInCurrentTree(self, item):
        """
        Check if navigation item is in current hierarchy or current page
        
        returns 0: outside, 1: in hierarchy, 2: current page 
        """
        url = self.request.url
        id = self.ToUrl(item)
        if url == id:
            return 2
        elif url.startswith(id):
            return 1
        return 0

    
    # field handling ---------------------------------------------------
    
    def _ProvidesOne(self, object, ifaces):
        if not ifaces:
            return False
        for i in ifaces:
            try:
                if isinstance(i, str):
                    i = ResolveName(i)
            except:
                continue
            if i.providedBy(object):
                return True
        return False

        
    def _GetFirstByInterfaces(self, object, conflist):
        """
        object may be object instance or object type id
        """
        if isinstance(object, str):
            object = self.context.app.configurationQuery.GetObjectConf(object)
        if IObjectConf.providedBy(object):
            object = self.context.root.factory.VirtualObj(object)
        if hasattr(conflist, "keys"):
            for k in list(conflist.keys()):
                if not IConf.providedBy(conflist[k]):
                    continue
                ifs = conflist[k].get("interfaces")
                if self._ProvidesOne(object, ifs):
                    return conflist[k]
        else:
            for k in conflist:
                if not IConf.providedBy(k):
                    continue
                ifs = k.get("interfaces")
                if self._ProvidesOne(object, ifs):
                    return k
        return None
    

    def _GetAllByInterfaces(self, object, conflist):
        l=[]
        if hasattr(conflist, "keys"):
            for k in list(conflist.keys()):
                if not IConf.providedBy(conflist[k]):
                    continue
                ifs = conflist[k].get("interfaces")
                if not ifs:
                    l.append(conflist[k])
                    continue
                if self._ProvidesOne(object, ifs):
                    l.append(conflist[k])
        else:
            for k in conflist:
                if not IConf.providedBy(k):
                    continue
                ifs = k.get("interfaces")
                if not ifs:
                    l.append(k)
                    continue
                if self._ProvidesOne(object, ifs):
                    l.append(k)
        return l

    
    def _ResolveFlds(self, flist, object=None, addtype=None, addHidden=1, addReadonly=0):
        """
        Resolve field field list and expand 'AllTypeDataFlds' and 'AllTypeMetaFlds' with 
        real fields.
        """
        cq = self.context.app.configurationQuery
        flds = []
        for f in flist:
            if f == AllTypeDataFlds:
                if addtype:
                    typefields = cq.GetAllObjectFlds(addtype)
                else:
                    typefields = cq.GetAllObjectFlds(object.GetTypeID())
                for f2 in typefields:
                    if not addReadonly and f2.get("readonly",False):
                        continue
                    if not addHidden and f2.get("hidden",False):
                        continue
                    flds.append(f2)

            elif f == AllTypeMetaFlds:
                for f2 in cq.GetAllMetaFlds():
                    if not addReadonly and f2.get("readonly",False):
                        continue
                    if not addHidden and f2.get("hidden",False):
                        continue
                    flds.append(f2)
            else:
                flds.append(f)
        return flds

    
    def _LoadFldsConf(self, fields, object, pool_type=None):
        """
        Lookup field configurations for all fields listed with field.id
        """
        if not pool_type:
            try:
                pool_type = object.GetTypeID()
            except:
                pass
        confs = []
        cq = self.context.app.configurationQuery
        for f in fields:
            if not isinstance(f, str):
                confs.append(f)
                continue
            f = cq.GetFld(f, pool_type)
            if f:
                confs.append(f)
        return confs


    def _GetFldsList(self, listflds, container, listtype):
        cq = self.context.app.configurationQuery
        flds = []
        for f in listflds:
            if f == AllTypeDataFlds:
                for f2 in cq.GetAllObjectFlds(listtype):
                    if not f2.get("readonly",False):
                        flds.append(f2)
            else:
                flds.append(f)
        return self._LoadFldsConf(flds, container, listtype)
    
    def _GetFldsSearch(self, searchflds, container, listtype):
        cq = self.context.app.configurationQuery
        flds = []
        for f in searchflds:
            if f == AllTypeDataFlds:
                for f2 in cq.GetAllObjectFlds(listtype):
                    if not f2.get("readonly",False):
                        flds.append(f2)
            else:
                flds.append(f)
        return self._LoadFldsConf(flds, container, listtype)
    

    def _AddObject(self, typeID, title, context=None, url="objid_url"):
        context = context or self.context
        if not context.IsTypeAllowed(typeID, self.User()):
            raise ValueError("Not allowed")

        form = ObjectForm(view=self, context=context, loadFromType=context.app.configurationQuery.GetObjectConf(typeID), autofill="off")
        form.subsets = {"create": {"fields": self.GetFldsAdd(context, typeID), "actions": ["default", "create", "cancel"]}}
        form.use_ajax = False
        form.Setup(subset="create", addTypeField=True)
        result, data, action = form.Process(redirectSuccess=url, redirectCancel=self.FolderUrl(context))
        if result and not data:
            self.Redirect(self.FolderUrl(context))
            return
        return dict(content=data, result=result, view=self, head=form.HTMLHead(), title=title)


    def _AddObjectIframe(self, typeID, title, context=None, url="objid_url"):
        context = context or self.context
        if not context.IsTypeAllowed(typeID, self.User()):
            raise ValueError("Not allowed")

        form = ObjectForm(view=self, context=context, loadFromType=context.app.configurationQuery.GetObjectConf(typeID), autofill="off")
        form.subsets = {"create": {"fields": self.GetFldsAdd(context, typeID), "actions": ["default", "create"]}}
        form.use_ajax = False
        form.Setup(subset="create", addTypeField=True)
        result, data, action = form.Process(renderSuccess=False)
        if result and action.id=="create":
            info = """
            <input type="hidden" class="addformresult" name="id" value="%d">
            <input type="hidden" class="addformresult" name="title" value="%s">
            <br>
            <p class="alert">Sie können den neuen Eintrag "%s" jetzt mit dem Button "Übernehmen" ins Formular übertragen.</p>
            """ % (result.id, result.meta.title, result.meta.title)
            return dict(content=data+info, result=result, view=self, head="", title=title)
        return dict(content=data, result=result, view=self, head=form.HTMLHead(), title=title)


    # helper -----------------------------------------------------------
    
    def ResolveUrl(self, url, context=None):
        """
        Resolve a string to url for object or the current context.

        Possible values:
        
        - page_url
        - obj_url
        - obj_folder_url
        - parent_url
        """
        if not url:
            return ""
        if context is None:
            context = self.context
        if url == "view_url":
            return self.FolderUrl(context)
        elif url == "section_url":
            try:
                section = self.request.currentSection
            except:
                section = ""
            return self.FolderUrl(context) + section
        elif url == "page_url":
            url = self.PageUrl(context)
        elif url == "obj_url":
            url = self.Url(context)
        elif url.find("objid_url")!=-1:
            url = url.replace("objid_url", self.FolderUrl(context.parent) + str(context.id))
        elif url.find("obj_folder_url")!=-1:
            url = url.replace("obj_folder_url", self.FolderUrl(context))
        elif url == "root_url":
            url = self.FolderUrl(context.root)
        elif url == "parent_url":
            url = self.Url(context.parent)
        return self.ToUrl(url)
    
        
    def ToUrl(self, item, context=None):
        """
        convert iface configuration item id to url
        replaced values: context., root., parent., pool., portal.
        """
        if not context:
            context = self.context
        if isinstance(item, str):
            u = item
        else:
            u = item["id"]
        if u.find("context.")!=-1:
            u = u.replace("context.", self.FolderUrl(context))
        elif u.find("root.")!=-1:
            u = u.replace("root.", self.FolderUrl(context.root))
        elif u.find("parent.")!=-1:
            u = u.replace("parent.", self.FolderUrl(context.parent))
        elif u.find("app.")!=-1:
            u = u.replace("app.", self.FolderUrl(context.app))
        elif u.find("portal.")!=-1:
            u = u.replace("portal.", self.FolderUrl(context.app.portal))
        return u

    def GetAction(self):
        """
        get the current action id from view or request
        """
        return self.actionid or self.GetFormValue("a")
    
    
    def IFaceCacheHeader(self, response):
        """
        Add the iface pages default cache header `configuration.cache`
        """
        if self.ifaceConf.cache=="no-cache":
            self.NoCache(response)
        self.Modified(response)
        

    def Form(self, conf, callback, formkws, tag):
        typeID = conf.get("loadFromType")
        form = HTMLForm(view=self, loadFromType=self.context.app.configurationQuery.GetObjectConf(typeID), autofill="off")
        form.fields = self.GetFlds(conf.fields, self.context, typeID)
        form.actions = [
            Conf(id="default",    method="StartForm",             name="Initialize",   hidden=True),
            Conf(id=tag,          method="ReturnDataOnSuccess",   name="Submit",       hidden=False),
        ]
        form.use_ajax = False
        form.ListenEvent("success", callback)
        form.Setup()
        result, data, action = form.Process(**formkws)
        if result and not data:
            self.Redirect(self.PageUrl(self.context))
            return
        return {"content": data, "result": result, "view": self, "foot": form.HTMLHead(), "pageinfo": tag}

    
    # default view callables ------------------------------------------------------------

    def slot(self):
        return {}

    def settings(self):
        return {}

    def tmpl(self):
        return {}

    def base(self):
        self.request.currentSection = "base"
        return {}


    # merged as one class for easier subclassing
    # class ObjectIFace(IFaceView, Parts):
    
    def default(self):
        url = self.GetRedirect("default", self)
        self.Redirect(url)

    def open(self):
        id = self.GetFormValue("id")
        v = self.GetFormValue("v")
        obj = None
        if id:
            if not IContainer.providedBy(self.context):
                obj = self.context.parent.GetObj(id)
            else:
                obj = self.context.GetObj(id)
            if obj is None:
                root = self.context.root
                obj = root.LookupObj(id)
        if not obj:
            return HTTPNotFound()
        url = self.FolderUrl(obj)
        self.Redirect(url)

    def meta(self):
        self.request.currentTab = "context.meta"
        return {}

    def view(self):
        self.request.currentTab = "context.view"
        return {"pageinfo": "view", "msgs": []}

    def viewlist(self):
        self.request.currentTab = "context.viewlist"
        searchid = self.context.configuration.id
        if not searchid or not str(searchid) in self.ifaceConf.searchconf:
            if IRoot.providedBy(self.context):
                searchid = "root"
                if not str(searchid) in self.ifaceConf.searchconf:
                    searchid = None
            else:
                searchid = None
        return {"pageinfo": "view", "msgs": [], "searchconf": searchid or "default"}

    def viewsearch(self):
        self.request.currentTab = "context.search"
        self.request.currentSection = "search"
        return dict(pageinfo="search", msgs=[], searchconf="search")

    def options(self):
        self.request.currentTab = "context.options"
        app = self.context.app
        selected = self.GetFormValue("tag")
        if selected:
            tool = app.GetTool(selected, contextObject=self.context)
            data = self.RenderView(tool)
            # pyramid bug? reset the active view in request
            self.request.__dict__['__view__'] = self
            return {"content": data, "tools": [], "tool": tool, "pageinfo": "options"}

        t = app.configurationQuery.GetAllToolConfs(contextObject=self.context)
        return {"content": "", "tools": t, "tool": None, "pageinfo": "options"}

    def add(self):
        self.request.currentTab = "context.add"
        typeID = self.GetFormValue("pool_type")
        if not typeID:
            return {"content": self.selectType(), "result": True}
            #raise ValueError, "No type id found"
        if not self.context.IsTypeAllowed(typeID, self.User()):
            raise ValueError("Not allowed")

        form = ObjectForm(view=self, loadFromType = self.context.app.configurationQuery.GetObjectConf(typeID), autofill="off")
        form.subsets = {"create": {"fields": self.GetFldsAdd(self.context, typeID), "actions": ["default","create"]}}
        form.use_ajax = False
        form.Setup(subset="create", addTypeField=True)
        result, data, action = form.Process(redirectSuccess="view_url")
        if result and not data:
            self.Redirect(self.PageUrl(self.context))
            return
        return {"content": data, "result": result, "view": self, "foot": form.HTMLHead(), "pageinfo": "add"}

    def edit(self):
        self.request.currentTab = "context.edit"
        form = ObjectForm(loadFromType = self.context.configuration, view=self, autofill="off")
        form.subsets = {"edit": {"fields": self.GetFldsEdit(self.context), "actions": ["edit"], "defaultAction": "defaultEdit"}}
        form.Setup(subset="edit")
        result, data, action = form.Process(redirectSuccess="view_url")
        return {"content": data, "result": result, "foot": form.HTMLHead(), "pageinfo": "edit"}

    def form(self):
        self.request.currentTab = "context.options"
        typeID = self.GetFormValue("pool_type")
        if not typeID:
            return {"content": self.selectType(), "result": True}
            #raise ValueError, "No type id found"
        if not self.context.IsTypeAllowed(typeID, self.User()):
            raise ValueError("Not allowed")

        form = ObjectForm(view=self, loadFromType = self.context.app.configurationQuery.GetObjectConf(typeID), autofill="off")
        form.subsets = {"create": {"fields": self.GetFldsAdd(self.context, typeID), "actions": ["default","create"]}}
        form.use_ajax = False
        form.Setup(subset="create", addTypeField=True)
        result, data, action = form.Process(redirectSuccess="view_url")
        if result and not data:
            self.Redirect(self.PageUrl(self.context))
            return
        return {"content": data, "result": result, "view": self, "foot": form.HTMLHead(), "pageinfo": "add"}

    def duplicate(self):
        url = self.GetRedirect("duplicate", self)
        self.Redirect(url)

    def deletelist(self):
        self.request.currentTab = "context.options"
        ids = self.GetFormValue("ids")
        if isinstance(ids, str):
            if "," in ids:
                ids = ids.split(",")
            else:
                ids = [ids]
        result = {"msgs": [], "objsToDelete": [], "action": "deletec", "result": False, "ids": ids, "pageinfo": "delete"}
        if not ids:
            result["msgs"] = [translator()(_("Nothing to delete"))]
            return result
        delete = self.GetFormValue("delete")
        objs = []
        for i in ids:
            o = self.context.obj(i)
            if o is not None:
                # check delete permission
                if self.Allowed("delete", o):
                    objs.append(o)
                else:
                    result["msgs"].append(o.meta.title + " " + translator()(_("Unauthorized. Delete is not allowed.")))
        if delete != "1":
            result["objsToDelete"] = objs
            return result
        ok = False
        user = self.User()
        for o in objs:
            # linked as unit/unitlist
            linked = self.context.root.search.GetReferences(o.id, types=None, sort="id")
            if linked:
                result["msgs"].append(o.meta.title + ": " + translator()(_("Still linked. Not deleted.")) + " " + str([l[0] for l in linked]))
                ok = False
                continue
            try:
                ok = self.context.Delete(o.id, user=user, obj=o)
            except Exception as e:
                result["msgs"].append(str(e))
                ok = False
        if not ok:
            return result
        url = self.GetRedirect("deletelist", self)
        self.Redirect(url, messages=[_("OK")])


    def delete(self, url="view_url"):
        self.request.currentTab = "context.options"
        delete = self.GetFormValue("delete")
        result = {"msgs": [], "objsToDelete": [self.context], "action": "deleteo", "result": False, "ids":None, "pageinfo": "delete"}
        if delete != "1":
            return result
        ok = False
        parent = self.context.parent
        try:
            ok = parent.Delete(self.context.id, user=self.User(), obj=self.context)
        except Exception as e:
            result["msgs"].append(str(e))
            ok = False
        if not ok:
            return result
        self.Redirect(self.ResolveUrl(url, parent), messages=[translator()(_("OK. Deleted."))])

    def delfile(self):
        self.ResetFlashMessages()
        file = self.GetFormValue("fid")
        user = self.User()
        try:
            r = self.context.DeleteFile(file, user)
            if not r:
                m = translator()(_("Something went wrong!"))
            else:
                m =  translator()(_("OK. Deleted."))
        except Exception as e:
            m=str(e)
        r = Response(content_type="text/html", conditional_response=True)
        r.text = "<span>%(msg)s</span>" % {"name": str(file), "msg":m}
        return r


    def action(self):
        action = self.GetFormValue("action")
        url = self.GetFormValue("ref")
        if not url:
            url = self.FolderUrl()
        values = dict()
        context = self.context
        user = self.User()

        # interactive transitions mit form auslesen und verarbeiten. nur 1 form pro transition.
        workflow = context.workflow
        process = workflow.GetWf()
        transitions = process.PossibleTransitions(context.meta.pool_wfa, action=action, context=context, user=user)
        if len(transitions)>=1:
            t = transitions[0]
            fncs = t.GetInteractiveFunctions()
            if fncs:
                fnc = fncs[0]
                if hasattr(fnc, "__init__") and fnc.form is None:
                    form = fnc(self).form
                else:
                    form = fnc
                form.Setup()
                form.widget.item_template = "field_onecolumn"
                form.widget.action_template = "form_actions_onecolumn"
                result, data, formaction = form.Process(renderSuccess=False, redirectCancel=url)
                if not result or (result and formaction.id != "submit"):
                    return dict(result=result, head=form.HTMLHead(), content=data, transition=t)
                values = result

        try:
            # workflow ausführen. form daten in 'data' wenn verarbeitet.
            transition = workflow.WfAction(action, user, values=values)
        except WorkflowNotAllowed:
            self.Redirect(url, messages=["Bereits ausgeführt"])
            return
        self.context.CommitInternal(user)
        msg = transition.message or "OK"
        self.Redirect(url, messages=[msg])

    def transition(self):
        transition = self.GetFormValue("t")
        url = self.GetFormValue("ref")
        if not url:
            url = self.Url()
        user = self.User()
        self.context.workflow.WfAction("", user, transition=transition)
        self.context.CommitInternal(user)
        msg = "OK"
        self.Redirect(url, messages=[msg])


    def wf(self):
        self.request.currentTab = "context.options"
        return {"pageinfo": "wf"}

    def tool(self):
        self.request.currentTab = "context.options"
        return {"pageinfo": "tool"}
    
    def profile(self):
        from nive_userdb.userview.view import UserForm
        from nive.security import IAdminUser

        user = self.User(sessionuser=False)
        if IAdminUser.providedBy(user):
            return dict(content="Singned in as System Admin", result=False, title="Profile")

        userdb = self.context.app.portal.userdb
        typeconf=userdb.configurationQuery.GetObjectConf("user")
        form = UserForm(view=self, context=user, loadFromType=typeconf)
        form.Setup(subset="edit")
        result, data, action = form.Process(renderSuccess=True)
        return dict(content=data, result=result, title="Profile")

    def selectType(self):
        user = self.User()
        lt = self.context.GetAllowedTypes(user)
        tmpl = """<p><a href="add?pool_type=%s" class="btn btn-primary add">%s</a></p>"""
        html = ""
        for t in lt:
            html += tmpl % (t["id"], t["name"])
        return html

    

