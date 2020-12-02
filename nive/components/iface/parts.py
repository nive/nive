

from nive.definitions import Conf, IRoot, IContainer
from nive.i18n import translate, _


class Hint(object):
    """
    Hint class
    Use hints to point users to outstanding actions and explain the situation.
    
    Hints can linked be linked to hint-sections defined in the interface and be
    loaded on precondition callback functions. Callbacks take the current view
    context as parameter.
    
    The user can disable hints in his personal settings.  
    """
    
    def __init__(self, id, sections, condition, text):
        self.id = id
        self.sections = sections
        self.condition = condition
        self.text = text
        
    def Visible(self, section, view):
        if not section in self.sections:
            return False
        return self.condition(view)

    def Render(self, values=None):
        return self.text.render(values)



class Parts:
    """
    Renders interface parts
    """
    
    action = None
    static = ""
    activateUnitInfo = False
        
    # html parts -------------------------------------------------------

    def title(self):
        """
        html head title
        """
        t = self.context.app.configuration.title
        if t:
            return "%s - %s" % (self.ifaceConf.name, t)
        return self.ifaceConf.name

    @property
    def tmpl_macro(self):
        return self.ifaceConf.tmpl_macro

    def sections(self, count=100, context=None):
        """
        html body div#header div#headOptions div#mainNav
        
        main navigation list
        
        count: number of sections to be rendered. 
        """
        tmpl = """<li class="nav-item %(class)s"><a class="nav-link" href="%(url)s" title="%(description)s"> %(name)s </a></li>"""
        html = []
        try:
            n = self.request.currentSection
        except:
            try:
                n=self.ifaceConf.currentSection
            except:
                n = self.GetFormValue("sec")
        if self.ifaceConf.sections == "portal":
            self.ifaceConf.sections = self.context.app.portal.sections
        for s in self.ifaceConf.sections[:count]:
            permission = s.get("permission")
            if permission and not self.Allowed(permission, context or self.context):
                continue
            cls = "normal"
            if n == s["ref"]:
                cls = "active"
            url = self.ToUrl(s)
            html.append(tmpl % {"url": url, "class": cls, "name": translate(s["name"]), "description": translate(s.get("description",""))})
        return "".join(html)
    

    def backlink(self):
        """
        backlink added to head logo.
        """
        if not self.ifaceConf.backlink:
            return "/"
        return self.ToUrl(self.ifaceConf.backlink)


    def headlink(self):
        """
        single link in header right to headoptions drop down.
        """
        if not self.ifaceConf.headlink:
            return ""
        conf = self.ifaceConf.headlink
        if conf.get("icon"):
            return """
<a href="%(url)s" class="nav-link"><img src="%(static)s%(icon)s" title="%(name)s"> %(name)s</a>
        """ % {"url": self.ToUrl(conf), "name": translate(conf.name), "static": self.static, "icon": conf.icon}
        # no icon configured
        return """
<a href="%(url)s" class="nav-link">%(name)s</a>
        """ % {"url": self.ToUrl(conf), "name": translate(conf.name), "static": self.static}
        

    def headlinkAnonymous(self):
        """
        single link in header right to headoptions drop down.
        """
        if not self.ifaceConf.headlinkanonymous:
            return ""
        conf = self.ifaceConf.headlinkanonymous
        if conf.get("icon"):
            return """
<a href="%(url)s"><img src="%(static)s%(icon)s" title="%(name)s"> %(name)s</a>
        """ % {"url": self.ToUrl(conf), "name": translate(conf.name), "static": self.static, "icon": conf.icon}
        # no icon configured
        return """
<a href="%(url)s">%(name)s</a>
        """ % {"url": self.ToUrl(conf), "name": translate(conf.name), "static": self.static}


    def headoptions(self, context=None):
        """
        html body div#header div#userOptions
        user options in head: head_logout, head_search
        """
        html = []
        for u in self.ifaceConf.headoptions:
            if isinstance(u, str):
                if u=="divider":
                    html.append("""<div class="dropdown-divider"></div>""")
                else:
                    html.append(getattr(self, u)())
            else:
                permission = u.get("permission")
                if permission and not self.Allowed(permission, context or self.context):
                    continue
                html.append(self.head_link(u, cls="dropdown-item"))
        return "".join(html)
    

    def navigation(self):
        """
        left column navigation
        """
        tmpl = """
 <div onclick="%(url)s" class="nav-link disabled nav-header">%(name)s</div>
 %(content)s
        """ 
        html = ["""<nav class="nav flex-column">"""]
        for n in self.ifaceConf.navigation:
            html.append(tmpl % {"url": self.ToUrl(n), "content": getattr(self, n["widget"])(n), "name": translate(n["name"], self.request)})
        html.append("""</nav> """)
        return "".join(html)

        
    def path_render(self, items, css="path"):
        """
        Renders path items as html
        
        items: dict with url, title, class 
        """
        sep = """ <span class="divider">/</span>"""
        tmpl = """<li class="%(class)s"><a href="%(url)s">%(title)s</a></li>"""
        html=["""<ul class="%s">"""%css]
        html.append(sep.join([tmpl % i for i in items]))
        html.append("</ul>")
        return "".join(html)

    
    def path(self, object=None, css="path", addLink=None):
        """
        Parent links in content top
        addLink: custom last element in list as Conf(id='url',name='name') 
        
        use css=breadcrumb for bootstrap style
        """
        if not self.ifaceConf.path:
            return ""
        html=[]
        if addLink:
            html.append({"url":self.ToUrl(addLink.get('id')), "title":translate(addLink.get('name')), "class":""})
        if not object:
            o = self.context
        else:
            o = object
        objs = list(o.GetParents())
        objs.reverse()
        for p in objs:
            html.append({"url":self.FolderUrl(p), "title":p.GetTitle(), "class":""})
        html.append({"url":self.FolderUrl(o), "title":o.GetTitle(), "class":"active"})
        return self.path_render(html, css=css)
    
    
    def contentHeader(self, pageinfo=None):
        """
        renders the title for the content area
        """
        if pageinfo:
            return pageinfo.get("title", "")
        try:
            return self.context.meta.title
        except:
            return ""
    
    
    def tabs(self, active=None):
        """
        html body div.mainBoxContent div#unit_tabs
        tabs in content
        """
        tabs = self.GetTabs(self.context)
        if not tabs:
            return ""
        tmpl = """<li class="nav-item"><a class="nav-link %(cls)s" href="%(url)s">%(name)s</a></li>"""
        if active is None:
            try:
                active = self.request.currentTab
            except:
                pass
        html = ["""<ul class="nav nav-tabs">"""]
        for t in tabs:
            permission = t.get("permission")
            if permission and not self.Allowed(permission, self.context):
                continue
            cls = ""
            if active == t["id"]:
                cls = "active"
            html.append(tmpl % {"url": self.ToUrl(t), "name": translate(t["name"]), "cls": cls})
        html.append("</ul>")
        return "".join(html)


    def settingsLinks(self, base=None):
        """
        html body div.mainBoxContent div#unit_settings
        dropdown in content
        """
        li = self.settingsStripped(base=base)
        if not li:
            return ""
        return """
<div class="dropdown float-right unit-settings">
  <button class="btn btn-sm btn-light dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
    <i class="icon-cog"></i> %(Settings)s
    <span class="caret"></span>
  </button>
  <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
    %(li)s
  </div>
</div>  """% dict(li=li, Settings=translate(_("Settings"), self.request))


    def settingsStripped(self, active=None, base=None, addSlots=False, cls="dropdown-item"):
        """
        settings as <li> list
        """
        settings = self.GetSettings(self.context)
        if addSlots:
            service = self.context.service
            if service is not None:
                for slot in service.slots:
                    settings.append(Conf(id="context.slot?sid="+slot, name=service.get(slot).name, icon=""))

        if not settings:
            return ""
        if active is None:
            try:
                active = self.request.currentTab
            except:
                pass

        app = self.context.app
        base0 = ""
        if base=="dev":
            from peak.config import ROUTING # TODO reconfigure ROUTING
            base = ROUTING.development
            base0 = self.Url(app.portal)
            if base.endswith("/") and not base0.endswith("/"):
                base = base[:-1]
            if not base.endswith("/") and base0.endswith("/"):
                base += "/"

        def rewriteBase(url):
            if not base0:
                return url
            return url.replace(base0, base)

        tmpl = """<a class="%(class)s" href="%(url)s">%(icon)s %(name)s</a>"""
        html = []
        for t in settings:
            permission = t.get("permission")
            if permission and not self.Allowed(permission, self.context):
                continue
            cc = cls
            if active == t["id"]:
                cc += " active"
            ic = t.get("icon","")
            icon = ("""<i class="%s"></i>"""%ic) if ic else ""
            html.append(tmpl % {"url": rewriteBase(self.ToUrl(t)), "name": translate(t["name"], self.request), "class": cc, "icon": icon})

        return "\r\n".join(html)


    def unitInfo(self, fields):
        """
        disabled!!!
        html body div.mainBoxContent div.unit_info
        block below tabs with object info
        """
        if not self.activateUnitInfo:
            return "" # TODO config unitinfo

        if self.context.IsRoot():
            return " "
        if fields == "edit":
            fields = (('pool_wfa', 'pool_create', 'pool_createdby'),('id', 'pool_change', 'pool_changedby'))
        elif type(fields) == type(""):
            fields = (('id', 'pool_state', 'pool_category'),)
        html = """
<div class="unit_info">
 <div class="blockOptions" style="float:right;margin:5px;">
  Details <a href="" id="unitInfo_b" onClick="javascript:swBl('unitInfo',this);return false;"><img src="%(static)simages/maximize.png" alt="Details ein-/ausblenden" style="vertical-align: bottom" /></a>
 </div>
 <table id="unitInfo" cellpadding="0" cellspacing="0">
  %(rows)s
 </table>
 <br style="clear:both"/>
 <!--script language="javascript">swBlLoad('unitInfo','unitInfo_b');</script-->
</div>
        """
        rows = []
        for row in fields:
            rows.append("<tr>")
            first = True
            for f in row:
                fld = self.context.GetFieldConf(f)
                cls = ""
                if first:
                    cls = " class='first'"
                    first = False
                rows.append("""<th%s>%s</th><td>%s</td>""" % (cls, fld["name"], self.RenderField(fld, self.context.meta.get(f, self.context.data.get(f)))))
            rows.append("</tr>")
        html = html % {"static": self.static, "rows": rows}
        return html

     
    def messages(self, msgs=None, error=0):
        """
        html body div.mainBoxContent ul
        displays messages if found in context or passed as msgs
        class="alert alert-success"
        """
        cls = "alert-success"
        if error:
            cls = "alert-error"
        if not msgs:
            msgs = self.GetFormValue("msgs")
        flashs = self.request.session.peek_flash()
        if not msgs and not flashs:
            return ""
        html = ["""<div class="alert %s"><ul>"""%cls]
        if msgs:
            for m in msgs:
                html.append("""<li>%s</li>""" % (m))
        if flashs:
            for m in self.request.session.pop_flash():
                html.append("""<li>%s</li>""" % (m))
        html.append("""</ul></div>""")
        return "".join(html)
    
    
    def hints(self, section):
        """
        Renders the given hint section for the current view context
        """
        if not self.ifaceConf.hints:
            return ""
        html = []
        for hint in self.ifaceConf.hints:
            if not hint.Visible(section, self):
                continue
            html.append("""<div class="alert hint">%s</div>"""%(str(hint.text)))
        return "".join(html)
     
     
    def shortcuts(self):
        """
        html body div.mainBoxContent div#unit_shortcuts
        shortcuts links / icons below unitInfo
        """
        sc = self.GetShortcuts(self.context)
        if not sc:
            return ""
        html = """<div id="unit_shortcuts" class="well alert alert-light"><div class="unit_options_block">Shortcuts</div> %s  <br class="clearBlock" /></div>"""
        l = []
        for s in sc:
            try:
                l.append(getattr(self, s["id"])())
            except Exception as e:
                l.append("Error %s (%s)" % (str(e), s["id"]))
                pass 
        return html % ("".join(l))
    
    
    # widgets ------------------------------------------------------
    """
    html widgets called in headoptions, navigation, shortcuts
    """
    
    def head_link(self, conf, cls=""):
        if conf.get("icon"):
            return """
<a href="%(url)s" class="%(cls)s"><img src="%(static)s%(icon)s" title="%(name)s"> %(name)s</a>
        """ % {"url": self.ToUrl(conf), "name": translate(conf.name), "static": self.static, "cls": cls, "icon": conf.icon}
        # no icon configured
        return """
<a href="%(url)s" class="%(cls)s">%(name)s</a>
        """ % {"url": self.ToUrl(conf), "name": translate(conf.name), "cls": cls, "static": self.static}

    def head_logout(self):
        """
        logout and help lilnk
        """
        return """
<li><a href="%(logout)s"><img src="%(static)simages/logout.png" title="Logout" align="top">%(username)s Logout</a></li>
        """ % {"logout": "/logout", "username": "", "static": self.static}


    def head_search(self):
        """
        simple searchform with textfield and button. calls search view.
        """
        return """
<div id="headSearch2">
 <span>Suche</span>
 <form action="%(url)ssearch'" method="get">
  <input type="text" name="searchPhrase" id="searchStr"/>
  <input type="submit" name="searchButton" id="searchButton" value="Start"/>
 </form>
</div>
        """ % {"url": self.FolderUrl(self.context.root)}
    
    
    def navigation_folder(self, conf):
        """
        javascript tree view for content structure.
        configuration: icon, sort, levelup, callback

        """
        sort = conf.get("sort", "title")
        container = self.context
        if not IContainer.providedBy(self.context):
            container = self.context.parent
        items = container.GetObjsList(parameter=dict(), sort=sort, containerOnly=True)
        if conf.get("icon"):
            tmpl = """<li class="nav-item"><a href="open?id=%(id)d" class="nav-link"><i class='""" + conf.get("icon") + """'></i> %(title)s</a></li>"""
        elif conf.get("state"):
            tmpl = """<li class="nav-item"><a href="open?id=%(id)d" class="nav-link">%(title)s [%(pool_state)s]</a></li>"""
        else:
            tmpl = """<li class="nav-item"><a href="open?id=%(id)d" class="nav-link">%(title)s</a></li>"""
        html = []
        if conf.get("levelup", True) and not IRoot.providedBy(self.context):
            html.append(tmpl % dict(id=container.parent.id, title="../ " + container.parent.meta.title, pool_state=""))
        cb = conf.get("callback")
        for i in items:
            if cb is not None:
                html.append(cb(i))
            else:
                html.append(tmpl % i)
        return "".join(html)


    def navigation_section(self, conf):
        """
        section with link list
        configuration: links 
        """
        tmpl = """<a href="%(url)s" class="nav-link">%(icon)s %(name)s</a>"""
        html = []
        for link in conf["links"]:
            icon = link.get("icon", "")
            if icon:
                icon = """<i class="%s"></i> """ % icon
            html.append(tmpl % {"url": self.ToUrl(link), "name": translate(link["name"], self.request), "icon": icon})
        return "".join(html)
    

    def navigation_path(self, conf):
        """
        renders the parent path as vertikal links
        """
        tmpl = """<li><a href="%(url)sview" class="level%(level)s">%(name)s</a></li>"""
        html = []
        object = self.context
        objs = list(object.GetParents())
        objs.reverse()
        objs += [self.context]
        l = 0
        for p in objs:
            html.append(tmpl % {"url":self.FolderUrl(p), "level": str(l), "name":p.GetTitle()})
            l+=1
        return "".join(html)
    

    def shortcut_add(self):
        """
        context sensitive list of add links
        """
        atypes = self.context.GetAllowedTypes(self.User())
        #atypes = self.context.app.GetAllObjectConfs(visibleOnly=True)
        if not atypes:
            return ""
        l = []
        for t in atypes:
            l.append("""<a href="add?pool_type=%(type)s"><img alt="%(name)s erstellen" src="%(static)simages/types/%(type)s_add.png" align="top" /> </a>""" % {"name": t["name"], "type": t["id"], "static": self.static})
        return """<div class="unit_options_block">%s</div>""" % ("".join(l))
        

    def shortcut_wfbuttons(self):
        """
        commit and reject icons if contained in context workflow transitions
        """
        if self.context.configuration["workflowDisabled"]:
            return ""
        wfinfo = self.context.wf.GetWfInfo(self.User())
        if not wfinfo or not wfinfo["wf"] or len(wfinfo["wf"]["transitions"])==0:
            return ""

        l = []
        redirect = self.GetFormValue('url')
        if not redirect:
            redirect = self.request.URL
        for t in wfinfo["transitions"]:
            a = ""
            if "commit" in t['applications']:
                a = "commit"
            if "reject" in t['applications']:
                a = "reject"
            if not a:
                continue
            p = self.FmtURLParam(action=a, trans=t['id'], url=redirect)
            l.append("""<a href="wf?%(param)s" class="tree"><img alt="%(name)s" src="%(static)simages/publish.png" align="top" /></a> """ % {"name": t["name"], "param": p, "static": self.static})
        return """<div class="unit_options_block">%s</div>""" % ("".join(l))
        

    def shortcut_wfselect(self):
        """
        drop down with all possible context workflow transitions
        """
        if self.context.configuration["workflowDisabled"]:
            return ""
        wfinfo = self.context.wf.GetWfInfo(self.User())
        if not wfinfo or not wfinfo["wf"] or len(wfinfo["wf"]["transitions"])==0:
            return ""

        l = []
        redirect = self.GetFormValue('url')
        if not redirect:
            redirect = self.request.URL
        for t in wfinfo["transitions"]:
            l.apend("""<option value="%s">%s</option>""" % (t['applications'][0], t["name"]))
        html = """
<div class="unit_options_block">
<form id="unit_options_transition" name="transition" action="wf" method="post">
 %(param)s
 <select name="action" onChange="submitdd(this)">
  <option>Status setzen...</option>
  %(options)s
 </select>
</form>
</div>
        """ % {"param": self.FmtFormParam(url=redirect), "options": "".join(l)}
        return html


    def shortcut_tools(self):
        """
        drop down with all possible context tools
        """
        tools = self.context.app.configurationQuery.GetAllToolConfs(self.context)
        if not tools:
            return ""
        redirect = self.GetFormValue("url")
        if not redirect:
            redirect = self.request.URL
        l = []
        for t in tools:
            l.append("""<option value="%s">%s</option>""" % (t["id"], t["name"]))
        html = """
<div class="unit_options_block">
<form id="unit_options_tool" action="tool" method="post">
 %(param)s
 <select name="tool" onChange="submitdd(this)">
  <option value="">Zusatzfunktionen...</option>
  %(tools)s
 </select>
</form>
</div>
        """ % {"param": self.FmtFormParam(redirect_url=redirect), "tools": "".join(l)}
        return html


    def shortcut_duplicate(self):
        """
        in place duplicate button
        """
        param = self.FmtURLParam(ids=self.context.id)
        l = """<a href="duplicate?%(param)s"><img src="%(static)simages/duplicate.png" alt="Duplizieren" align="top" /> </a>""" % {"param": param, "static": self.static}
        return """<div class="unit_options_block">%s</div>""" % (l)


    def shortcut_delete(self):
        """
        object delete button
        """
        if not self.Allowed("iface_delete", self.context):
            return ""
        p = self.FmtURLParam(ids=self.context.id)
        l = """<a href="../delete?%(param)s"><img src="%(static)simages/delete.png" alt="L&ouml;schen" align="top" /> </a>""" % {"param": p, "static": self.static}
        return """<div class="unit_options_block_del">%s</div>""" % (l)


