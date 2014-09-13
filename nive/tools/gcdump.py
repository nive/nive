# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive.tool import Tool
from nive.definitions import ToolConf, IApplication
from nive.i18n import _

configuration = ToolConf(
    id = "gcdump",
    context = "nive.tools.gcdump.gcdump",
    name = _(u"Object dump"),
    description = _("This function dumps a list of all objects found in memory."),
    apply = (IApplication,),
    data = [],
    mimetype = "text/html"
)


import gc
from types import InstanceType

def DumpObjects(stream):
        
    limit = 1
    # Recursively expand slist's objects
    # into olist, using seen to track
    # already processed objects.
    def _getr(slist, olist, seen):
        for e in slist:
            if id(e) in seen:
                continue
            seen[id(e)] = None
            olist.append(e)
            tl = gc.get_referents(e)
            if tl:
                _getr(tl, olist, seen)
    
    gcl = gc.get_objects()
    olist = []
    seen = {}
    # Just in case:
    seen[id(gcl)] = None
    seen[id(olist)] = None
    seen[id(seen)] = None
    # _getr does the real work.
    _getr(gcl, olist, seen)

    stream.write(u"Number of objects found: ")
    stream.write(unicode(len(olist)))
    stream.write(u"<br>\n")
    #stream.write(olist[0].__dict__)
    trefs = {}
    for o in olist:#[100000:100200]:
        t = type(o)
        ref = str(t)
        if ref.find("weakref")!=-1:
            try:
                t2 = type(o())
                ref = "%s &gt; %s" %(ref, str(t2))
            except:
                pass
        elif t==InstanceType:
            try:
                ref = "%s &gt; %s" %(ref, str(o.__class__))
            except:
                pass

        if not ref in trefs:
            trefs[ref]=1
        else:
            trefs[ref]+=1
        del o
    del olist
    del gcl
    del seen
        
    stream.write("<table class='table-bordered table table-condensed' style='width:70%'>\n")
    sorted = []
    for r,v in trefs.items():
        if v < limit:
            continue
        sorted.append((r,v))
    sorted.sort(key=lambda tup: tup[1])
    while sorted:
        i = sorted.pop()
        stream.write("<tr><td>%s</td><th>%d</th></tr>\n"%(i[0].replace("<","").replace(">",""),i[1]))
    stream.write("</table>\n")            

    return 1




class gcdump(Tool):
    """
    """

    def _Run(self, **values):
        
        return DumpObjects(self.stream)
        
