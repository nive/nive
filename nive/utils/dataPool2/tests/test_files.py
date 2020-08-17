

import copy, time, io
import unittest
from pkg_resources import resource_filename

from nive.utils.dataPool2.files import File


class fileentrytest(object):
    test=1
    
    @property
    def root(self):
        return resource_filename('nive.utils.dataPool2', 'tests/')
    
    @property
    def pool(self):
        return self
    
    def abspath(self, file):
        root = resource_filename('nive.utils.dataPool2', 'tests/')
        return root+"test_files.py"


class FileTest(unittest.TestCase):

    def test_create(self):
        #   File( filekey="", 
        #         filename="", 
        #         file=None, 
        #         size=0, 
        #         path="", 
        #         extension="", 
        #         fileid=0, 
        #         uid="", 
        #         tempfile=False, 
        #         filedict=None, 
        #         fileentry=None)
        file = File(filekey="aaa",
                    filename="qqqq.png", 
                    file=b"0123456789"
                    )
        self.assertTrue(file.filekey=="aaa")
        self.assertTrue(file.filename=="qqqq.png")
        self.assertTrue(file.size==10)
        self.assertTrue(file.extension=="png")

        file = File(filekey="aaa",
                    filename="qqqq.png", 
                    file=b"0123456789",
                    fileentry=fileentrytest()
                    )
        self.assertTrue(file.filekey=="aaa")
        self.assertTrue(file.filename=="qqqq.png")
        self.assertTrue(file.size==10)
        self.assertTrue(file.extension=="png")

        file = File(filekey="aaa",
                    path="/tmp/qqqq.png" 
                    )
        self.assertTrue(file.filekey=="aaa")
        self.assertTrue(file.filename=="qqqq.png")
        self.assertTrue(file.extension=="png")
        
        file = File(filedict={"filekey":"aaa",
                              "filename":"qqqq.png", 
                              "file":b"0123456789",
                              "fileentry":fileentrytest()}
                    )
        self.assertTrue(file.filekey=="aaa")
        self.assertTrue(file.filename=="qqqq.png")
        self.assertTrue(file.size==10)
        self.assertTrue(file.extension=="png")


    def test_read(self):
        file = File("aaa", filename="import.zip", tempfile=True)
        self.assertTrue(file.isTempFile())
        self.assertTrue(file.filename=="import.zip")
        self.assertTrue(file.extension=="zip")
        self.assertRaises(IOError, file.read)

        file = File(filekey="aaa",
                    filename="qqqq.png", 
                    file=b"0123456789",
                    fileentry=fileentrytest()
                    )
        self.assertTrue(file.read()==b"0123456789")

        file = File(filekey="aaa",
                    filename="qqqq.png", 
                    file=b"0123456789",
                    fileentry=fileentrytest()
                    )
        self.assertTrue(file.read(5)==b"01234")
        self.assertTrue(file.read(5)==b"56789")
        self.assertTrue(file.read(5)==b"")
        self.assertTrue(file.tell()==10)
        file.seek(0)
        self.assertTrue(file.tell()==0)

        file = File(filekey="aaa",
                    file=None,
                    fileentry=fileentrytest()
                    )
        self.assertRaises(IOError, file.read)
        file.close()
        self.assertFalse(file.isTempFile())


    def test_path(self):
        root = resource_filename('nive.utils.dataPool2', 'tests/')
        file = File("aaa")
        file.fromPath(root+"test_db.py")
        self.assertTrue(file.filename=="test_db.py")
        self.assertTrue(file.extension=="py")
        self.assertFalse(file.abspath())
        file.close()

        file = File(filekey="aaa",
                    file=None
                    )
        file.fileentry=fileentrytest
        file.path = root+"test_db.py"
        self.assertTrue(file.abspath().startswith(root))
        
        file = File("aaa", filename="qqqq.png", size=10)
        file.fromPath(root+"test_db.py")
        self.assertTrue(file.filename=="qqqq.png")
        self.assertTrue(file.extension=="png")
        file.close()
        
        
    def test_dict(self):
        file = File(filekey="aaa",
                    filename="qqqq.png", 
                    file=b"0123456789",
                    fileentry=fileentrytest()
                    )
        self.assertTrue(file.get("filekey")=="aaa")
        self.assertTrue(file.get("filename")=="qqqq.png")
        self.assertTrue(file.get("size")==10)

        self.assertTrue(file["filekey"]=="aaa")
        self.assertTrue(file["filename"]=="qqqq.png")
        self.assertTrue(file["size"]==10)

        self.assertTrue(file.get("none",123)==123)
        
        file.update({"filekey":"bbb", "filename":"oooo.png"})
        self.assertTrue(file.get("filekey")=="bbb")
        self.assertTrue(file.get("filename")=="oooo.png")
        
        for k in file:
            self.assertTrue(k)
