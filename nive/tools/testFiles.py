
import os, stat

from nive.tool import Tool, ToolView
from nive.definitions import ToolConf, ViewConf, FieldConf
from nive.definitions import IApplication
from nive.i18n import _

configuration = ToolConf(
    id = "testfiles",
    context = "nive.tools.testFiles.testfiles",
    name = "Test load all files",
    description = "tests path, size, objid",
    apply = (IApplication,),
    mimetype = "text/html",
    data = [
        FieldConf(id="repair", datatype="list", default="0",  name="Repair size",
                  listItems=[dict(id="1",name="Yes"),
                             dict(id="0",name="No")],
                  description=""),
        FieldConf(id="delete", datatype="list", default="0",  name="Delete non existing objids files",
                  listItems=[dict(id="1",name="Yes"),
                             dict(id="0",name="No")],
                  description=""),
        FieldConf(id="defaultkey", datatype="string", default=""),
        FieldConf(id="tag", datatype="string", default="testfiles", hidden=1)
    ],
    views = [
        ViewConf(name="", view=ToolView, attr="form", permission="admin", context="nive.tools.testFiles.testfiles")
    ]
)

class testfiles(Tool):
    """
    """

    def _Run(self, **values):

        self.InitStream()

        delete = values.get("delete")=="1"
        repair = values.get("repair")=="1"
        defaultkey = values.get("defaultkey")

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
        sql="select id, fileid, filename, path, size, extension, filekey from pool_files"
        cc = conn.cursor()
        cc.execute(sql)
        # loop
        c=e=o=0
        for rec in cc.fetchall():
            c+=1
            try:
                obj = root.LookupObj(rec[0])
                if obj is None:
                    sql = "select id from pool_meta where id=%s"
                    cc.execute(sql, (rec[0],))
                    test = cc.fetchall()
                    if not test:
                        self.stream.write("OBJ ERR: #%d (for fileid %d) %s -> obj id not existing<br>" % (rec[0], rec[1], rec[2]))
                        if delete:
                            sql = "delete from pool_files where fileid=%s"
                            cc.execute(sql, (rec[1],))
                            #TODO delete file?
                        else:
                            e+=1
                    else:
                        self.stream.write("OBJ ERR: #%d (for fileid %d) %s -> obj load failed<br>" % (rec[0], rec[1], rec[2]))
                        e += 1
            except Exception as excp:
                self.stream.write("OBJ EXCP: #%d (for fileid %d) %s  -> %s<br>"%(rec[0], rec[1], rec[2], str(excp)))
                e+=1
                raise
            path = app.dbConfiguration.fileRoot + rec[3]

            if not os.path.isfile(path):
                self.stream.write("FILE ERR: #%d (for fileid %d) %s  -> File not found<br>"%(rec[0], rec[1], path))
                if delete:
                    sql = "delete from pool_files where fileid=%s"
                    cc.execute(sql, (rec[1],))
                else:
                    e+=1
                continue

            try:
                with open(path, 'rb+') as file:
                    file.read(30)
            except Exception as excp:
                self.stream.write("FILE ERR: #%d (for fileid %d) %s  -> %s<br>"%(rec[0], rec[1], path, str(excp)))
                e+=1

            size = os.stat(path)[stat.ST_SIZE]
            if size != rec[4]:
                self.stream.write("FILE ERR: #%d (for fileid %d) %s  -> size mismatch: db %d, fs %d<br>"%(rec[0], rec[1], path, rec[4], size))
                if repair:
                    sql = "update pool_files set size=%s where fileid=%s"
                    cc.execute(sql, (size, rec[1]))
                else:
                    e+=1

            if not rec[6]:
                self.stream.write("FILE ERR: #%d (for fileid %d) %s  -> filekey empty<br>"%(rec[0], rec[1], path))
                if defaultkey:
                    sql = "update pool_files set filekey=%s where fileid=%s"
                    cc.execute(sql, (defaultkey, (rec[1],)))
                else:
                    e+=1

            o+=1
        self.stream.write("Done. %d total, %d ok, %d errors <br>"%(c,o,e))

        return self.stream, ""

