

import unicodedata
import re




class PathExtension(object):
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
        if self.AddExtension(filename) == self.meta.pool_filename:
            # no change
            return
        filename = self.UniqueFilename(filename)
        if filename:
            # update
            self.meta["pool_filename"] = self.AddExtension(filename)
        else:
            # reset filename
            self.meta["pool_filename"] = ""
        self._SetName()
        
        
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
        while root.FilenameToID(self.AddExtesion(name), unitref, parameter=dict(id=self.id), operators=dict(id="!=")) != 0:
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
        path = unicodedata.normalize("NFKD", path) #.encode("ascii", "ignore")
        path = re.sub('[^\w\s-]', '', path).strip().lower()
        path = re.sub('[-\s]+', '_', path)
        
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


    def AddExtesion(self, filename):
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
                id = self.root.FilenameToID(name, self.id)
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
                id = self.FilenameToID(name, self.id)
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


