


from nive.components.reform.forms import HTMLForm
from nive.definitions import IFieldConf
from nive.definitions import ConfigurationError
from nive.definitions import Conf 

from nive import helper

from nive.i18n import _, translate, TranslationString


class Search:
    """
    Search form and list renderer for interface views
    
    usage ::

        self.table(searchconf)
        or
        self.search(searchconf)
        or
        self.result(searchconf)
    """
    
    # search function ----------------------------------------------------------------------
    
    def result(self, searchconf=None, user=None):
        """
        main search function to be called from templates. if searchconf is none
        values are extracted from self.ifaceConf configuration object.
        
        returns the search dictionary and no rendered html. Use ``self.table()`` or ``self.search()``
        to generate html and forms.
        
        request based search parameters are "start, max, sort, ascending" for user sorts and paged results
        """
        if not hasattr(searchconf, "has_key"):
            n=searchconf
            searchconf = self.GetSearchConf(searchconf, self.context)
            if not searchconf:
                raise ConfigurationError("No search definition found ('%s')" % (n))
        fldsList = searchconf["fields"]
        searchFlds = searchconf["form"]
        
        #search form
        if searchFlds:
            tmp = []
            for f in searchFlds:
                tmp.append(f.copy(readonly=False, required=False))
            searchFlds = tmp
            form = HTMLForm(view=self, user=user, autofill="off")
            form.method = searchconf.get("method")
            form.fields = tmp
            form.widget.item_template = "field_onecolumn"
            form.actions = [Conf(id="search", method="Search", name=translate(_("Filter"), self.request), hidden=False)]
            form.Setup()
            result, parameter = form.Extract(self.request, removeNull=True, removeEmpty=True)
        else:
            form = None
            parameter = dict()
        operators = searchconf.get("operators", {"pool_type":"="})
        qr = searchconf.get("queryRestraints")
        if searchconf.get("container"):
            parameter["pool_unitref"] = self.context.id

        # callback
        cb = searchconf.get("callback")
        if cb is not None:
            qr, parameter, operators, searchFlds = cb(view=self, qr=qr, parameter=parameter, operators=operators,
                                                      searchFlds=searchFlds, searchconf=searchconf)

        if qr:
            for p in qr:
                ok = 0
                if p in parameter:
                    if isinstance(qr[p], (list,tuple)):
                        if parameter[p] in qr[p]:
                            ok = 1
                if not ok:
                    parameter[p] = qr[p]
        sdict = self.getSearchDict(searchconf)

        options = searchconf.get("options") or {}

        root = self.context.root
        # preload list flds
        for fld in fldsList:
            if fld.datatype in ("list", "radio", "multilist", "checkbox"):
                if not fld.listItems:
                    v = helper.LoadListItems(fld, app=self.context.app, obj=self.context)
                    fld.listItems = v
                        
        if not searchconf.get("type") or options.get("dataTable"):
            # if type is not explicitly named or data table is explicitly set call Search()
            items = root.search.Search(parameter,
                                fields=fldsList if "id" in fldsList else fldsList+["id"],
                                sort=sdict["sort"],
                                start=sdict["start"],
                                max=sdict["max"],
                                ascending=sdict["ascending"],
                                operators=operators,
                                static=self.static,
                                **options)
        else:
            items = root.search.SearchType(searchconf["type"],
                                    parameter,
                                    fields=fldsList + ["pool_filename", "id"],
                                    sort=sdict["sort"],
                                    start=sdict["start"],
                                    max=sdict["max"],
                                    ascending=sdict["ascending"] ,
                                    operators=operators,
                                    static=self.static,
                                    **options)
        return items, fldsList, searchFlds, form, searchconf, sdict
    

    # listing ------------------------------------------------
    
    def listing(self, searchconf=None):
        """
        simple result list rendering. Renders linked two line blocks for each result.
        """
        items, fldsList, searchFlds, form, searchconf, sdict = self.result(searchconf)
        rowtmpl = searchconf.get("rowtmpl")
        return self.listRows(items, fldsList, link=True, rowtmpl=rowtmpl)
        
        
    # listing parts ------------------------------------------------

    def listRows(self, items, fldsList, link=False, rowtmpl=None):
        """
        generate table row html
        """
        if link:
            l = """onclick="location.href='open?id=%(id)d'" style="cursor:pointer" """
        else:
            l = ""
        if not rowtmpl:
            rowtmpl = """<div class="well alert alert-light" %(link)s><h4>%(title)s</h4><div>%(subheader)s</div></div>"""
            rowtmpl = rowtmpl % {
                          "link":l,
                          "header": "%(title)s",
                          "subheader": "%(pool_type)s (%(id)d)"
            }
        body = []
        for i in items["items"]:
            body.append(rowtmpl % i)
        return "".join(body)
            
            
    # table ------------------------------------------------
    
    def table(self, searchconf=None, styling="table-bordered", urlTmpl="location.href='open?id=%(id)d'"):
        """
        simple result table rendering
        
        styling: table-bordered, table-striped, table-condensed
        """
        items, fldsList, searchFlds, form, searchconf, sdict = self.result(searchconf)
        return """
        <table id="tableList" class="table %s">
        %s 
        %s
        </table>
        """ % (styling, self.tableHeader(fldsList), self.tableRows(items, fldsList, searchconf, link=True, urlTmpl=urlTmpl))
        
        
    # table parts ------------------------------------------------

    def tableHeader(self, fldsList):
        """
        list header row including titles and sort
        """
        header = """<tr>%s</tr>"""        
        fldTmpl = """<th>%s</th> """ 
        flds = []
        for fld in fldsList:
            flds.append(fldTmpl % translate(fld.name, self.request))
        return header % "".join(flds)
    
    
    def tableRows(self, items, fldsList, searchconf, link=False, urlTmpl=""):
        """
        generate table row html
        """
        row = """<tr>%(value)s</tr>"""
        if link:
            urlTmpl = self.ToUrl(urlTmpl)
            row = "".join(["""<tr class="listRow" onclick=\"""", urlTmpl, """\">%(value)s</tr>"""])
        fld = """<td>%s</td>"""
        
        body = []
        for i in items["items"]:
            html = []
            for f in fldsList:
                id = f.id
                data = i[id]
                if hasattr(searchconf, "renderer") and hasattr(searchconf.renderer, id):
                    data = searchconf.renderer.get(id)(field=f, value=data, context=self, data=i)
                html.append(fld %(data))
            i["value"] = "".join(html)
            body.append(row % i)
        return "".join(body)
            
            
    # search ----------------------------------------------
    
    def search(self, searchconf="default", styling="table table-striped", urlTmpl=None, showMessages=True, user=None):
        """
        main search function to be called from templates. if searchconf is none
        values are extracted from self.ifaceConf configuration object.
        
        request based search parameters are "start, max, sort, ascending" for user sorts and paged results
        """
        items, fldsList, searchFlds, form, searchconf, sdict = self.result(searchconf, user=user)
        urlTmpl = urlTmpl or searchconf.get("urlTmpl") or "location.href='open?id=%(id)d'"
        return self.searchBody(form, items, searchconf.get("type"), fldsList, searchFlds, sdict, searchconf, styling, urlTmpl, showMessages)

    
    # search html parts ----------------------------------------------

    def searchBody(self, form, items, searchType, fldsList, searchFlds, sdict, searchconf, styling, urlTmpl, showMessages):
        """
        renders search form and list. 
        calls all included parts: header, rows, pageUrls and listoptions.
        """
        urls = self.pageurls(items)
        action = ""
        formhtml = ""
        messages = ""
        box = ""
        if len(searchFlds):
            #formhtml = form.RenderBody(items["criteria"])
            fl = []
            form.Setup()
            #result, formvalues = form.Extract(self.request, removeNull=True, removeEmpty=True)
            for f in searchFlds:
                if f.datatype=="file":
                    fl.append("<th></th>")
                    continue
                form2 = HTMLForm(loadFromType=form.loadFromType, view=self, autofill="off")
                form2.actions = []
                form2.fields = [f]
                form2.widget.item_template = "field_nolabel"
                form2.Setup()
                form2._c_fields[0].settings["css_class"] = "form-control form-control-sm"
                fl.append("<th>"+form2.RenderBody(items["criteria"], msgs=None, errors=None, result=None)+"</th>")

            formhtml = """
            <tr>
              %(fields)s
              <th><button class="btn btn-sm btn-light"><img src="%(static)simages/icon_reload.svg" alt="Liste aktualisieren" title="Liste aktualisieren"></button></th>
            </tr>
            """ % dict(fields=" ".join(fl), static=self.static)

        if showMessages:
            messages = self.messages()
        shortcuts = ""
        options = ""
        if searchconf.get("folder"):
            shortcuts = self.shortcuts()
        options = self.listoptions(searchconf)
        header = self.header2(fldsList=fldsList, pool_type=searchType, addSort=True, searchconf=searchconf)
        rows = self.rows(recs=items.get('items'), fldsList=fldsList, obj=self.context,
                         checkbox=searchconf.get("listoptions"),
                         urlTmpl=urlTmpl,
                         linkCell=searchconf.get("linkcell") or True,
                         searchconf=searchconf)

        if formhtml:
            formhtml = """<tr> %(form)s </tr>""" % {"form":formhtml}

        html = """
<form action="%(action)s" id="boxSearch" name="searchForm" method="post" enctype="multipart/form-data" class="search">
 %(messages)s
 %(urls)s
 %(shortcuts)s
 
  <input type="hidden" name="start" value="%(start)d">
  <input type="hidden" name="sort" value="%(sort)s">
  <input type="hidden" name="ascending" value="%(ascending)s">
  <input type="hidden" name="ref" value="%(ref)s">

  <table class="%(styling)s list">
   <thead>%(header)s</thead>
   <tbody>
     %(formhtml)s
     %(rows)s
   <tbody>   
  </table>
 %(urls)s
 %(options)s
</form>
        """ % {"action":action, "formhtml":formhtml, "messages": messages, "shortcuts": shortcuts,
               "urls":urls, "options": options, "header": header, "rows":rows, "static": self.static,
               "start": 0, "sort": sdict["sort"], "ascending": sdict["ascending"],
               "styling": styling, "ref": self.CurrentUrl(preserveHost=False)}  # "header": form.HTMLHead()  #sdict["start"]
        return html


    def header(self, fldsList,pool_type,addSort=True):
        """
        list header row including titles and sort
        """
        raise TypeError("removed!")


    def header2(self, fldsList,pool_type,addSort=True,searchconf=None):
        """
        list header row including titles and sort

                    <th tal:repeat="fld fields">
                        <a tal:content="fld.name" id="sort-${fld.id}" class="sort" data-value="${fld.id}" href="#"></a>
                    </th>
                    <th></th>

        """
        app = self.context.app
        fldTmpl = """<th class="list_header" id="list_%s" nowrap>%s</th> """
        #up = translate(_("Sort ascending"), self.request)
        #down = translate(_("Sort descending"), self.request)
        sortTmpl = """<a id="sort-%(id)s" class="sort" data-value="%(id)s" href="#">%(name)s</a>"""

        flds = []
        for fld in fldsList:
            sort = ""
            if IFieldConf.providedBy(fld):
                name = translate(fld["name"], self.request)
                fldid = fld.get("settings",{}).get("sort_id", fld["id"])
                sort = sortTmpl % dict(id=fld["id"], name=translate(fld["name"], self.request))
            else:
                if addSort and fld[0]!="+":
                    sort = sortTmpl % (fld, fld)
                if fld=="+folderpath":
                    name = translate(_("Folder"), self.request)
                else:
                    # ! iface2 update
                    name = translate(app.configurationQuery.GetFldName(fld, pool_type), self.request)
                fldid = fld
            flds.append(fldTmpl % (fldid, sort))
        
        html = """
        <tr>
        %s
        <th></th>
        </tr>
        """ % ("".join(flds))
        return html    

    
    def rows(self,recs,fldsList,obj=None,
             view=0,edit=0,duplicate=0,commit=0,reject=0,checkbox=1,ov=0,select=0,
             urlTmpl=None,linkCell=True,searchconf=None):
        """
        list row and field rendering
        """
        wfa_icon = 1
        type_icon = 0
        xOffset = "4"
        yOffset = "4"
        targetId = "list_ov"
        cache = dict()

        html = []
        app = self.context.app
        
        if ov:
            unit_ov_url = "ov"

        # show 1. column only for "pool_wfa","pool_state"
        show = 0
        if IFieldConf.providedBy(fldsList[0]):
            if fldsList[0]["id"] in ("pool_wfa","pool_state"):
                show = 1
        else:
            if fldsList[0] in ("pool_wfa","pool_state"):
                show = 1
        
        urlTmpl = self.ToUrl(urlTmpl)

        # loop result
        cnt = 0
        for row in recs:
            cnt = cnt + 1
            id = row["id"]
            vUrl = self.FmtURLParam(id=id)
            url = urlTmpl%(row)
            html.append("""<tr class="listRow listRow%s" id="row%d">""" % (str((cnt % 2) +1), id))
        
            rowStr = []
            rowIsLinked = False
            linkCnt = 0
        
            # buttons
            if show and (view or edit or duplicate or commit or reject or ov):
                rowStr.append("""<td class="listOptions" nowrap>""")
                if view:       rowStr.append("""<a href="open?%s" class="text"><img src="%(static)simages/docs.gif" border="0" align="top" title="View" /></a> """ % (vUrl, self.static))
                if edit:       rowStr.append("""<a href="open?%s" class="text"><img src="%(static)simages/edit.gif" border="0" align="top" title="Edit" /></a> """ % (app.GetURLParam(id, url='e'), self.static))
                if duplicate:  rowStr.append("""<a href="open?%s" class="text"><img src="%(static)simages/duplicate.gif" border="0" align="top" title="Duplicate" /></a> """ % (app.GetURLParam(id, url='d'), self.static))
                if commit:     rowStr.append("""<a href="wfcall?%s" class="text"><img src="%(static)simages/commit.gif" border="0" align="top" title="Commit" /></a> """ % (app.GetURLParam(id, action='commit', trans='commit'), self.static))
                if reject:     rowStr.append("""<a href="wfcall?%s" class="text"><img src="%(static)simages/reject.gif" border="0" align="top" title="Reject" /></a> """ % (app.GetURLParam(id, action='reject', trans='reject'), self.static))
                if ov:
                    t = row.get("pool_wfa")
                    if not t:
                        data = """<img src="%simages/state%d.gif" title="State" />""" % (self.static, row.get('pool_state',1))
                        skipState=1
                    else:
                        ckey = "pool_wfa"+t
                        if ckey in cache:
                            data = cache[ckey]
                        else:
                            data = t # app.GetWfActivityName(t) # TODO lookup name
                            cache[ckey] = data
                        data = """<img src="%(static)simages/wf%s.gif" title="%s" border="0" />""" % (self.static, t, data)
                    target = targetId # + str(id)
                    url = "%s?%s&el=%s" % (unit_ov_url, self.FmtURLParam(id=id), target)
                    urlOv = "loadOvM(event, '%s', '%s', %s, %s, 'left')    " % (url, target, xOffset, yOffset)
                    rowStr.append("""<a onMouseDown="%s" class="text">%s</a>""" % (urlOv, data))
                rowStr.append("""</td>""")
        
            # flds
            for fld in fldsList:
                data = ""
                fldid = fld.id
                
                # load custom renderer fld
                if hasattr(searchconf, "renderer") and hasattr(searchconf.renderer, fldid):
                    data = searchconf.renderer.get(fldid)(field=fld, value=row.get(fldid), context=self, data=row)
        
                elif fldid == "pool_type":
                    t = row.get("pool_type")
                    ckey = "pool_type"+t
                    if ckey in cache:
                        data = cache[ckey]
                    else:
                        try:
                            data = translate(app.configurationQuery.GetObjectConf(t).get("name", t), self.request)
                        except AttributeError:
                            data = t + " ???"
                        cache[ckey] = data
                    if type_icon:
                        data = """<img src="%simages/types/%s.png" title="%s" />""" % (self.static, t, data)
                    if not select:
                        #data = """<a href="open?%s" class="text">%s</a>""" % (vUrl, data)
                        if not type_icon:
                            linkCnt = linkCnt + 1
        
                elif fldid == "pool_wfa":
                    if show and ov:
                        continue
                    t = row.get("pool_wfa")
                    data = t
                    if t:
                        ckey = "pool_wfa"+t
                        if ckey in cache:
                            data = cache[ckey]
                        elif fld.get("listItems"):
                            for f in fld["listItems"]:
                                if f["id"]==t:
                                    data = f["name"]
                                    cache[ckey] = data
                        else:
                            data = app.GetWfActivityName(t) # TODO lookup name
                            cache[ckey] = data
                        if wfa_icon:
                            data = """<img src="%simages/wf%s.gif" title="%s" />""" % (self.static, t, data)
        
                elif fldid == "pool_state":
                    if show and ov and skipState:
                        continue
                    data = """<img src="%simages/state%d.gif" title="State" />""" % (self.static, row.get('pool_state'))

                elif fld.datatype in ("list", "radio"):
                    data = row.get(fldid)
                    cached = cache.get(fldid)
                    if cached is None:
                        cached = helper.LoadListItems(fld, app=app, obj=obj)
                        cache[fld.id] = cached
                    for i in cached:
                        if i["id"]==str(data):
                            data = translate(i["name"], self.request)
                            break

                elif fld.datatype in ("multilist", "checkbox"):
                    data = row.get(fldid)
                    names = []
                    cached = cache.get(fldid)
                    if cached is None:
                        cached = helper.LoadListItems(fld, app=app, obj=obj)
                        cache[fld.id] = cached
                    for value in data:
                        for i in cached:
                            if i["id"]==value:
                                names.append(translate(i["name"], self.request))
                                break
                    if names:
                        data = ", ".join(names)

                elif fld.datatype in ("unit",):
                    data = row.get(fldid)
                    cached = cache.get(fldid)
                    if cached is None:
                        cached = helper.LoadListItems(fld, app=app, obj=obj)
                        cache[fld.id] = cached
                    for i in cached:
                        if i["id"]==str(data):
                            data = i["name"]
                            break

                else:
                    data = row.get(fldid)

                if linkCell==True or (isinstance(linkCell, (list,tuple)) and fldid in linkCell):
                    rowStr.append("""<td onclick="%s" class="pointer">%s</td>""" % (url, data))
                else:
                    rowStr.append("""<td>%s</td>""" % (data))

            if checkbox:
                rowStr.append("""<td class="listAction" align="right"><input value="%s" type="checkbox" name="ids" /></td>""" % (id))
            else:
                rowStr.append("""<td class="listAction" align="right"></td>""")
            rowStr.append("</tr>")
            html.append("".join(rowStr))
        
        if len(recs) == 0:
            html.append("""<tr class="listRow"><td></td><td colspan="%d"><br/><i>%s</i><br/><br/></td></tr>""" % (len(fldsList), translate(_("Empty result set!"), self.request)))
        
        return "".join(html)    


    
    def pageurls(self, items):
        """
        if paged result the previous, next and set links
        """
        if items.get('total', 0) == 0:
            return ""
        
        # pages
        start = items.get("start")
        maxPage = items.get("max")
        total = items.get("total")
        pageCount = int(total / maxPage) + (total % maxPage != 0)
        pageHtml = ""
        
        if total <= maxPage:
            cnt = translate(_("${total} of ${total}", mapping={'total': items.get('total')}))
            return """<div class="paging"><div>%s</div></div>""" % (cnt)

        cnt = translate(_("${start} to ${count} of ${total}", mapping={"start":items.get('start')+1, "count":items.get('start')+items.get('count'), 'total': items.get('total')}))
        prev = """<a class="search_start" data-value="%d">&laquo;</a>""" % (items.get("prev"))
        next = """<a class="search_start" data-value="%d">&raquo;</a>""" % (items.get("next"))
        pageTmpl = """ <a class="search_start" data-value="%d">%s</a> """
        pageTmpl1 = """ [%s] """
        
        if items.get("start")==0:
            prev = "&laquo;"
        if items.get("next")==0:
            next = "&raquo;"
        
        if pageCount > 1:
            current = int(start / maxPage)
            count = 10
            pages = [0]
            first = current - int(count / 2) + 1
            if first < 1:
                first = 1
            elif pageCount < count:
                first = 1
                count = pageCount
            elif first + count > pageCount - 1:
                first = pageCount - count
            for i in range(count - 1):
                p = first + i
                if p == pageCount - 1:
                    break
                pages.append(p)
            pages.append(pageCount - 1)
        
            # loop pages
            for i in pages:
                # check curent page
                if start >= maxPage * i and start <= maxPage * i:
                    pageHtml = pageHtml + pageTmpl1 % (str(i + 1))
                else:
                    pageHtml = pageHtml + pageTmpl % (maxPage * i, str(i + 1))
        else:
            prev = ""
            next = ""
        
        html = """<div class="paging"><div>%s %s %s %s</div></div>""" % (cnt, prev, pageHtml, next)
        return html    


    def listoptions(self, searchconf):
        """
        list options for action checkbox
        """
        if not searchconf.get("listoptions"):
            return ""
        ccp = delete = ""

        if searchconf.get("container") and "ccp" in searchconf.get("listoptions", []):
            ccp = """
 <input type="image" src="%(static)simages/copy.png" name="copy" id="copy" class="btn btn-sm btn-light" title="%(Copy)s" />
 <input type="image" src="%(static)simages/cut.png" name="cut" id="cut" class="btn btn-sm btn-light" title="%(Cut)s" />
 <input type="image" src="%(static)simages/paste.png" name="paste" id="paste" class="btn btn-sm btn-light" title="%(Paste)s" />
        """ % {"static": self.static,
               "Copy": translate(_("Copy"), self.request),
               "Cut": translate(_("Cut"), self.request),
               "Paste": translate(_("Paste"), self.request)}

        if "delete" in searchconf.get("listoptions",[]):
            delete = """<input type="submit" name="delete" id="delete" value="%(Delete)s" class="btn btn-sm btn-light" i18n:attributes="value">""" % \
                     {"static": self.static,
                      "Delete": translate(_("Delete selected"), self.request)}

        html = """
<div id="listActionButtons">
 %(ccp)s &nbsp;
 %(delete)s &nbsp;
 <button type="button" name="selectButton" id="selectButton" class="btn btn-sm btn-light">%(Select all)s</button>
</div>
        """ % {"static": self.static, "ccp": ccp, "delete": delete, "base":self.FolderUrl(),
               "Select all": translate(_("Select all"), self.request)}
        return html


    def getSearchDict(self, searchconf):
        """
        extracts search parameters from request
        start, max, sort, ascending
        """
        d = {"start": int(self.GetFormValue('start',0) or 0),
             "max": int(self.GetFormValue('max',searchconf.get("max",30))), 
             "sort": self.GetFormValue('sort',searchconf.get("sort",'title')), 
             "ascending": self.GetFormValue('ascending',searchconf.get('ascending',True)) in ("True", "true", "1", 1, True)}
        return d

