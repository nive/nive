

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
import logging

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
            if f is None:
                continue
            images.append(p.source)
        r,m = self.Process(images=images, force=kw.get("force", False))
        return r


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
        

    def Process(self, images=None, profiles=None, force=False):
        """
        Process images and create versions from profiles. ::
        
            images = list of image field ids to process. if none all images based on 
                     selected profiles are processed.
            profiles = list of profiles to process. if none all profiles are 
                       processed
            force = convert non temp files
            returns result (count processed), messages
        
        Example: If `Process(images=['highres'], profiles=None)` all versions with
        `source=highres` are updated.

        Events: 
        updateImage(profile)

        """
        if not PILloaded:
            return 0, ["Python image library (PIL) not installed."]
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
            return 0, ["No match"]
        msgs = []
        result = 0
        for profile in convert:
            r = self._Convert(profile, force)
            result += r
            if r:
                self.Signal("updateImage", profile=profile)
        self.Signal("imageprocessed")
        return result, []
        
        
    def _CheckCondition(self, profile):
        if not hasattr(profile, "condition"):
            return True
        c = ResolveName(profile.condition)
        return c(self)
      
        
    def _Convert(self, profile, force):
        source = self.files.get(profile.source)
        dest = self.files.get(profile.dest)
        if source is None:
            return 0
        if not source.tempfile and not force and dest:
            # convert only if tempfile or dest does not exist or force=True
            return 0

        p=None
        try:
            try:
                source.file.seek(0)
            except:
                pass
            try:
                iObj = Image.open(source)
            except IOError:
                # no file to be converted
                return 0
            iObj = iObj.convert("RGB")
            
            # resize
            size = [profile.width, profile.height]
            if size[0] != 0 or size[1] != 0:
                #if size[0] == 0:
                #    size[0] = size[1]
                #elif size[1] == 0:
                #    size[1] = size[0]
                resize = True
                x, y = iObj.size
                if size[0] and x > size[0]:
                    y = y * size[0] / x
                    x = size[0]
                elif size[1] and y > size[1]:
                    x = x * size[1] / y
                    y = size[1]
                else:
                    # original is smaller
                    resize = False
                    if profile.source==profile.dest:
                        # same image -> skip
                        return 0

                size = int(x), int(y)
                if resize:
                    iObj = iObj.resize(size, Image.ANTIALIAS)

            p = DvPath()
            p.SetUniqueTempFileName()
            p.SetExtension(profile.extension)
            destPath = str(p)
            iObj.save(destPath, profile.format)
            try:
                if source.file.closed:
                    source.file = None
                else:
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
            if p is not None:
                p.Delete()
        return 1
        



from nive.tool import Tool, ToolView
from nive.definitions import ToolConf, FieldConf, ViewConf, IApplication


tool_configuration = ToolConf(
    id = "processImages",
    context = "nive.extensions.images.ProcessImagesTool",
    name = "Process images based on conversion profiles",
    description = "Rewrites all or empty images based on form selection.",
    apply = (IApplication,),
    mimetype = "text/html",
    data = [
        FieldConf(id="types", datatype="checkbox", default="", required=1, settings=dict(codelist="types"), name="Object types", description=""),
        FieldConf(id="emptyonly", datatype="bool", default=1, name="Rewrite only empty images", description=""),
        FieldConf(id="testrun", datatype="bool", default=1, name="Testrun, no commits", description=""),
        FieldConf(id="tag", datatype="string", default="processImages", hidden=1)
    ],

    views = [
        ViewConf(name="", view=ToolView, attr="form", permission="admin", context="nive.extensions.images.ProcessImagesTool")
    ]
)

class ProcessImagesTool(Tool):

    def _Run(self, **values):

        parameter = dict()
        if values.get("types"):
            tt = values.get("types")
            if not isinstance(tt, list):
                tt = [tt]
            parameter["pool_type"] = tt
        operators = dict(pool_type="IN")
        fields = ("id", "title", "pool_type", "pool_filename")
        root = self.app.root
        recs = root.search.Search(parameter, fields, max=1000000, operators=operators, sort="id")

        if len(recs["items"]) == 0:
            return values, "<h2>None found!</h2>"

        user = values["original"]["user"]
        testrun = values["testrun"]
        emptyonly = values["emptyonly"]
        result = []
        cnt = 0
        rcnt = 0
        log = logging.getLogger("converter")
        for rec in recs["items"]:
            rcnt +=1
            if rcnt%1000==0:
                log.info("Processing Images: %d of %d ... %d processed."%(rcnt, recs["total"], cnt))
            obj = root.LookupObj(rec["id"])
            if obj is None or not hasattr(obj, "ProcessImages"):
                continue
            if testrun:
                cnt += 1
                continue
            try:
                if emptyonly:
                    cnt += obj.ProcessImages(user=user)
                else:
                    cnt += obj.ProcessImages(user=user, force=True)

                obj.dbEntry.Commit(user=user)
            except Exception as e:
                err = str(rec["id"])+" Error: "+str(e)
                log.error(err)
                result.append(err)
        return None, "OK. %d images processed!<br>%s" % (cnt, "<br>".join(result))





      
