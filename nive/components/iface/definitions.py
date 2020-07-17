# -*- coding: utf-8 -*-


from nive.definitions import Conf
from nive.definitions import IObject, IContainer, IRoot, INonContainer

from nive.definitions import baseConf
from nive.definitions import Interface, implementer
from nive.definitions import ConfigurationError



class IIFaceRoot(Interface):
    """ """


class IIFaceConf(Interface):
    """ """


AllTypeDataFlds = 1
AllTypeMetaFlds = 2
AllTypeFlds = 3


@implementer(IIFaceConf)
class IFaceConf(baseConf):
    """
    peak interface view configuration class
    -----------------------------------------
    configuration attributes:
    
    - id: iface module id (optional)
    - name: iface module name (optional)
    - slogan: iface header slogan
    - sections: header bar links
    - currentsection: the active section. can be set for the whole module.
    - backlink: backlink added to head logo
    - headlink: single link on the right, and left of headoptions.
    - headlinkAnonymous: single link on the right, and left of headoptions.
    - headoptions: header options dropdown on the right.
    - navigation: left navigation
    - path: enable or disable breadcrumbs
    - tabs: object content tabs (default or type specific)
    - settings: settings drop down content specific
    - objectheader: object tab header block (default or type specific)
    - shortcuts: object shortcuts bar (default or type specific)
    - pageinfos: dict with page.id providing additional information for page rendering
    - addflds: fields rendered in add form 
    - editflds: fields rendered in edit form
    - metaflds: field list for meta page view (default or type specific)
    - dataflds: field list for data page view (default or type specific)
    - searchconf: search configurations including form, list fields and options. default or type specific. 
    - defaultviews: default (name="") view redirects based on interfaces.
    
    Configures most parts of the interface for html rendering. Required by view classes, parts and search. 
    
    - container list search parameter fields
    - container list fields
    - container list options (cut-copy-paste, delete)
    - edit fields
    - add fields
    - meta fields
    - object shortcuts (add, duplicate, tools, workflow, ccp, delete)
    - object iface tabs
    - interface navigation type
    - interface display name
    
    Url handling in sections, tabs, navigation:
    Calls ToUrl to map item.id to URL. The prefix of id is used to generate the link
    included in the html. e.g. root.search maps to http://server.com/root/search
    Possible values are
    
    - context
    - parent
    - root
    - pool
    - portal
    
    searchfield rendere callback example: ::

        def renderStateIcon(field, value, context, data):
            return '<img src="/static/images/state%d.gif" title="Active state: %d"/>' % (data, data)

    
    implements: IIFaceConf
    """

    def __init__(self, copyFrom=None, **values):
        self.id = ""
        self.name = ""
        self.slogan = ""
        self.logo = ""
        self.cache = "no-cache"
        self.containercls = "container-fluid"
        
        # id: used as url, name: display name, ref: section reference used to highlight active section
        self.sections = [
            Conf(id="root.base",     name="Overview", ref="b"),
            Conf(id="root.view",     name="Content",  ref=""),
            Conf(id="root.search",   name="Search",   ref="s"),
            Conf(id="root.settings", name="Settings", ref="e")
        ]
        
        # item as string or Conf
        # string: called as class method
        # Conf: id: used as url, name: display name, icon: display icon
        self.backlink = None
        self.headlink = None
        self.headlinkanonymous = None
        self.headoptions = [
            "head_logout", 
            #"head_search"
        ]
        
        self.navigation = [
            Conf(id="root.view", name="Folder", widget="navigation_folder", baseID=0, sort="title")
        ]
        
        self.path = True

        self.tabs = [
            Conf(id="context.viewlist", name="Content",  permission= "iface_view", interfaces=[IContainer]),
            Conf(id="context.view",     name="View",     permission= "iface_view", interfaces=[IObject]),
            Conf(id="context.edit",     name="Edit",     permission= "iface_edit", interfaces=[IObject]),
            Conf(id="context.add",      name="Add",      permission= "iface_add",  interfaces=[IContainer]),
            Conf(id="context.options",  name="Options",  permission= "iface_view", interfaces=[IObject]),
            Conf(id="context.meta",     name="System",   permission= "iface_view", interfaces=[IObject])
        ]
        
        self.objectheader = [
            Conf(id="object_info", interfaces=[IObject])
        ]

        self.shortcuts = [
            Conf(id="shortcut_add",     interfaces=[IContainer]), 
            Conf(id="shortcut_tools",   interfaces=[IObject]),
            Conf(id="shortcut_delete",  interfaces=[INonContainer])
        ]
        
        self.settings = [
        ]

        self.pageinfos = {}
        
        self.addflds =  Conf(default=Conf(fields=["title", AllTypeDataFlds], interfaces=[IObject]))
        self.editflds = Conf(default=Conf(fields=["title", AllTypeDataFlds], interfaces=[IObject]))
        self.metaflds = Conf(default=Conf(fields=["title", AllTypeMetaFlds], interfaces=[IObject]))
        self.dataflds = Conf(default=Conf(fields=["title", AllTypeDataFlds], interfaces=[IObject,IContainer]))
        
        # search and list defaults. can be replaced on type base.
        self.searchconf = Conf(default = 
            Conf(
                type = None,
                container = True,
                queryRestraints = None,
                callback = None, # callback for parameter lookup: callback(view, parameter, operators, searchconf)
                listoptions = ["ccp", "deletec"],
                form = ["pool_type", "title"],
                fields = ["pool_state","pool_type", "title", "pool_create","pool_createdby", "pool_change", "pool_changedby", "id"],
                method = None, # GET or POST
                max = 30,
                ascending = True,
                interfaces = [IContainer],
                renderer = None,
                options = None
            )
        )
            
        self.defaultviews= [
            Conf(id="viewlist", permission="iface_view", interfaces=[IContainer]),
            Conf(id="view", permission="iface_view", interfaces=[IObject]),
            Conf(id="base", permission="iface_view", interfaces=[IRoot])
        ]

        baseConf.__init__(self, copyFrom, **values)


    def __str__(self):
        return "%(id)s (%(name)s)" % self

    def test(self):
        report = []
        # check id
        if len(self.id) > 25:
            report.append((ConfigurationError, " ServiceConf.id too long. 25 chars allowed.", self))
        return report        
        

        
    

    