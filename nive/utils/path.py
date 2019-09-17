# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

try:    from win32pipe import popen
except: from os import popen

import os
import zipfile
import stat
import shutil
import uuid
import tempfile

class DvPath(object):
    """
    Common path and directory operations
    """

    def __init__(self, path = None):
        """
        string: path
        """
        self._path = ""
        if path:
            if isinstance(path, str):
                self.SetStr(path)
            else:
                self.SetStr(str(path))

    def __str__(self):
        return self._path

    def SetStr(self, path):
        """
        string: path
        """
        self._path = path

    def GetStr(self):
        """
        returns string
        """
        return self._path


    # set ----------------------------------------------------------------------------
    def SetName(self, name):
        """
        string: name
        """
        p, s = os.path.split(self._path)
        s, ext = os.path.splitext(self._path)
        if len(p) > 0:
            p += os.sep
        self._path = p + name + ext

    def SetExtension(self, ext):
        """
        string: ext
        """
        if not ext:
            return
        if not ext.startswith("."):
            ext = "." + ext
        p, old = os.path.splitext(self._path)
        self._path = p + ext

    def SetNameExtension(self, nameExt):
        """
        string: nameExt
        """
        self._path, s = os.path.split(self._path)
        self.AppendSeperator()
        self._path += nameExt

    def Append(self, path):
        """
        string: path
        """
        if not path:
            return
        if not path.startswith(os.sep):
            self.AppendSeperator()
        self._path += path

    def AppendSeperator(self):
        if self._path!="" and not self._path.endswith(os.sep):
            self._path += os.sep

    def AppendDirectory(self, dir):
        """
        string: dir
        """
        self.AppendSeperator()
        self.SetName(dir)
        self.AppendSeperator()

    def RemoveLastDirectory(self):
        name = self.GetNameExtension()
        self.SetNameExtension("")
        if self._path.endswith(os.sep):
            self._path = self._path[:-1]
        self.SetNameExtension("")
        self.AppendSeperator()
        self.SetNameExtension(name)


    # get ----------------------------------------------------------------------------

    def GetPath(self): 
        """
        Path includes trailing seperator
        return: string
        """
        if not self.IsValid():
            return ""
        path, name = os.path.split(self._path)
        if not path:
            return ""
        if not path.endswith(os.sep):
            path += os.sep
        return path

    def GetName(self):
        """
        return: string
        """
        if not self.IsValid():
            return ""
        path, name = os.path.split(self._path)
        name, ext = os.path.splitext(name)
        return name

    def GetExtension(self):
        """
        return: string
        """
        if not self.IsValid():
            return ""
        path, ext = os.path.splitext(self._path)
        if ext.startswith("."):
            ext = ext[1:]
        return ext

    def GetNameExtension(self):
        """
        return: string
        """
        if not self.IsValid():
            return ""
        path, name = os.path.split(self._path)
        return name

    def GetSize(self):
        """
        return long
        """
        if not self.IsValid():
            return ""
        if self.IsDirectory():
            return 0
        try:
            return os.stat(self._path)[stat.ST_SIZE]
        except:
            return -1

    def GetLastDirectory(self):
        """
        Name of last directory
        return string
        """
        if not self.IsValid():
            return ""
        path, name = os.path.split(self._path)
        if path.endswith(os.sep):
            path = path[:-1]
        parts = path.split(os.sep)
        if not parts:
            return ""
        return parts[-1]


    # state ----------------------------------------------------------------------------
    def IsFile(self):
        """
        return bool
        """
        return os.path.isfile(self._path)

    def IsDirectory(self):
        """
        return bool
        """
        return os.path.isdir(self._path)

    def Exists(self):
        """
        return bool
        """
        return self.IsFile() or self.IsDirectory()

    def IsValid(self): #INTERN
        """
        return bool
        """
        return len(self._path) > 0


    # operations ----------------------------------------------------------------------------

    def Delete(self, deleteSubdirs = False):
        """
        Ignores exceptions
        return bool
        """
        if deleteSubdirs:
            path = self.GetPath()
            if not self.IsDirectory():
                return False
            shutil.rmtree(self._path, ignore_errors=True)
            return not self.IsDirectory()

        try:
            if self.IsDirectory():
                os.rmdir(self._path)
                return not self.IsDirectory()
            os.remove(self._path)
        except OSError:
            pass
        return not self.IsFile()


    def CreateDirectories(self):
        """
        Ignores exceptions
        return bool
        """
        if self.Exists():
            return True
        try:
            path, name = os.path.split(self._path)
            os.makedirs(path)
            return True
        except:
            return False


    def CreateDirectoriesExcp(self):
        """
        Throws exceptions
        return bool
        """
        if self.Exists():
            return True
        path, name = os.path.split(self._path)
        os.makedirs(path)
        return True


    def Rename(self, newName):
        """
        return bool
        """
        if not self.IsFile():
            return False
        os.renames(self._path, newName)
        return True


    def Execute(self, cmd, returnStream = True):
        """
        execute the current path with popen and returns std out
        """
        s = popen(self._path + " " + cmd, "r")
        if returnStream:
            return s
        r = ""
        while 1:
            d = s.readline()
            if not d or d == ".\n" or d == ".\r":
                break
            r += d
        return r
    
    
    def SetUniqueTempFileName(self):
        """
        Creates a unique tempfile name with the current file extension
        """
        dir = tempfile.gettempdir()
        if not dir:
            return False
        ext = self.GetExtension()
        self._path = dir
        self.AppendSeperator()
        name = str(uuid.uuid4())
        self.SetName(name)
        self.SetExtension(ext)
        return True


    def Copy(self, copyPath):
        """(string copyPath) return bool
        Copy file to copyPath. Directories are created if necessary
        """
        try:
            aOldPath = self._path
            self._path = copyPath
            self.CreateDirectories()
            shutil.copy2(aOldPath, str(copyPath))
            return True
        except Exception as e:
            self._path = aOldPath
            return False

    def Pack(self, add=(), rootDir=""):
        """
        create a zip or tar archive from file/directory list.
        to store files with relative directory set rootdir
        to base directory for files
        format is choosen from extension
        """
        if self.GetExtension() == "zip":
            return self.Zip(add, rootDir)
        return self.Tar(add, rootDir)

    def Zip(self, add=(), rootDir=""):
        def zipdir(path, ziph):
            # ziph is zipfile handle
            for root, dirs, files in os.walk(path):
                for file in files:
                    fn = os.path.join(root, file)
                    ziph.write(fn, arcname=fn[len(rootDir):])

        zipf = zipfile.ZipFile(self._path, 'w', zipfile.ZIP_DEFLATED)
        for file in add:
            if os.path.isdir(file):
                zipdir(file, zipf)
            else:
                zipf.write(file, arcname=file[len(rootDir):])
        zipf.close()
        return True


    def Tar(self, add=(), rootDir=""):
        files = ""
        for f in add:
            files += "'%s' " % (f)
        cmd = """cvzf %(path)s %(files)s""" % {"path": self._path, "files": str(files)}
        s = popen("tar " + cmd, "r")
        r = ""
        while 1:
            d = s.readline()
            if not d or d == ".\n" or d == ".\r":
                break
            r += d
        return True