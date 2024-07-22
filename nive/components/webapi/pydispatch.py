# Copyright 2012-2014 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt


"""
Python API Dispatching
----------------------
The main Web API is meant to be called through HTTP requests with
user and state information passed in with the request object. To
make the same API functionality including security easily useable 
from python code, this file provides dispatch functions with 
several options.

Url usage:: 

    '/todos/api/newItem?pool_type=todo&text=test'

Python usage: 
    
    todos.api.dispatch(method='newItem', 
                       secure=True, request=self.request, 
                       pool_type='todo', text='test')
    or
    todos.api(method='newItem', pool_type='todo', text='test')

handles virtual request and reponse objects for view processing:

- request.POST = kws
- request.response
- response.status

"""
import json

from pyramid.view import render_view
from pyramid import testing


class DispatchResponse(object):
    status = None

class DispatchRequest(object):
    response = DispatchResponse()
    context = None
    POST = None
    GET = None


class Dispatcher(object):
  
    def dispatch(self, method, secure=False, request=None, **kw):
        """
        If *secure* is true permissions of the current user are checked against the view. If the
        user lacks the necessary permissions and empty string is returned or if *raiseUnauthorized*
        is True HTTPForbidden is raised. 
        
        returns rendered result
        """
        if request is None:
            secure = False
            
        disprequest = testing.DummyRequest() #DispatchRequest()
        disprequest.context = self
        disprequest.POST = kw
        disprequest.method = "POST"
        disprequest.content_type = "dict"
        value = render_view(self, disprequest, method, secure)
        if value is None:
            value = {}
        else:
            value = json.loads(value)
        return value, disprequest.response.status




