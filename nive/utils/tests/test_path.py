# -*- coding: utf-8 -*-

import unittest
import os
import tempfile

from nive.utils.path import DvPath



class Path(unittest.TestCase):
    
    def setUp(self):
        self.base = os.sep+"tmp_nivepathtest_000"+os.sep
        self.name = self.base+"nofile.txt"
        pass
    
    def test_Create(self):
        n = self.name
        p = DvPath(n)
        self.assertTrue(p._path==n)
        self.assertTrue(str(p)==n)
        p = DvPath(DvPath(n))
        self.assertTrue(str(p)==n)
        p.SetStr(n)
        self.assertTrue(str(p)==n)
        self.assertTrue(p.GetStr()==n)
        
        
    def test_Set(self):
        n = self.name
        p = DvPath(n)
        self.assertTrue(str(p)==n)
        p.SetName("new")
        self.assertTrue(str(p)==self.base+"new.txt", str(p))
        p.SetExtension("png")
        self.assertTrue(str(p)==self.base+"new.png")
        p.SetNameExtension("another.txt")
        self.assertTrue(str(p)==self.base+"another.txt")
        

    def test_Dirs(self):
        n = self.base
        p = DvPath(n)
        self.assertTrue(str(p)==n)
        p.Append("another_dir"+os.sep+"and.file")
        self.assertTrue(str(p)==n+"another_dir"+os.sep+"and.file", str(p))
        p = DvPath(n)
        p.AppendDirectory("the_last")
        self.assertTrue(str(p)==n+"the_last"+os.sep, str(p))
        p.RemoveLastDirectory()
        self.assertTrue(str(p)==n)
        p = DvPath(n[:-1])
        p.AppendSeperator()
        self.assertTrue(str(p)==self.base)
        
        
            
    def test_Get(self):
        n = self.name
        p = DvPath(n)
        self.assertTrue(p.GetPath() == self.base)
        self.assertTrue(p.GetName() == "nofile")
        self.assertTrue(p.GetExtension() == "txt")
        self.assertTrue(p.GetNameExtension() == "nofile.txt")
        self.assertTrue(p.GetSize() == -1)
        self.assertTrue(p.GetLastDirectory() == "tmp_nivepathtest_000")
        p.IsFile()
        p.IsDirectory()
        p.Exists()
        p.IsValid()

    
    def test_fncs(self):
        temp = tempfile.gettempdir()
        p = DvPath(temp)
        p.AppendDirectory("tmp_nivepathtest_000")
        p.Delete(deleteSubdirs = True)
        p.CreateDirectories()
        self.assertTrue(p.IsDirectory())
        p.CreateDirectoriesExcp()
        p.Rename("tmp_nivepathtest_111")
        p.AppendDirectory("tmp_nivepathtest_000")
        p.AppendDirectory("tmp_nivepathtest_000")
        p.CreateDirectories()
        self.assertTrue(p.IsDirectory())
        p = DvPath(temp)
        p.AppendDirectory("tmp_nivepathtest_000")
        p.Delete(deleteSubdirs = False)
        self.assertTrue(p.IsDirectory()==True)
        p.Delete(deleteSubdirs = True)
        self.assertTrue(p.IsDirectory()==False)
        #p.Execute("cmd", returnStream = True)
        
        
    def test_tempfilename(self):
        p = DvPath("file.txt")
        p.SetUniqueTempFileName()
        self.assertTrue(p.GetExtension()=="txt",p.GetExtension())
        
            
            