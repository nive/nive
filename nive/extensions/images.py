

"""
Image processing extension
--------------------------
Converts images based on profiles and stores the converted images as different
files in object.
Profiles are configured as ``object.configuration.imageProfiles`` with the following attributes: ::

    source = "imagefull": field id of the source image 
    dest = "image": field id of the destination image
    format = "jpg": image format
    quality = "80": quality depending on format
    width = 400: width of new image
    height = 0: height of new image
    extension = "jpg": file name extension
    condition = None: callback function which takes the image object as parameter and returns whether
                       the profile is valid for the image object or not 

Examples ::

    ProfileImage = Conf(source="imagefull", dest="image", format="JPEG", 
                        quality="80", width=400, height=0, extension="jpg")
    ProfileIcon =  Conf(source="imagefull", dest="icon",  format="JPEG", 
                        quality="70", width=100, height=0, extension="jpg")
    
If either width or height is 0 the new image is scaled proportionally.
See PIL documentation for possible format and quality values.
 
"""

from nive.utils.path import DvPath
from nive import File
from nive.helper import ResolveName

PILloaded = 1
try:     from PIL import Image
except:  PILloaded=0


class ImageExtension:

    def Init(self):
        if PILloaded:
            self.ListenEvent("commit", "ProcessImages")
            self.ListenEvent("deleteFile", "CleanupImages")
        elif self.configuration.imageProfiles:
            self.app.log.error("Image Converter: PIL not imported!")


    def ProcessImages(self, **kw):
        images = []
        keys = self.files.keys()
        for p in self.configuration.imageProfiles:
            if p.source in images:
                continue
            if not p.source in keys:
                continue
            f = self.files.get(p.source)
            if not f or not f.tempfile:
                continue
            images.append(p.source)
        self.Process(images=images)
        self.Signal("imageprocessed", **kw)


    def CleanupImages(self, **kw):
        fldname = kw.get("fldname")
        keys = self.files.keys()
        if not fldname in keys:
            return

        for p in self.configuration.imageProfiles:
            if p.source!=fldname or p.dest==fldname:
                continue
            self.dbEntry.DeleteFile(p.dest)


    def GetImgSize(self, image):
        """
        Returns the image size (width, height) in pixel
        """
        i = self.files.get(image)
        if not i:
            return 0,0
        try:
            im = Image.open(i.path)
            return im.size
        except:
            return 0,0        
        

    def Process(self, images=None, profiles=None):
        """
        Process images and create versions from profiles. ::
        
            images = list of image field ids to process. if none all images based on 
                     selected profiles are processed.
            profiles = list of profiles to process. if none all profiles are 
                       processed
            returns result, messages
        
        Example: If `Process(images=['highres'], profiles=None)` all versions with
        `source=highres` are updated.

        Events: 
        updateImage(profile)

        """
        if not PILloaded:
            return False, ["Python image library (PIL) not installed."]
        convert = []
        profiles = profiles or self.configuration.imageProfiles
        if not images:
            for p in profiles:
                if not self._CheckCondition(p):
                    continue
                convert.append(p)
        else:
            for p in profiles:
                if not self._CheckCondition(p):
                    continue
                if p.source in images:
                    convert.append(p)
        if not convert:
            return True
        msgs = []
        result = True
        for profile in convert:
            r, m = self._Convert(profile)
            msgs += m
            if not r:
                result = False
            else:
                self.Signal("updateImage", profile=profile)
        return result, msgs
        
        
    def _CheckCondition(self, profile):
        if not hasattr(profile, "condition"):
            return True
        c = ResolveName(profile.condition)
        return c(self)
      
        
    def _Convert(self, profile):
        source = self.files.get(profile.source)
        if not source or not source.tempfile:
            # convert only if tempfile
            return False, ()
        if not source:
            return False, ["Image not found: " + profile.source]
        p = DvPath()
        p.SetUniqueTempFileName()
        p.SetExtension(profile.extension)
        destPath = str(p)
        
        try:
            try:
                source.file.seek(0)
            except:
                pass
            try:
                iObj = Image.open(source)
            except IOError:
                # no file to be converted
                return False, ()
            iObj = iObj.convert("RGB")
            
            # resize
            size = [profile.width, profile.height]
            if size[0] != 0 or size[1] != 0:
                if size[0] == 0:    
                    size[0] = size[1]
                elif size[1] == 0:    
                    size[1] = size[0]
                x, y = iObj.size
                if x > size[0]: y = y * size[0] / x; x = size[0]
                if y > size[1]: x = x * size[1] / y; y = size[1]
                size = int(x), int(y)
            
            iObj = iObj.resize(size, Image.ANTIALIAS)
            iObj.save(destPath, profile.format)
            try:
                source.file.seek(0)
            except:
                pass
            
            # file meta data
            imgFile = open(destPath, 'rb')
            filename = DvPath(profile.dest+"_"+source.filename)
            filename.SetExtension(profile.extension)
            file = File(filekey=profile.dest, 
                        filename=str(filename), 
                        file=imgFile,
                        size=p.GetSize(), 
                        path=destPath, 
                        extension=profile.extension,  
                        tempfile=True)
            self.files.set(profile.dest, file)
        finally:
            # clean temp file
            p.Delete()
        return True, []
        





      
