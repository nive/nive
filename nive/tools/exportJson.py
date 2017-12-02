# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import json
import base64

from nive.tool import Tool, ToolView
from nive.definitions import ToolConf, FieldConf, ViewConf
from nive.definitions import IApplication, MetaTbl, Structure, IContainer
from nive.helper import ConfEncoder
from nive.i18n import _

configuration = ToolConf(
    id = "exportJson",
    context = "nive.tools.exportJson.exportJson",
    name = _(u"Json data export"),
    description = _("This function exports all objects in json format. Optionally as flat list or tree structure. This is not a simple database table dump. Object events will be triggered before exporting data."),
    apply = (IApplication,),
    mimetype = "text/json",
    data = [
        FieldConf(id="tree", 
                  datatype="bool", 
                  default=1, 
                  listItems=[{"id":"true", "name":"Tree"},{"id":"false","name":"Flat list"}], 
                  name=_(u"Export as tree"),
                  description=_(u"Export objects as tree structure (contained objects are included as 'items')")),
        FieldConf(id="filedata", 
                  datatype="radio", 
                  default="none", 
                  listItems=[{"id":"none", "name":"Only file information (No file data)"},
                             {"id":"path", "name":"Only file information and local paths (No file data)"},
                             {"id":"data", "name":"Include all file data"},], 
                  name=_(u"File data"),
                  description=_(u"Include binary file data in json export (encoded as base64)"))
    ],
    views = [
        ViewConf(name="", view=ToolView, attr="run", permission="system", context="nive.tools.exportJson.exportJson"),
    ]
)

class exportJson(Tool):
    """
    """

    def _Run(self, **values):

        result = 1
        codepage="utf-8"
    
        app = self.app
        datapool = app.db
        conf = app.dbConfiguration
        conn = datapool.connection
        tree = values.get("tree")
        filedata = values.get("filedata")
        self.filename = app.configuration.id + ".json"

        if not conn:
            self.stream.write(_(u"Database connection error (${name})\n", mapping={u"name": app.dbConfiguration.context}))
            return 0
        
        if not conn.IsConnected():
            self.stream.write(_(u"Database connection error (${name})\n", mapping={u"name": app.dbConfiguration.context}))
            return 0
        
        def mapfields(fields):
            return [f.id for f in fields]
        
        metaflds = mapfields(app.GetAllMetaFlds(ignoreSystem=False))

        def exportObj(o):
            values = {"__items__": []}
            for field in metaflds:
                values[field] = o.meta.get(field)
            for field in o.configuration.data:
                if field["datatype"] == "file":
                    file = o.files.get(field.id)
                    if not file:
                        continue
                    values[field.id] = {"filename": file.filename, "size": file.size}
                    if filedata=="path":
                        values[field.id]["path"] = file.path
                    elif filedata=="data":
                        values[field.id]["data"] = base64.b64encode(file.read())
                else:
                    values[field.id] = o.data.get(field.id)
            
            if IContainer.providedBy(o):
                for child in o.GetObjs():
                    cv = exportObj(child)
                    values["__items__"].append(cv)
            return values
                
        root = app.root()
        data = {"__items__": []}
        for child in root.GetObjs():
            cv = exportObj(child)
            data["__items__"].append(cv)
            
        if not tree:
            def getlist(values, datalist):
                for v in values["__items__"]:
                    datalist = getlist(v, datalist)
                del values["__items__"]
                datalist.append(values)
                return datalist
            data = getlist(data, [])
            
        self.stream.write(ConfEncoder().encode(data))
        
        return 1

