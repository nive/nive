# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Object based events
-------------------
Events are object based and registered with the object itself. So they will
only be called as long as the object exists and are meant in the first place 
to be used in conjunction with object extension. 

Events work quite simple: the signal representing the event is just a string
and is registered in combination with a function. If the event is fired 
somewhere, the linked function will be called with event specific paramaters.

*signals* have not to be registered. They are just fired by calling *Signal(signal)*.

Every object and root fires the *init* event linked to **Init()** on creation.
So it is not necessary to register for *init* yourself and but use it as plugin point to 
register your own events.

For example if you would like to get your function **Edit()** called if the object is 
updated, add this function to your objects class: ::
    
    class myObject:
    
        def Init(self):
            self.ListenEvent("update", "Edit")
        
    
        def Edit(self, data):
            # e.g. process data 
            return
            
Inventing custom events is quite easy: :: 

        def SomeEvent(self):
            self.Signal("some_event")
            
            
For non Object or Root derived classes initialize the event system by adding a signal
to the __init__ function: ::

    def __init__(self):
        self.Signal("init")
    
"""

import inspect

class Events(object):
    """
    Object event listener.
    """
    
    def InitEvents(self):
        """
        Call Init() for every super class
        """
        if not hasattr(self, "_eventdispatch"):
            self._eventdispatch = {}
        for cls in self.__class__.__mro__:
            f = cls.__dict__.get("Init")
            if f is not None:
                f(self)


    def SetupEventsFromConfiguration(self, events):
        """
        Calls ListenEvent for each event registered in a configuration.events slot.

        :param events: list of events to listen to
        :return: nothing
        """
        for e in events:
            self.ListenEvent(e.event, e.callback)
                

    def ListenEvent(self, signal, function):
        """
        Register a function for an event. 
        
        - *signal*: the event to listen for
        - *function*: callback to be called if the event is fired

        """
        if not self._eventdispatch.has_key(signal):
            self._eventdispatch[signal] = [function]
        else:
            self._eventdispatch[signal].append(function)


    def RemoveListener(self, signal, function=None):
        """
        Remove the function from an event.

        - *signal*: the event to listen for
        - *function*: callback to be called if the event is fired

        """
        if not self._eventdispatch.has_key(signal):
            return
        if not function:
            del self._eventdispatch[signal]
            return
        try:
            self._eventdispatch[signal].remove(function)
        except ValueError:
            pass
    

    def Signal(self, signal, raiseExcp=True, **kw):
        """
        Fire an event *signal*. *kw* are the parameters passed to the callback.
        
        Functions called by the event system can pass values back if required.
        The returned values are added to list of results. Each entry is a tuple
        containing the result, the called function as string and the actual class
        the function was called for. e.g.
        
           ((True, "MyEvent", "<class MyObject ...>"))

        """
        if signal==u"init":
            self.InitEvents()
            #return
        if not self._eventdispatch or not signal in self._eventdispatch:
            return None
        result = []
        for fnc in self._eventdispatch[signal]:
            try:
                if isinstance(fnc, basestring):
                    for cls in self.__class__.__mro__:
                        f = cls.__dict__.get(fnc)
                        if f is not None:
                            r = f(self, **kw)
                            if r is not None:
                                # store result if not None as tuple
                                # (result, str(fnc), str(cls))
                                result.append((r, str(fnc), str(cls)))
                else:
                    if "context" in inspect.getargspec(fnc).args:
                        r = fnc(context=self, **kw)
                    else:
                        r = fnc(**kw)
                    if r is not None:
                        # store result if not None as tuple
                        # (result)
                        result.append((r, str(fnc)))
            except:
                if raiseExcp:
                    raise
        # cleanup event table
        if signal=="close":
            self._Cleanup()
        return result


    def _Cleanup(self):
        if self._eventdispatch is None:
            return
        for e in self._eventdispatch:
            self._eventdispatch[e] = None
        self._eventdispatch = None
