# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive.tool import Tool, ToolView
from nive.definitions import ToolConf, FieldConf, ViewConf


configuration = ToolConf(
    id = "exampletool",
    context = "nive.tools.example.tool",
    name = "Empty tool for tests",
    description = "",
    apply = None,  #(IObject,)
    mimetype = "text/html",
)
configuration.data = [
    FieldConf(id="parameter1", datatype="bool",               default=0,  name="Show 1", description="Display 1"),
    FieldConf(id="parameter2", datatype="string", required=1, default="", name="Show 2", description="Display 2")
]
configuration.views = [
    ViewConf(name="", view=ToolView, attr="run", permission="system", context="nive.tools.example.tool")
]


class tool(Tool):

    def _Run(self, **values):
        result = "<h1>OK</h1>"
        return None, result

