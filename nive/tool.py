# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
nive Tool base class to use as base for new tools. 

Tools represent an executeable function to be run with or without an
object context. Tools can be loaded by dotted python name or, if registered
by app.Register(), with their id. 
Registering tools is necessary to set application specific values and to 
automatically apply tools to objects.

Tools can be applied to selected object types or interfaces or global. They are always 
loaded by *id*. ::

    tool = app().GetTool("sendMail")
    tool(recv="me@domain.com",title="New mail")

Tool return values on execution are :: 

    result, stream/data = tool()

*stream/data* depends on the tool. By default tools use StringIO to write output data. *result*
signals whether the tool succeeded or not.
 
Parameter value lookup on execution:

1) ``tool.Run(**values)``: execution specific values
2) ``tool.configuration.values``: configured values on application level
3) ``tool.data``: default configured prarameter values

To create a new tool:
Subclass and overwrite ``def _Run()`` function. Use self.stream to write result data.

"""

from StringIO import StringIO

from nive.definitions import Interface, ITool, implements
from nive.definitions import ConfigurationError
from nive.views import BaseView
from nive.forms import ToolForm


class Tool(object):
    """

    """
    implements(ITool)

    def __init__(self, configuration, app):
        self.configuration = configuration
        self.app_ = app
        self.stream = False

        self.__name__ = ""
        self.__parent__ = None
        self.__acl__ = []

        self.id = ""
        self.mimetype = "text/html"
        self._LoadConfiguration()


    def _LoadConfiguration(self):
        """
        loads self.configuration 
        """
        if not self.configuration:
            raise ConfigurationError, "Tool configuration is None. Please load the tool by referencing the tool configuration."
        
        c = self.configuration
        for k in c.keys():
            # special values
            if k == "id" and c.id:
                self.__name__ = c.id
                self.id = c.id
            if k == "acl" and c.acl:
                self.__acl__ = c.acl
                continue
            # map value
            setattr(self, k, c[k])
            
    @property
    def app(self):
        """ returns the cms application object """
        return self.app_
    

    # Subclass functions --------------------------------------------

    def _Run(self, **values):
        result = True
        return result


    # Execution --------------------------------------------------------------------------------------------

    def __call__(self, **kw):
        return self.Run(**kw)


    def Run(self, **kw):
        """
        Execute the tool.
        
        If stream is disabled (self.stream = None) and no stream is passed,
        the function returns the result data as string/binary.
        Otherwise the stream is returned as second parameter.
        
        returns bool, stream
        """
        if not self.stream:
            self.stream = StringIO()

        # call function
        values = self.ExtractValues(**kw)
        values["original"] = kw
        result = self._Run(**values)
        return result, self.stream


    def ExtractValues(self, **kw):
        """
        Extract values for configured parameters

        1) tool.Run(values): call specific values
        2) tool.configuration.values: configured values on application level
        3) tool.data: default prarameter values
        
        returns dictionary
        """
        values = {}
        cv = self.configuration.values
        for p in self.configuration.data:
            if   p.id in kw:      values[p.id] = kw[p.id]
            elif p.id in cv:      values[p.id] = cv[p.id]
            else:                 values[p.id] = p.default
        return values


    def AppliesTo(self, poolType):
        """
        Return if this tool applies to the given nive object type.
        
        returns bool
        """
        if not self.configuration.apply:
            return False
        return poolType in self.configuration.apply


    def GetAllParameters(self):
        """
        Return the configured parameter definitions for the function
        
        returns list
        """
        return self.configuration.data


    def GetParameter(self, id):
        """
        Get single parameter definition for function
        
        returns configuration or None
        """
        for fld in self.configuration.data:
            if fld.id == id:
                return fld
        return None



class _IGlobal(Interface):
    """
    used for global tool registration as tool.apply
    """

class _GlobalObject(object):
    """
    used for global tool lookup
    """
    implements(_IGlobal)
    
    
    
class ToolView(BaseView):    
    """
    Default tool views supporting a form renderer and direct execution

    Include the view in the tool configuration as follows :: 

        configuration.views = [
          ViewConf(name="", view=ToolView, attr="run", permission="system", context="... tool context class ...")
        ]

    or for the form ::

        configuration.views = [
          ViewConf(name="", view=ToolView, attr="form", permission="system", context="... tool context class ...")
        ]

    """
    
    def form(self):
        """
        Run a tool by rendering the default form and execute on submit.
        This function does not return a valid Response object. This view is meant to
        be called from another view or template:
        ``view.RenderView(tool)``
        """
        form = ToolForm(view=self, loadFromType=self.context.configuration)
        form.Setup()
        result, data, action = form.Process()
        if not isinstance(data, basestring):
            try:
                data = data.getvalue()
            except:
                data = str(data)
        if result and action.id == "run" and self.context.mimetype != "text/html":
            fn = None
            if hasattr(self.context, "filename"):
                fn = self.context.filename
            return self.SendResponse(data=data, mime=self.context.mimetype, raiseException=True, filename=fn)
        return self.SendResponse(form.HTMLHead() + data, mime=self.context.mimetype, raiseException=False) 
    
    
    def run(self):
        """
        Run a tool by rendering the default form and execute on submit.
        This function does not return a valid Response object. This view is meant to
        be called from another view or template:
        ``view.RenderView(tool)``
        """
        tool = self.context
        values = self.GetFormValues(method="POST")
        values["request"] = self.request
        result = tool.Run(**values)
        data = tool.stream
        if not isinstance(data, basestring):
            try:
                data = data.getvalue()
            except:
                data = str(data)
        return self.SendResponse(data, mime=self.context.mimetype, raiseException=False)     
    
           