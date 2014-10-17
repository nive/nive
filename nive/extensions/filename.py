# Copyright 2014 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive.definitions import ModuleConf, Conf


class FilenameLookup(object):
    """
    Enables readable url path names instead of ids for object traversal.
    Names are stored as meta.pool_filename.

    Extensions like *.html* are not stored. Path matching works independent 
    from extensions.
    """
    def Init(self):
        self.__name__ = self.meta.pool_filename or str(self.id)

    def __getitem__(self, id):
        """
        Traversal lookup based on object.pool_filename and object.id. Trailing extensions 
        are ignored.
        `file` is a reserved name and used in the current object to map file downloads. 
        """
        if id == u"file":
            raise KeyError, id
        id = id.split(u".")
        if len(id)>2:
            id = (u".").join(id[:-1])
        else:
            id = id[0]
        try:
            id = long(id)
        except:
            name = id
            id = 0
            if name:
                id = self.dataroot.FilenameToID(name, self.id)
            if not id:
                raise KeyError, id
        o = self.GetObj(id)
        if not o:
            raise KeyError, id
        return o



def SetupFilenameLookup(app, pyramidConfig):
    # get all roots and add extension
    extension = "nive.extensions.filename.FilenameLookup"
    def add(confs):
        for c in confs:
            e = c.extensions
            if e and extension in e:
                continue
            if e == None:
                e = []
            if isinstance(e, tuple):
                e = list(e)
            e.append(extension)
            c.unlock()
            c.extensions = tuple(e)
            c.lock()

    add(app.GetAllRootConfs())
    add(app.GetAllObjectConfs())


configuration = ModuleConf(
    id = "filenameLookup",
    name = u" Enables readable url path names instead of ids for object traversal",
    context = "nive.extensions.filename",
    events = (Conf(event="startRegistration", callback=SetupFilenameLookup),),
)
