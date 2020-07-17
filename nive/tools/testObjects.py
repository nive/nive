
from nive.tool import Tool, ToolView
from nive.definitions import ToolConf, ViewConf, FieldConf
from nive.definitions import IApplication
from nive.i18n import _

configuration = ToolConf(
    id = "testobjects",
    context = "nive.tools.testObjects.testobjects",
    name = "Test load all objects",
    description = "tests tree structure and obj data",
    apply = (IApplication,),
    mimetype = "text/html",
    data = [
        FieldConf(id="repair", datatype="number", default="", name="Repair parents -> move to id", description=""),
        FieldConf(id="delete", datatype="list", default="0",  name="Delete if non existing data table id",
                  listItems=[dict(id="1",name="Yes"),
                             dict(id="0",name="No")],
                  description=""),
        FieldConf(id="tag", datatype="string", default="testobjects", hidden=1)
    ],
    views = [
        ViewConf(name="", view=ToolView, attr="form", permission="admin", context="nive.tools.testObjects.testobjects")
    ]
)

class testobjects(Tool):
    """
    """

    def _Run(self, **values):

        self.InitStream()

        delete = values.get("delete")=="1"
        repair = values.get("repair")
        if repair:
            repair = int(repair)
        else:
            repair = None

        app = self.app
        root = app.root
        datapool = app.db
        conn = datapool.connection

        if not conn:
            self.stream.write(_(u"Database connection error (${name})\n", mapping={u"name": app.dbConfiguration.context}))
            return self.stream, ""
        
        if not conn.IsConnected():
            self.stream.write(_(u"Database connection error (${name})\n", mapping={u"name": app.dbConfiguration.context}))
            return self.stream, ""

        # load all pool_files
        sql="select id, pool_type, title, pool_unitref, pool_dataref, pool_datatbl from pool_meta"
        cc = conn.cursor()
        cc.execute(sql)
        # loop
        c=e=o=0
        for rec in cc.fetchall():
            c+=1
            try:
                obj = root.LookupObj(rec[0])
                if obj is None:
                    sql = "select id from %s where id=%s"%(rec[5], rec[4])
                    cc.execute(sql)
                    test = cc.fetchall()
                    if not test:
                        self.stream.write("OBJ ERR: #%d (in %d) - %s - %s -> data table entry missing: %s<br>"%(rec[0], rec[3], rec[1], rec[2] or '~', sql))
                        if delete:
                            sql = "delete from pool_meta where id=%s"
                            cc.execute(sql, (rec[0],))
                        else:
                            e += 1
                    elif root.LookupObj(rec[3]) is None:
                        self.stream.write("OBJ ERR: #%d (in %d) - %s - %s -> parent missing: %d<br>" % (rec[0], rec[3], rec[1], rec[2] or '~', rec[3]))
                        if repair is not None:
                            sql = "update pool_meta set pool_unitref=%s where id=%s"
                            cc.execute(sql, (repair, rec[0]))
                        else:
                            e += 1
            except Exception as excp:
                self.stream.write("OBJ EXCP: #%d (in %d) - %s - %s -> %s<br>"%(rec[0], rec[3], rec[1], rec[2] or '~', str(excp)))
                e+=1
                #raise
                continue
            o+=1
        self.stream.write("Done. %d total, %d ok, %d errors <br>"%(c,o,e))

        return self.stream, True

