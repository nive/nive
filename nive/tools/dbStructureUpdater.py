# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive.tool import Tool, ToolView
from nive.definitions import ToolConf, ViewConf, FieldConf, IApplication, Structure, MetaTbl

from nive.i18n import _
from nive.helper import FakeLocalizer
from nive.utils.dataPool2.base import OperationalError

from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request

   
   
configuration = ToolConf(
    id = "dbStructureUpdater",
    context = "nive.tools.dbStructureUpdater.dbStructureUpdater",
    name = _("Database Structure"),
    description = _("Generate or update the database structure based on configuration settings."),
    apply = (IApplication,),
    mimetype = "text/html",
    data = [
        FieldConf(id="modify",     datatype="bool", default=0, name=_("Modify existing columns"),  description=_("Change existing database columns to new configuration. Depending on the changes, data may be lost!")),
        FieldConf(id="showSystem", datatype="bool", default=0, name=_("Show system columns"),      description=""),
    ],
    views = [
        ViewConf(name="", view=ToolView, attr="run", permission="system", context="nive.tools.dbStructureUpdater.dbStructureUpdater")
    ]
)

class dbStructureUpdater(Tool):

    def _Run(self, **values):

        result = 1
        importWf = 1
        importSecurity = 0
        showSystem = values.get("showSystem")
        modify = values.get("modify")
        request = values["original"]
        ignoreTables = self.app.configuration.get("skipUpdateTables", ())
        self.InitStream()

        try:
            localizer = get_localizer(get_current_request())
        except:
            localizer = FakeLocalizer()
        #localizer.translate(term) 

        text = _(""" <div class="well">
This tool compares the physically existing database structure (tables, columns) with the current configuration settings.
The database structure is shown on the left, configuration settings on the right. <br><br>
Existing database columns will only be altered if manually selected in the 'Modify' column. Modifying a table may destroy the data
stored (e.g if converted from string to integer), so don't forget to create backups of the database before modifying anything.<br>
By default this tool will only create new tables and columns and never delete any column.
 </div>       """)
        self.stream.write(localizer.translate(_(text)))

        self.stream.write("""<form action="" method="post">
                     <input type="hidden" name="tag" value="dbStructureUpdater">
                     <input type="hidden" name="modify" value="1">""")
        app = self.app
        try:
            conf = app.dbConfiguration
            connection = app.NewConnection()
            if not connection:
                self.stream.write(localizer.translate(_("""<div class="alert alert-error">No database connection configured</div>""")))
                return None, 0
        except OperationalError as e:
            self.stream.write(localizer.translate(_("""<div class="alert alert-error">No database connection configured</div>""")))
            return None, 0

        db = connection.GetDBManager()
        self.stream.write(localizer.translate(_("<h4>Database '${name}' ${host} </h4><br>", mapping={"host":conf.host, "name":conf.dbName})))

        if not db:
            self.stream.write(localizer.translate(_("<div class='alert alert-error'>Database connection error (${name})</div>", mapping={"name": app.dbConfiguration.context})))
            return None, 0
        
        # check database exists
        if not db.IsDatabase(conf.get("dbName")):
            db.CreateDatabase(conf.get("dbName"))
            self.stream.write("")
            self.stream.write("")
            self.stream.write(localizer.translate(_("<div class='alert alert-success'>Database created: '${name}'</div>", mapping={"name": conf.dbName})))
            db.dbConn.commit()
        db.UseDatabase(conf.get("dbName"))

        # check types for data tables -------------------------------------------------------------
        aTypes = app.configurationQuery.GetAllObjectConfs()
        
        for aT in aTypes:
            fmt = aT["data"]
            if(fmt == []):
                continue

            if aT["dbparam"] in ignoreTables:
                continue

            m = None
            if modify:
                m = request.get(aT["dbparam"])
                if isinstance(m, str):
                    m = [m]
            if not db.UpdateStructure(aT["dbparam"], fmt, m):
                self.stream.write("")
                self.stream.write(localizer.translate(_("<div class='alert alert-error'>Table update failed: ${dbparam} (type: ${name})</div>", mapping=aT)))
                result = 0
                continue
            db.dbConn.commit()
                
            self.printStructure(db.GetColumns(aT["dbparam"], fmt), aT["dbparam"], fmt, db, localizer)

        # check meta table exists and update ---------------------------------------------------------------
        if not MetaTbl in ignoreTables:
            meta = app.configurationQuery.GetAllMetaFlds(ignoreSystem=False)
            tableName = MetaTbl

            if not db.IsTable(tableName):
                if not db.CreateTable(tableName, columns=meta):
                    self.stream.write(localizer.translate(_("<div class='alert alert-error'>Table creation failed (pool_meta)</div>")))
                    return None, 0
                db.dbConn.commit()

            # create and check modified fields
            m = None
            if modify:
                m = request.get(tableName)
                if isinstance(m, str):
                    m = [m]
            if not db.UpdateStructure(tableName, meta, m):
                self.stream.write(localizer.translate(_("<div class='alert alert-error'>Table update failed (pool_meta)</div>")))
                result = 0
            db.dbConn.commit()

            self.printStructure(db.GetColumns(tableName, meta), tableName, meta, db, localizer)


        # check structure tables exist and update ------------------------------------------------------------
        for table in list(Structure.items()):
            if table[0] in ignoreTables:
                continue

            tableName = table[0]
            fields = table[1]["fields"]
            identity = table[1]["identity"]
            if not db.IsTable(tableName):
                if not db.CreateTable(tableName, columns=fields, createIdentity = bool(identity), primaryKeyName = identity):
                    self.stream.write(localizer.translate(_("<div class='alert alert-error'>Table creation failed (${name})</div>",mapping={"name":tableName})))
                    return None, 0
                db.dbConn.commit()
        
            # create and check modified fields
            m = None
            if modify:
                m = request.get(tableName)
                if isinstance(m, str):
                    m = [m]
            if not db.UpdateStructure(tableName, fields, m, createIdentity = bool(identity)):
                self.stream.write(localizer.translate(_("<div class='alert alert-error'>Table creation failed (${name})</div>",mapping={"name":tableName})))
                result = 0
            db.dbConn.commit()

            if showSystem:
                self.printStructure(db.GetColumns(tableName, fields), tableName, fields, db, localizer)



        if db.modifyColumns:
            self.stream.write("""<div class="alert alert-error"><input class="btn btn-primary" type="submit" name="submit" value=" %s "><br>%s</div>""" % (
                localizer.translate(_("Modify selected columns")), 
                localizer.translate(_("Changes on existing columns have to be applied manually. This will write selected 'Configuration settings' to the database.<br> <b>Warning: This may destroy something!</b>"))))
        self.stream.write(localizer.translate("</form>"))
        connection.close()
        return None, result

    
    def printStructure(self, structure, table, fmt, db, localizer):
        header = """
<h4>%(Table)s: %(tablename)s</h4>
<table class="table"><tbody>
<tr><td colspan="5">%(Db Columns)s</td>                                        <td colspan="2">%(Configuration settings)s</td></tr>
<tr><td>%(ID)s</td><td>%(Type)s</td><td>%(Default)s</td><td>%(Settings)s</td>  <td>%(Modify?)s</td><td></td></tr>
"""  % {"tablename":table, 
        "Table": localizer.translate(_("Table")), 
        "Db Columns": localizer.translate(_("Database settings")), 
        "Configuration settings": localizer.translate(_("Configuration settings")),
        "ID":localizer.translate(_("ID")),
        "Type":localizer.translate(_("Type")),
        "Default":localizer.translate(_("Default")),
        "Settings":localizer.translate(_("Settings")),
        "Modify?":localizer.translate(_("Modify?"))
       }

        row = """
<tr><td>%(id)s</td><td>%(type)s</td><td>%(default)s</td><td>Not null: %(null)s, Identity: %(identity)s</td>        <td>%(Modify)s</td><td>%(Conf)s</td></tr>
"""

        cb = """
<input type="checkbox" name="%s" value="%s">""" 

        footer = """
</tbody></table> <br>"""


        self.stream.write(header)
        for col in structure:
            id = col
            col = structure[col].get("db")
            if not col:
                col = {"id":id, "type": "", "default": "", "null": "", "identity": ""}
            conf = ""
            for d in fmt:
                if col and d["id"].upper() == col["id"].upper():
                    conf = db.ConvertConfToColumnOptions(d)
                    break
            col["Modify"] = cb % (table, id)
            col["Conf"] = conf
            self.stream.write(row % col)

        self.stream.write(footer)

        return 
    
    
