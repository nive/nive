# -*- coding: utf-8 -*-

# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Test version of nive.tools.sendMail. Use `sendMailTester` as a replacement for `sendMail` in tests
or to disable actual mail delivery
"""

import logging

from nive.utils.utils import ConvertToList
from nive.definitions import ToolConf
from nive.tools.sendMail import sendMail
from nive.i18n import _

configuration = ToolConf("nive.tools.sendMail",
    context = "nive.tools.sendMailTester.sendMailTester",
    name = _("Fake Mailer"),
    description = __doc__
)


class sendMailTester(sendMail):

    def _Run(self, **values):
        """
        """
        
        host = values.get("host")
        port = values.get("port")
        sender = values.get("sender")
        user = values.get("user")
        pass_ = values.get("pass_")

        fromName = values.get("fromName")
        fromMail = values.get("fromMail")
        replyTo = values.get("replyTo")

        recvids = values.get("recvids")
        recvrole = values.get("recvrole")
        recvmails = values.get("recvmails")
        cc = values.get("cc")
        bcc = values.get("bcc")

        title = values.get("title")
        body = values.get("body")
        html = values.get("html")
        utf8 = values.get("utf8")
        ssl = values.get("ssl")

        showToListInHeader = values.get("showToListInHeader")
        force = values.get("force")
        debug = values.get("debug")
        maillog = values.get("maillog")
        log = logging.getLogger(maillog or "sendMail")

        self.InitStream()

        # lookup receivers
        recvs = []
        if recvmails:
            if isinstance(recvmails, str):
                recvs.append((recvmails, ""))
            else:
                recvs.extend(recvmails)
        if recvids or recvrole:
            recvs.extend(self._GetRecv(recvids, recvrole, force, self.app))
        if cc:
            cc = self._GetRecv(cc, None, force, self.app)
            if cc:
                recvs.extend(cc)
        if bcc:
            bcc = self._GetRecv(bcc, None, force, self.app)
            if bcc:
                recvs.extend(bcc)
        
        if len(recvs) == 0:
            self.stream.write(_("No receiver for the e-mail! Aborting."))
            return None, 0

        temp = []
        for r in recvs:
            temp.append(self._GetMailStr(r))
        to = temp
        temp = []
        for r in cc:
            temp.append(self._GetMailStr(r))
        cc = temp
        temp = []
        for r in bcc:
            temp.append(self._GetMailStr(r))
        bcc = temp

        if fromMail and fromMail != "":
            senderMail = sender
        else:
            fromMail = sender
            senderMail = ""

        contentType = "text/plain"
        if html:
            contentType = "text/html"
        if utf8:
            contentType += "; charset=utf-8"

        if debug:
            mails_original = ""
            for m in recvs:
                mails_original += m + "\r\n<br>"
            body += """\r\n<br><br>\r\nDEBUG\r\n<br> Original receiver: \r\n<br>""" + mails_original
            # in debug mode use default receiver mail as receiving address for all mails
            recvs = [(recvmails, "")]

        result = 1
        if showToListInHeader:
            self.stream.write((", ").join(r))
        else:
            for recv in recvs:
                self.stream.write(recv[0] + " ok, ")
                if log:
                    logdata = "%s - %s - %s" % (recv[0], recv[1], title)
                    log.debug(" %s", logdata)
        return None, result


    def _GetMailStr(self, mail):
        if isinstance(mail, str):
            return mail
        if isinstance(mail, (list,tuple)) and len(mail) > 1:
            return '"%s" <%s>' % (mail[1], mail[0])
        return mail[0]
        
