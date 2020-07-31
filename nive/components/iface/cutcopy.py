# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from nive.i18n import _
from nive.utils.utils import ConvertListToStr, ConvertToNumberList

from nive.definitions import IContainer, IRoot, ISort

"""
Cut, copy and paste functionality for objects 

conf for objects:
    - self.disableCopy: either unset or True/False

"""



class CopyView:
    """
    View functions for cut, copy and paste
    """
    CopyInfoKey = "CCP__"

    def cut(self):
        """
        """
        self.ResetFlashMessages()
        ids = self.GetFormValue("ids")
        if not ids:
            ids = [self.context.id]
        cp = self.SetCopyInfo("cut", ids, self.context)
        url = self.GetFormValue("url")
        if not url:
            url = self.PageUrl(self.context)
        msgs = _("OK. Cut.")
        ok = True
        return self.Redirect(url, [msgs], refresh=True)


    def copy(self):
        """
        """
        self.ResetFlashMessages()
        ids = self.GetFormValue("ids")
        if not ids:
            ids = [self.context.id]
        cp = self.SetCopyInfo("copy", ids, self.context)
        url = self.GetFormValue("url")
        if not url:
            url = self.PageUrl(self.context)
        msgs = _("OK. Copied.")
        return self.Redirect(url, [msgs], refresh=True)


    def paste(self):
        """
        """
        self.ResetFlashMessages()
        deleteClipboard=1
        url = self.GetFormValue("url")
        if not url:
            url = self.PageUrl(self.context)
        action, ids = self.GetCopyInfo()
        if not action or not ids:
            msgs = []
            return self.Redirect(url, msgs, refresh=True)

        pepos = self.GetFormValue("pepos",0)
        result = False
        msgs = [_("Method unknown")]
        if action == "cut":
            result, msgs = self.Move(ids, pepos, user=self.User())
            if result and deleteClipboard:
                cp = self.DeleteCopyInfo()
        elif action == "copy":
            result, msgs = self.Paste(ids, pepos, user=self.User())
        return self.Redirect(url, msgs, refresh=result)
    
    
    def SetCopyInfo(self, action, ids, context):
        """
        store in session or cookie
        """
        if not ids:
            return ""
        if isinstance(ids, str):
            ids=ConvertToNumberList(ids)
        cp = ConvertListToStr([action]+ids).replace(" ","")
        self.request.session[self.CopyInfoKey] = cp
        return cp


    def GetCopyInfo(self):
        """
        get from session or cookie
        """
        cp = self.request.session.get(self.CopyInfoKey,"")
        if isinstance(cp, str):
            cp = cp.split(",")
        if not cp or len(cp)<2:
            return "", []
        return cp[0], cp[1:]

    
    def ClipboardEmpty(self):
        """
        check if clipboard is empty
        """
        cp = self.request.session.get(self.CopyInfoKey,"")
        return cp==""
    

    def DeleteCopyInfo(self):    
        """
        reset copy info
        """
        self.request.session[self.CopyInfoKey] = ""


    def CanCopy(self, context=None):
        """
        """
        context = context or self.context
        if IRoot.providedBy(context):
            return False
        return not hasattr(context, "disableCopy") or not context.disableCopy

    def CanPaste(self, context=None):
        """
        """
        context = context or self.context
        if IContainer.providedBy(context):
            return False
        return not hasattr(context, "disableCopy") or not context.disableCopy


    def Paste(self, ids, pos, user, context=None):
        """
        Paste the copied object with id to this object
        """
        context = context or self.context
        root = context.root
        new = []
        msgs = []
        result = True
        for id in ids:
            id = int(id)
            if context.id == id:
                continue
            obj = root.LookupObj(id, preload="skip")
            if not obj:
                msgs.append(_("Object not found"))
                result = False
                continue
            newobj = context.Duplicate(obj, user)
            if not newobj:
                raise TypeError("Duplicate failed")
            if ISort.providedBy(context):
                context.InsertAfter(newobj.id, pos, user=user)
            new.append(newobj)
        if not context.app.configuration.autocommit:
            for o in new:
                o.Commit(user)
        if result:
            msgs.append(_("OK. Copied and pasted."))
        return result, msgs

    def Move(self, ids, pos, user, context=None):
        """
        Move the object with id to this object

        Events

        - beforeAdd(data=obj.meta, type=type)
        - afterDelete(id=obj.id)
        - moved()
        - afterAdd(obj=obj)
        """
        context = context or self.context
        root = context.root
        oldParent = None

        moved = []
        msgs = []
        result = True
        for id in ids:
            id = int(id)
            if context.id == id:
                continue
            obj = root.LookupObj(id, preload="skip")
            if not obj:
                msgs.append(_("Object not found"))
                result = False
                continue

            type = obj.GetTypeID()
            # allow subobject
            if not context.IsTypeAllowed(type, user):
                raise TypeError("Object cannot be added here")

            context.Signal("beforeAdd", data=obj.meta, type=type)
            if not oldParent or oldParent.id != obj.parent.id:
                oldParent = obj.parent
            obj.__parent__ = context
            obj.meta["pool_unitref"] = context.id
            oldParent.Signal("afterDelete", id=obj.id)
            obj.Signal("moved")
            # obj.Close()
            moved.append(obj)

        for o in moved:
            o.Commit(user)
            if ISort.providedBy(context):
                self.InsertAfter(o.id, pos, user=user)
            context.Signal("afterAdd", obj=o)
        if result:
            msgs.append(_("OK. Cut and pasted."))
        return result, msgs



