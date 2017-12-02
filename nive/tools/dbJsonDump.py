# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import json
import datetime

from nive.tool import Tool, ToolView
from nive.definitions import ToolConf, FieldConf, ViewConf
from nive.definitions import IApplication, MetaTbl, Structure
from nive.helper import JsonDataEncoder
from nive.i18n import _

configuration = ToolConf(
    id = "dbJsonDump",
    context = "nive.tools.dbJsonDump.dbJsonDump",
    name = _(u"Database json dump"),
    description = _("This function dumps table contents the way records are stored in json format."),
    apply = (IApplication,),
    mimetype = "text/json",
    data = [
        FieldConf(id="excludeSystem", 
                  datatype="checkbox",
                  default=[], 
                  listItems=[{"id":"pool_sys", "name":"pool_sys"},{"id":"pool_fulltext","name":"pool_fulltext"}], 
                  name=_(u"Exclude system columns"))
    ],
    views = [
        ViewConf(name="", view=ToolView, attr="run", permission="system", context="nive.tools.dbJsonDump.dbJsonDump")
    ]
)

class dbJsonDump(Tool):
    """
    """

    def _Run(self, **values):

        result = 1
        codepage="utf-8"
    
        app = self.app
        datapool = app.db
        conf = app.dbConfiguration
        conn = datapool.connection
        system = values.get("excludeSystem")
        self.filename = app.configuration.id + ".json"

        if not conn:
            self.stream.write(_(u"Database connection error (${name})\n", mapping={u"name": app.dbConfiguration.context}))
            return 0
        
        if not conn.IsConnected():
            self.stream.write(_(u"Database connection error (${name})\n", mapping={u"name": app.dbConfiguration.context}))
            return 0
        
        def mapfields(fields):
            a=[]
            for f in fields:
                a.append(f.id)
            return a
        
        export = [(MetaTbl,mapfields(app.GetAllMetaFlds(ignoreSystem=False)))]
        for t in app.GetAllObjectConfs():
            export.append((t.dbparam, ["id"]+mapfields(t.data)))
        for t in Structure.items():
            export.append((t[0], mapfields(t[1]["fields"])))

        data = {}
        for table in export:
            #tablename
            tablename=table[0]
            if system and tablename in system:
                continue 
            #fields
            fields=table[1]
            columns = (",").join(fields)
            sql="select %s from %s" % (columns, tablename)
            c = conn.cursor()
            c.execute(sql)
            tvalues = []
            for rec in c.fetchall():
                recvalue = {}
                pos = 0
                for col in rec:
                    recvalue[fields[pos]] = col
                    pos+=1
                tvalues.append(recvalue)
            data[tablename] = tvalues
        
        self.stream.write(JsonDataEncoder().encode(data))        
        
        return 1

