# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#


from nive.tool import Tool, ToolView
from nive.definitions import ToolConf, FieldConf, ViewConf
from nive.definitions import IApplication, MetaTbl, Structure
from nive.i18n import _

configuration = ToolConf(
    id = "dbSqlDump",
    context = "nive.tools.dbSqlDump.dbSqlDump",
    name = _("Database sql dump"),
    description = _("This function dumps table contents as SQL INSERT statements. 'CREATE table' statements are not included."),
    apply = (IApplication,),
    mimetype = "text/sql"
)
configuration.data = [
    FieldConf(id="excludeSystem", 
              datatype="checkbox",
              default=[], 
              listItems=[{"id":"pool_sys", "name":"pool_sys"},{"id":"pool_fulltext","name":"pool_fulltext"}], 
              name=_("Exclude system columns"))
]
configuration.views = [
    ViewConf(name="", view=ToolView, attr="run", permission="system", context="nive.tools.dbSqlDump.dbSqlDump")
]


class dbSqlDump(Tool):
    """
    """

    def _Run(self, **values):

        result = 1
        codepage="utf-8"
    
        self.InitStream()
        app = self.app
        datapool = app.db
        conf = app.dbConfiguration
        conn = datapool.connection
        system = values.get("excludeSystem")
        self.filename = app.configuration.id + ".sql"

        if not conn:
            self.stream.write(_("Database connection error (${name})\n", mapping={"name": app.dbConfiguration.context}))
            return None, 0
        
        if not conn.IsConnected():
            self.stream.write(_("Database connection error (${name})\n", mapping={"name": app.dbConfiguration.context}))
            return None, 0
        
        def mapfields(fields):
            a=[]
            for f in fields:
                a.append(f.id)
            return a
        
        export = [(MetaTbl,mapfields(app.configurationQuery.GetAllMetaFlds(ignoreSystem=False)))]
        for t in app.configurationQuery.GetAllObjectConfs():
            export.append((t.dbparam, ["id"]+mapfields(t.data)))
        for t in list(Structure.items()):
            export.append((t[0], mapfields(t[1]["fields"])))

        for table in export:
            #tablename
            tablename=table[0]
            if system and tablename in system:
                continue 
            #fields
            fields=table[1]
            columns = ",".join(fields)
            sql="select %s from %s" % (columns, tablename)
            c = conn.cursor()
            c.execute(sql)
            for rec in c.fetchall():
                data = []
                for col in rec:

                    value = conn.FmtParam(col)
                    if isinstance(value, bytes):
                        value = value.decode('unicode_escape')
                    data.append(value)
                data = ",".join(data)
                if not isinstance(data, str):
                    data = str(data, codepage)
                value = "INSERT INTO %s (%s) VALUES (%s);\n"%(tablename, columns, data)
                #value = value.encode(codepage) # todo [3] unicode
                self.stream.write(value)        
        
        return None, 1

