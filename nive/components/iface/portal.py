
import sys
import traceback

from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPError
from pyramid.renderers import render_to_response

from nive import portal


class IfacePortal(portal.Portal):

    # TODO remove default views
    def SetupPortalViews(self, config):
        # redirects
        config.add_view(servererror, context=Exception)
        config.add_view(httperror, context=HTTPError)
        config.add_view(portal.forbidden_view, context=Forbidden)
        config.add_view(portal.portal_view, name="", context="nive.portal.Portal")
        config.add_view(portal.logout_view, name="logout", context="nive.portal.Portal")
        config.add_view(portal.login_view,  name="login", context="nive.portal.Portal")
        config.add_view(portal.account_view,name="account", context="nive.portal.Portal")
        config.add_view(portal.robots_view, name="robots.txt", context="nive.portal.Portal")
        config.add_view(portal.sitemap_view, name="sitemap.xml", context="nive.portal.Portal")
        #config.add_view(favicon_view, name="favicon.txt", context="nive.portal.Portal", view=PortalViews)
    
        config.commit()


# http errors and redirects ------------------------------------------------------------------

def servererror(errorResponse, request):
    """
    Called in case of server side exceptions resulting in 500 status codes
    """
    if not isinstance(errorResponse, str):
        errorResponse = str(errorResponse)
    resp = render_to_response("nive.components.iface:templates/error.pt",
                              {"error":"500", "message":"The error was: %s" % errorResponse},
                              request=request)
    resp.status = "500 Server error"
    traceback.print_exc(file=sys.stdout)
    return resp

def httperror(errorResponse, request):
    """
    Queries the context object to find out whether to redirect or return the error status only.
    
    1) request.context.ErrorType(request.view_name)==1 -> Status response
    2) request.environ["HTTP_X_REQUESTED_WITH"]==XMLHttpRequest -> Status response
    3) all other cases -> default error page
    
    Extracts the context and the current url from the workspace, looks up the workspace runtime 
    configuration and redirects to the configured forbidden url.
    """
    response = errorResponse
    def status():
        headers = [("X-Result", "false")]
        if hasattr(response, "headerlist"):
            headers += list(response.headerlist)
        response.headerlist = headers    
        return response
    # 1)
    try:
        if request.context.HTTPErrorType(request.view_name)==1:
            return status()
    except:
        pass
    # 2)
    if request.environ.get("HTTP_X_REQUESTED_WITH")=="XMLHttpRequest":
        return status()
    # 3)
    resp= render_to_response("nive.components.iface:templates/error.pt",
                              {"error":"404"},
                              request=request)
    resp.status = "404 Not found"
    return resp
 
