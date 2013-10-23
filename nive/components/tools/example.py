# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import types

from nive.tools import Tool
from nive.definitions import ToolConf, FieldConf


configuration = ToolConf()
configuration.id = "exampletool"
configuration.context = "nive.components.tools.example.tool"
configuration.name = u"Empty tool for tests"
configuration.description = ""
configuration.apply = None  #(IApplication,)
configuration.data = [
    FieldConf(**{"id": "parameter1", "datatype": "bool",     "required": 0,     "readonly": 0, "default": 0, "name": u"Show 1",    "description": u"Display 1"}),
    FieldConf(**{"id": "parameter2", "datatype": "string",     "required": 0,     "readonly": 0, "default": 0, "name": u"Show 2",    "description": u"Display 2"})
]
configuration.mimetype = "text/html"



class tool(Tool):

    def _Run(self, **values):
        result = u"<h1>OK</h1>"
        return result

