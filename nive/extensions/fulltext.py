
from bs4 import BeautifulSoup

from nive.tool import Tool, ToolView

from nive.definitions import ModuleConf, ToolConf, Conf, ViewConf, FieldConf, IApplication




class Fulltext:
    """
    Fulltext support for cms pages. Automatically updates fulltext on commit. 
    """

    def Init(self):
        self.ListenEvent("commit", "UpdateFulltext")


    def UpdateFulltext(self, **kw):
        """
        Update fulltext for entry. Text is generated automatically.
        """
        if not self.app.configuration.fulltextIndex:
            return
        # get text from contained elements
        text = self.GetTexts()
        self.dbEntry.WriteFulltext(self.FormatFulltext(text))


    def FormatFulltext(self, textlist):
        # formats the raw text better display
        return "\r\n\r\n".join(textlist)

    def GetTexts(self):
        # loop all fulltext fields and make one string
        text = []
        for fld in self.app.configurationQuery.GetAllMetaFlds(ignoreSystem=False):
            if not fld.get("fulltext"):
                continue
            value = self.meta.get(fld["id"], "")
            if not value:
                continue
            if fld.datatype=="htext":
                soup = BeautifulSoup(value, "html.parser")
                text.append(soup.get_text())
            else:
                text.append(str(value))

        # data
        for fld in self.configuration.data:
            if not fld.get("fulltext"):
                continue
            value = self.data.get(fld["id"], "")
            if not value:
                continue
            if fld.datatype=="htext":
                soup = BeautifulSoup(value, "html.parser")
                text.append(soup.get_text())
            else:
                text.append(str(value))

        return text

    def GetFulltext(self):
        """
        Get current fulltext value
        """
        if not self.app.configuration.fulltextIndex:
            return ""
        return self.dbEntry.GetFulltext()

    def DeleteFulltext(self):
        """
        Delete fulltext
        """
        if not self.app.configuration.fulltextIndex:
            return
        self.dbEntry.DeleteFulltext()


class RewriteFulltext(Tool):

    def _Run(self, **values):

        self.InitStream()
        app = self.app
        root = app.root
        datapool = app.db
        conn = datapool.connection
        c = conn.cursor()

        # delete
        sql = "delete from pool_fulltext"
        c.execute(sql)
        c.close()
        conn.commit()
        self.stream.write("Deleted previous fulltext index.<br>")

        pages = root.search.Select(parameter={"pool_state": 1})
        cnt = len(pages)
        err = 0
        for page in pages:
            page = page[0]
            try:
                obj = root.LookupObj(page)
            except TypeError:
                self.stream.write("Error: Invalid obj (%(id)d).<br>" % {"id": page})
                continue
            if not obj:
                err += 1
                self.stream.write("Error: Unable to open page (%(id)d).<br>" % {"id": page})
            else:
                try:
                    obj.UpdateFulltext()
                except Exception as e:
                    err += 1
                    self.stream.write("Error: Unable to update page (%(id)d).<br>" % {"id": page})
                    self.stream.write(str(e))
                    self.stream.write("<br><br>")
        conn.commit()
        self.stream.write("Updated fulltext index. Finished.<br>")
        self.stream.write("%(cnt)d pages ok. %(err)d failed.<br>" % {"cnt": cnt, "err": err})
        return self.stream, 1


def SetupFulltext(app, pyramidConfig):
    # get all objects and add extension
    extension = "nive.extensions.fulltext.Fulltext"

    def add(confs):
        for c in confs:
            e = c.extensions
            if e is None:
                e = []
            elif extension in e:
                continue
            if isinstance(e, tuple):
                e = list(e)
            e.append(extension)
            c.unlock()
            c.extensions = tuple(e)
            c.lock()

    add(app.configurationQuery.GetAllObjectConfs())


toolconf = ToolConf(
    id="updatefulltext",
    context="nive.extensions.fulltext.RewriteFulltext",
    name="Rewrite fulltext index",
    description="Delete and rewrite the fulltext index.",
    apply=(IApplication,),
    mimetype="text/html",
    data=[
        FieldConf(id="tag", datatype="string", default="updatefulltext", hidden=1)
    ],
    views=[
        ViewConf(name="", view=ToolView, attr="form", permission="system", context="nive.extensions.fulltext.RewriteFulltext")
    ]
)

configuration = ModuleConf(
    id="fulltext",
    name="Element fulltext extension",
    context=Fulltext,
    events=(Conf(event="startRegistration", callback=SetupFulltext),),
    modules=[toolconf]
)

