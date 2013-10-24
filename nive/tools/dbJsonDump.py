# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import json

from nive.tool import Tool
from nive.definitions import ToolConf, FieldConf, IApplication, MetaTbl, Structure
from nive.i18n import _

configuration = ToolConf(
    id = "dbJsonDump",
    context = "nive.tools.dbJsonDump.dbJsonDump",
    name = _(u"Database json dump"),
    description = _("This function only dumps table contents the way records are stored."),
    apply = (IApplication,),
    mimetype = "text/json"
)

configuration.data = [
    FieldConf(id="excludeSystem", 
              datatype="mcheckboxes", 
              default=[], 
              listItems=[{"id":"pool_sys", "name":"pool_sys"},{"id":"pool_fulltext","name":"pool_fulltext"}], 
              name=_(u"Exclude system columns"))
]



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
            self.stream.write(_(u"Database connection error (${name})\n", mapping={u"name": app.poolTag}))
            return 0
        
        if not conn.IsConnected():
            self.stream.write(_(u"Database connection error (${name})\n", mapping={u"name": app.poolTag}))
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
        
        self.stream.write(json.dumps(data))        
        
        return 1

