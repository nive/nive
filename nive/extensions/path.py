

import unicodedata
import re




class PathExtension:
    """
    Enables readable url path names instead of ids for object traversal.
    Names are stored as meta.pool_filename and generated from
    title by default. Automatic generation can be disabled by setting
    *meta.customfilename* to False for each object.
    
    Extensions like *.html* are not stored. Path matching works independent 
    from extensions.
    """
    maxlength = 55   # max path length
    containerNamespace = True   # unique filenames for container or global
    extension = None


    def Init(self):
        if self.id == 0:
            # skip roots
            return
        self.ListenEvent("commit", "TitleToFilename")
        self._SetName()

    
    def TitleToFilename(self, **kw):
        """
        Uses title for filename
        """
        customfilename = self.data.get("customfilename", None)  # might not exist
        if customfilename:
            self._SetName()
            return
        # create url compatible filename from title
        filename = self.EscapeFilename(self.meta.title)
        # make unique filename
        filename = self.UniqueFilename(filename)
        if self.AddExtension(filename) == self.meta.pool_filename:
            # no change
            return
        if filename:
            # update
            self.meta["pool_filename"] = self.AddExtension(filename)
        else:
            # reset filename
            self.meta["pool_filename"] = ""
        self._SetName()
        self.Signal("pathupdate", path=self.meta["pool_filename"])
        
        
    def UniqueFilename(self, name):
        """
        Converts name to valid path/url
        """
        if name == "file":
            name = "file_"
        if self.containerNamespace:
            unitref = self.parent.id
        else:
            unitref = None
        cnt = 1
        root = self.root
        while root.search.FilenameToID(self.AddExtension(name), unitref, parameter=dict(id=self.id), operators=dict(id="!=")) != 0:
            if cnt>1:
                name = name[:-1]+str(cnt)
            else:
                name = name+str(cnt)
            cnt += 1
        return name


    def EscapeFilename(self, path):
        """
        Converts name to valid path/url
        
        Path length between *self.maxlength-20* and *self.maxlength* chars. Tries to cut longer names at spaces.      
        (based on django's slugify)
        """
        path = unicodedata.normalize("NFKD", path).encode("ascii", "ignore")
        path = path.decode("utf-8")
        path = re.sub('[^\w\s-]', '', path).strip().lower()
        path = re.sub('[-\s]+', '_', path)
        # avoid ids as filenames
        try:
            int(path)
            path += "_n"
        except:
            pass

        # cut long filenames
        cutlen = 20
        if len(path) <= self.maxlength:
            return path
        # cut at '_' 
        pos = path[self.maxlength-cutlen:].find("_")
        if pos > cutlen:
            # no '_' found. cut at maxlength.
            return path[:self.maxlength]
        return path[:self.maxlength-cutlen+pos]


    def AddExtension(self, filename):
        if not self.extension:
            return filename
        return "%s.%s" % (filename, self.extension)


    # system functions -----------------------------------------------------------------
    
    def __getitem__(self, id):
        """
        Traversal lookup based on object.pool_filename and object.id. Trailing extensions 
        are ignored if self.extension is None.
        `file` is a reserved name and used in the current object to map file downloads. 
        """
        if id == "file":
            raise KeyError(id)

        if self.extension is None:
            id = id.split(".")
            if len(id)>2:
                id = (".").join(id[:-1])
            else:
                id = id[0]

        try:
            id = int(id)
        except ValueError:
            name = id
            id = 0
            if name:
                id = self.root.search.FilenameToID(name, self.id)
            if not id:
                raise KeyError(id)

        obj = self.GetObj(id)
        if obj is None:
            raise KeyError(id)
        return obj


    def _SetName(self):
        self.__name__ = self.meta["pool_filename"]
        if not self.__name__:
            self.__name__ = str(self.id)




class RootPathExtension(object):
    """
    Extension for nive root objects to handle alternative url names
    """
    extension = None

    # system functions -----------------------------------------------------------------

    def __getitem__(self, id):
        """
        Traversal lookup based on object.pool_filename and object.id. Trailing extensions
        are ignored.
        `file` is a reserved name and used in the current object to map file downloads.
        """
        if id == "file":
            raise KeyError(id)

        if self.extension is None:
            id = id.split(".")
            if len(id)>2:
                id = (".").join(id[:-1])
            else:
                id = id[0]

        try:
            id = int(id)
        except:
            name = id
            id = 0
            if name:
                id = self.search.FilenameToID(name, self.id)
            if not id:
                raise KeyError(id)

        obj = self.GetObj(id)
        if not obj:
            raise KeyError(id)

        return obj


class PersistentRootPath(object):
    """
    Extension for nive root objects to handle alternative url names
    """

    def Init(self):
        self.ListenEvent("commit", "UpdateRouting")
        self.ListenEvent("dataloaded", "UpdateRouting")
        self.UpdateRouting()

    def UpdateRouting(self, **kw):
        # check url name of root
        if self.meta.get("pool_filename"):
            name = self.meta.get("pool_filename")
            if name != self.__name__:
                # close cached root
                self.app._CloseRootObj(name=self.__name__)
                # update __name__ and hash
                self.__name__ = str(name)
                self.path = name
                # unique root id generated from name . negative integer.
                self.idhash = abs(hash(self.__name__))*-1



from nive.tool import Tool, ToolView
from nive.definitions import ToolConf, FieldConf, ViewConf, IApplication


tool_configuration = ToolConf(
    id = "rewriteFilename",
    context = "nive.extensions.path.RewriteFilenamesTool",
    name = "Rewrite pool_filename based on title",
    description = "Rewrites all or empty filenames based on form selection.",
    apply = (IApplication,),
    mimetype = "text/html",
    data = [
        FieldConf(id="types", datatype="checkbox", default="", settings=dict(codelist="types"), name="Object types", description=""),
        FieldConf(id="testrun", datatype="bool", default=1, name="Testrun, no commits", description=""),
        FieldConf(id="resetall", datatype="string", default="", size=15, name="Reset all filenames", description="<b>Urls will change! Enter 'reset all'</b>"),
        FieldConf(id="tag", datatype="string", default="rewriteFilename", hidden=1)
    ],

    views = [
        ViewConf(name="", view=ToolView, attr="form", permission="admin", context="nive.extensions.path.RewriteFilenamesTool")
    ]
)

class RewriteFilenamesTool(Tool):

    def _Run(self, **values):

        parameter = dict()
        if values.get("resetall")!="reset all":
            parameter["pool_filename"] = ""
        if values.get("types"):
            tt = values.get("types")
            if not isinstance(tt, list):
                tt = [tt]
            parameter["pool_type"] = tt
        operators = dict(pool_type="IN", pool_filename="=")
        fields = ("id", "title", "pool_type", "pool_filename")
        root = self.app.root
        recs = root.search.Search(parameter, fields, max=10000, operators=operators, sort="id", ascending=0)

        if len(recs["items"]) == 0:
            return "<h2>None found!</h2>", False

        user = values["original"]["user"]
        testrun = values["testrun"]
        result = []
        cnt = 0
        for rec in recs["items"]:
            obj = root.LookupObj(rec["id"])
            if obj is None or not hasattr(obj, "TitleToFilename"):
                continue

            filename = obj.meta["pool_filename"]
            obj.TitleToFilename()
            if filename!=obj.meta["pool_filename"]:
                result.append(filename+" <> "+obj.meta["pool_filename"])
            if testrun==False:
                obj.dbEntry.Commit(user=user)
                #obj.CommitInternal(user=user)

            cnt += 1

        return "OK. %d filenames updated, %d different!<br>%s" % (cnt, len(result), "<br>".join(result)), True

