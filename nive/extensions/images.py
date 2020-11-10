

"""
Image processing extension
--------------------------
Converts images based on profiles and stores the converted images as different
files in object.
Profiles are configured as ``object.configuration.imageProfiles`` with the following attributes: ::

    source = "imagefull": field id of the source image 
    dest = "image": field id of the destination image
    quality = "80": quality depending on format
    width = 400: width of new image
    height = 0: height of new image
    skip = []: skip conversion if fmt in list
    format = "jpg": image format
    extension = "jpg": file name extension
    condition = None: callback function which takes the image object as parameter and returns whether
                       the profile is valid for the image object or not 

Examples ::

    ProfileImage = Conf(source="imagefull", dest="image", format="JPEG", 
                        quality="80", width=400, height=0, extension="jpg")
    ProfileIcon =  Conf(source="imagefull", dest="icon",  format="JPEG", 
                        quality="70", width=100, height=0, extension="jpg")

Fill ::
    ProfileImage = Conf(source="imagefull", dest="image", format="JPEG",
                        quality=80, width=630, height=0, extension="jpg",
                        fill=(630, 354), bg=(242,242,242), crop=True, enlarge=True, constraint=True, ratio="16:9")


    
If either width or height is 0 the new image is scaled proportionally.
See PIL documentation for possible format and quality values.
 
"""
import logging
import io

from nive.utils.path import DvPath
from nive import File
from nive.helper import ResolveName

PILloaded = 1
try:     from PIL import Image
except:  PILloaded=0

PyVipsloaded = 1
try:     import pyvips  # requires libvips
except:  PyVipsloaded=0


class ImageExtension:

    def Init(self):
        if self.configuration.get("imageProfiles"):
            if PILloaded:
                self.ListenEvent("commit", "ProcessImages")
                #self.ListenEvent("update", "ProcessImages")
                self.ListenEvent("deleteFile", "CleanupImages")
            else:
                self.app.log.error("Image Converter: PIL not imported!")


    def ProcessImages(self, **kw):
        images = []
        #keys = self.files.keys()
        for p in self.configuration.imageProfiles:
            if p.source in images:
                continue
            #if not p.source in keys:
            #    continue
            #f = self.files.get(p.source)
            #if f is None:
            #    continue
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

        try:
            source.file.seek(0)
        except:
            pass

        # skip conversion and copy file
        if profile.get("copy"):
            if source.extension in profile.get("copy"):
                # copy file
                data = source.read()
                file = File(filekey=profile.dest,
                            filename=str(profile.dest + "_" + source.filename),
                            file=io.BytesIO(data),
                            size=len(data),
                            path=None,
                            extension=source.extension,
                            tempfile=True)
                self.files.set(profile.dest, file)
                return 1

        destFormat = profile.get("format")
        destExtension = profile.get("extension")

        try:
            # svg
            if source.extension != "svg":
                # iObj = Image.open(source) ? PIL bug closes source if used multiple times
                iObj = Image.open(io.BytesIO(source.read()))
            else:
                # set dest format to png
                if not "format" in profile:
                    destFormat = "png"
                    destExtension = "png"
                image = pyvips.Image.thumbnail_buffer(source.read(), profile.width)
                iObj = Image.open(io.BytesIO(image.write_to_buffer("." + destExtension)))
                del image

        except IOError as e:
            try:
                source.file.seek(0)
            except:
                pass
            # no file converted
            logging.warning("IOError: Failed to convert image: %s -> %s" % (source.filename, str(e)))
            return 0

        temp = None
        try:
            iObj = iObj.convert("RGB")

            if profile.get("fill"):
                iObj = self._ScaleAndFill(iObj, profile)
            else:
                iObj = self._Scale(iObj, profile)

            if not destFormat:
                destFormat = self._NormalizeFmt(source.extension)
                destExtension = source.extension

            temp = DvPath()
            temp.SetUniqueTempFileName()
            temp.SetExtension(destExtension)
            destPath = str(temp)
            iObj.save(destPath, destFormat)
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
            filename.SetExtension(destExtension)
            file = File(filekey=profile.dest, 
                        filename=str(filename), 
                        file=imgFile,
                        size=temp.GetSize(),
                        path=destPath, 
                        extension=destExtension,
                        tempfile=True)
            self.files.set(profile.dest, file)
        finally:
            try:
                source.file.seek(0)
            except:
                pass
            # clean temp file
            if temp is not None:
                temp.Delete()
        return 1


    def _Scale(self, img, settings):
        # resize
        size = [settings.width, settings.height]
        if size[0] != 0 or size[1] != 0:
            # if size[0] == 0:
            #    size[0] = size[1]
            # elif size[1] == 0:
            #    size[1] = size[0]
            resize = True
            x, y = img.size
            if size[0] and x > size[0]:
                y = y * size[0] / x
                x = size[0]
            elif size[1] and y > size[1]:
                x = x * size[1] / y
                y = size[1]
            else:
                # original is smaller
                resize = False
                if settings.source == settings.dest:
                    # same image -> skip
                    return img

            size = int(x), int(y)
            if resize:
                img = img.resize(size, Image.ANTIALIAS)

        return img


    def _ScaleAndFill(self, img, settings):
        newx = settings.get("width", 0)
        newy = settings.get("heigth", 0)
        fill = settings.get("fill", None)
        crop = settings.get("crop", False)
        enlarge = settings.get("enlarge", True)
        x, y = img.size

        # enlarge
        if not enlarge and (newx>x or newy>y):
            return img

        if x<fill[0]:
            # width smaller dest
            newx = 0
            newy = fill[1]

        # constraint dimension and fit in box
        if settings.get("constraint", True) or newx==0 or newy==0:
            ratio = settings.get("ratio", "").split(":")
            if newx == 0 and newy != 0:
                newx = newy / float(y) * x
                if len(ratio)==2 and newx > newy / float(ratio[1]) * float(ratio[0]):
                    # too width for box
                    newx = newy / float(ratio[1]) * float(ratio[0])
                    newy = newx / float(x) * y

            elif newy == 0 and newx != 0:
                newy = newx / float(x) * y
                if len(ratio)==2 and newy > newx / float(ratio[0]) * float(ratio[1]):
                    # too width for box
                    newy = newx / float(ratio[0]) * float(ratio[1])
                    newx = newy / float(y) * x

        # valid?
        if newx==0 and newy==0:
            return img

        size = int(newx), int(newy)
        img = img.resize(size, Image.ANTIALIAS)

        if newx<fill[0]:
            # fill sides with bgcolor
            color = settings.get("bg", (242,242,242))
            newImage = Image.new("RGB", fill, color)
            newImage.paste(img, (int((fill[0]-newx)/2), 0))
            img = newImage
        elif newy>fill[1] and crop:
            # crop
            top = int((newy-fill[1])/2)
            img = self._Crop(img, (0, top, fill[0], fill[1]+top))

        return img


    def _Crop(self, img, box):
        img = img.crop(box=box)
        img.load()
        return img


    def _NormalizeFmt(self, fmt):
        if fmt.lower() in ("jpg", "jpeg"):
            return "JPEG"
        return fmt





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

        self.InitStream()
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
            self.stream.write("<strong>Found nothing</strong>")
            return self.stream, False

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
                err = str(rec["id"])+" "+str(rec["pool_type"])+" Error: "+str(e)
                log.error(err)
                self.stream.write(err+"<br>")
        if testrun:
            self.stream.write("Done. %d images found to be processed!<br>%s" % (cnt, "<br>".join(result)))
            return self.stream, ""
        self.stream.write("OK. %d images processed!<br>" % (cnt))
        return self.stream, ""





      
