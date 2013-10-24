# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive.tools import Tool
from nive.definitions import ToolConf, FieldConf


configuration = ToolConf(
    id = "exampletool",
    context = "nive.tools.example.tool",
    name = u"Empty tool for tests",
    description = "",
    apply = None,  #(IObject,)
    mimetype = "text/html",
)
configuration.data = [
    FieldConf(id="parameter1", datatype="bool",               default=0,  name=u"Show 1", description=u"Display 1"),
    FieldConf(id="parameter2", datatype="string", required=1, default="", name=u"Show 2", description=u"Display 2")
]



class tool(Tool):

    def _Run(self, **values):
        result = u"<h1>OK</h1>"
        return result

