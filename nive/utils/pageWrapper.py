

import time
import _thread
import logging

from nive.definitions import Conf


#! requires requests


#------------------------------------------------------------------------------------


class content_splitter(object):
    """
    used for conten wrapper to split source page
    with optional parameters for start and end markers.
    returns a list of splitted text blocks (1-3). 
    
    Usage on source page either ::

        ... {{ content start }} ... {{ content end }} ...

    or simply ::

       ... {{ content start }} ...

    Configuration ::

        Conf(context=pageWrapper.content_splitter)

    With custom start and end markers ::

        Conf(context=pageWrapper.content_splitter,
             start="<!-- content start -->",
             end="<!-- content end -->")

    """
    defaultBlockCommentStart = "{{ content start }}"
    defaultBlockCommentEnd = "{{ content end }}"

    def __init__(self, configuration):
        self.start = configuration.get("start") or self.defaultBlockCommentStart
        self.end = configuration.get("end") or self.defaultBlockCommentEnd
        
    def __call__(self, data):
        if isinstance(data, (list, tuple)):
            filtered = []
            for part in data:
                filtered.append(self._part(part))
            return filtered
        elif not isinstance(data, str):
            return data
        return self._part(data)

    def _part(self, data):
        # lookup comments
        if data.find(self.start) == -1:
            return [data]
        
        # split data
        l1 = data.split(self.start)
        if not self.end or data.find(self.end) == -1:
            return l1

        l2 = l1[-1].split(self.end)
        l1 = l1[:-1]
        data = l1 + l2
        return data
    
    
    

class string_replacer(object):
    """
    String replacer filter 
    replaces string 'orig' with 'new' in stream
    returns changed stream
    
    example ::

        ...
        text
        http://192.168.0.1/
        text
        ...

    converts to ::

        ...
        text
        http://www.mydomain.com
        text
        ...

    Configuration ::

       Conf(context=pageWrapper.string_replacer,
            orig="http://192.168.0.1",
            new="http://www.mydomain.com"),

    """
    def __init__(self, configuration):
        self.meta = configuration.get("meta")
        self.orig = configuration.get("orig")
        self.new = configuration.get("new")
        self.default = ""
        
    def __call__(self, data):
        if not self.orig or not data:
            return data
        if isinstance(data, (list, tuple)):
            filtered = []
            for part in data:
                filtered.append(self._part(part))
            return filtered
        elif not isinstance(data, str):
            return data
        return self._part(data)

    def _part(self, data):    
        new = self.new or self.default
        return data.replace(self.orig, new)




class replace_request_var(object):
    """
    Replace marker if `key` in view.request or view is set.

    Configuration ::

        Conf(context=pageWrapper.replace_request_var,
             marker=u"</title>",
             key=u"wrapper_page_title",
             placeholder=u" %s</title>",
             default=u""
        ),
    """

    def __init__(self, configuration):
        self.configuration = configuration

    def __call__(self, data, view):
        if not isinstance(data, str):
            return data
        if data.find(self.configuration.marker) == -1:
            return data
        if isinstance(view, dict):
            value = view.get(self.configuration.key, self.configuration.default)
        else:
            value = view.request.environ.get(self.configuration.key, self.configuration.default)
        return data.replace(self.configuration.marker, self.configuration.placeholder%value)



# defaults -----------------------------------------------------------------------------------------------------------------

# e.g.    Conf(context=string_replacer, orig="http://192.168.0.1/", new="http://www.test.de/")

class PageWrapper(object):
    """
    """
    defaultFilter = (Conf(context=content_splitter),)

    def __init__(self, url="", cache=True, interval=3600, timeout=5,
                 user=None, password=None, loadFilter=None, viewFilter=None):
        """
        
        :param url: 
        :param cache: 
        :param interval: 
        :param user: 
        :param password: 
        :param loadFilter: 
        :param viewFilter: 
        :return: nothing
        """
        self.url = url
        self.cache = cache
        self.updateInterval = interval        # in secs
        self.timeout = timeout
        self.user = user
        self.password = password

        self.loadFilter = loadFilter or self.defaultFilter
        self.viewFilter = viewFilter

        self.log = logging.getLogger("pagewrapper")
        self._parts = []
        self._lastUpdate = 0
        self._err = ""


    def Parts(self, **kw):
        return self._GetParts(**kw)

    def Header(self, **kw):
        page = self._GetParts(**kw)
        if len(page):
            return self.FilterOnView(page[0], **kw)
        return ""

    def Footer(self, **kw):
        page = self._GetParts(**kw)
        if len(page) < 2:
            return ""
        return self.FilterOnView(page[-1], **kw)


    def Load(self):
        self._Load()

    def Purge(self):
        self._lastUpdate = 0

    def Status(self):
        return self._err


    # bw
    def GetParts(self):
        return self.Parts()
    # bw
    def GetHeader(self):
        return self.Header()
    # bw
    def GetFooter(self):
        return self.Footer()

    # wrapper ------------------------------------------------------------------------

    def FilterOnLoad(self, data):
        if not self.loadFilter:
            # no filter configured
            return (data,)

        for fconf in self.loadFilter:
            data = fconf.context(fconf)(data)
        return data

    def FilterOnView(self, data, **kw):
        if not self.viewFilter:
            # no filter configured
            return data

        for fconf in self.viewFilter:
            data = fconf.context(fconf)(data, **kw)
        return data


    def _GetParts(self, **kw):
        if self._Reload():
            return self._Load()
        return self._parts

    def _Reload(self):
        if not self.cache or not self._lastUpdate:
            return True
        if self._lastUpdate + self.updateInterval < time.time():
            return True
        return False

    def _Load(self):
        # return values: HTTP Status, Reason, Message, Data, Time
        import requests
        try:
            t = time.time()
            resp = requests.get(self.url, timeout=self.timeout)
            self._err = ""
            data = resp.text

            if not data or not 199 < resp.status_code < 300:
                self._err = str(resp.status_code)
                self.log.error("Load failed: %d - %s" % (resp.status_code, self.url))
                return self._parts
            else:
                self.log.info("Loaded: %d - %s"%(resp.status_code, self.url))

            self._lastUpdate = time.time()
            data = self.FilterOnLoad(data)
            if self.cache:
                self._Cache(data)
            return data
        except Exception as e:
            self._err = str(e)
            self.log.exception("Load failed: "+self.url)
            return self._parts


    def _Cache(self, data):
        lock = _thread.allocate_lock()
        try:
            lock.acquire(1)
            self._parts = data
            if lock.locked():
                lock.release()
            return True
        except:
            if lock and lock.locked():
                lock.release()
            return False


