# -*- coding: utf-8 -*-

# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Receivers are looked up by user ids or roles. Sender name, receiver, title, and body can be set as values by call.

mails as list with [(email, name),...] ("name@mail.com","Name")
"""

import time
import logging

from smtplib import SMTP
from smtplib import SMTPServerDisconnected, SMTPRecipientsRefused, SMTPHeloError, SMTPSenderRefused, SMTPDataError, SMTPException

from email.message import EmailMessage
from email.header import Header

from nive.utils.utils import ConvertToList
from nive.definitions import ConfigurationError
from nive.definitions import ToolConf, FieldConf
from nive.tool import Tool
from nive.i18n import _

configuration = ToolConf(
    id = "sendMail",
    context = "nive.tools.sendMail.sendMail",
    name = _("Send mails to registered users"),
    description = __doc__,
    apply = None,
    data = (
        FieldConf(id="host",    name=_("SMTP host"),       datatype="string",       required=1,     readonly=1, default="",    description=""),
        FieldConf(id="port",    name=_("SMTP port"),       datatype="number",       required=1,     readonly=1, default=21,     description=""),
        FieldConf(id="sender",  name=_("SMTP sender mail"),datatype="email",        required=1,     readonly=1, default="",    description=""),
        FieldConf(id="user",    name=_("SMTP user"),       datatype="string",       required=0,     readonly=1, default="",    description=""),
        FieldConf(id="pass_",   name=_("SMTP password"),   datatype="password",     required=0,     readonly=1, default="",    description=""),

        FieldConf(id="fromName",  name=_("Sender name"),   datatype="string",       required=0,     readonly=0, default="",    description=""),
        FieldConf(id="fromMail",  name=_("Sender mail"),   datatype="string",       required=0,     readonly=0, default="",    description=""),
        FieldConf(id="replyTo",   name=_("Reply to"),      datatype="string",       required=0,     readonly=0, default="",    description=""),
        FieldConf(id="recvrole",  name=_("Receiver role"),    datatype="string",    required=1,     readonly=0, default="",    description=""),
        FieldConf(id="recvids",   name=_("Receiver User IDs"),datatype="string",    required=1,     readonly=0, default="",    description=""),
        FieldConf(id="recvmails", name=_("Receiver Mail"),    datatype="string",    required=1,     readonly=0, default="",    description=""),
        FieldConf(id="force",     name=_("Ignore notify settings"),datatype="bool", required=0,     readonly=0, default=0,      description=""),
        FieldConf(id="cc",        name=_("CC"),            datatype="string",       required=0,     readonly=0, default="",    description=""),
        FieldConf(id="bcc",       name=_("BCC"),           datatype="string",       required=0,     readonly=0, default="",    description=""),

        FieldConf(id="title", name=_("Title"),             datatype="string",       required=1,     readonly=0, default="",    description=""),
        FieldConf(id="body",  name=_("Text"),              datatype="htext",        required=0,     readonly=0, default="",    description=""),
        FieldConf(id="html",  name=_("Html format"),       datatype="bool",         required=0,     readonly=0, default=1,      description=""),
        FieldConf(id="utf8",  name=_("UTF-8 encoding"),    datatype="bool",         required=0,     readonly=0, default=1,      description=""),
        FieldConf(id="ssl",   name=_("Use SSL"),           datatype="bool",         required=0,     readonly=0, default=1,      description=""),
        FieldConf(id="maillog",  name=_("Log mails"),      datatype="string",       required=0,     readonly=0, default="",    description=""),
        FieldConf(id="showToListInHeader",name=_("Show all receivers in header"), datatype="bool", required=0, readonly=0, default=0,    description=""),

        FieldConf(id="debug", name=_("Debug mail receiver"),datatype="email",       required=0,     readonly=0, default="",    description=_("If not empty all mails are sent to this address. The original mail receivers are ignored.")),
    ),
    mimetype = "text/html"
    #modules = WidgetConf(name=_("Root"),      viewmapper="rootsettings",id="admin.rootsettings",sort=1100,   apply=(IApplication,), widgetType=IAdminWidgetConf),
)


class sendMail(Tool):

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
        # `recvs` is the raw list of mails in the form of `(mail, name)` tuples
        recvs = []
        if recvmails:
            if isinstance(recvmails, str):
                recvs.append((recvmails, ""))
            else:
                recvs.extend(recvmails)
        if recvids or recvrole:
            recvs.extend(self._GetRecv(recvids, recvrole, force, self.app))

        if len(recvs) == 0:
            self.stream.write(_("No receiver for the e-mail! Aborting."))
            return None, 0

        # lookup copy and blindcopy receiver
        if cc:
            cc = self._GetRecv(cc, None, force, self.app)
            if cc:
                recvs.extend(cc)
        if bcc:
            bcc = self._GetRecv(bcc, None, force, self.app)
            if bcc:
                recvs.extend(bcc)
        
        # to, cc, bcc are the corresponding lists formatted as strings `name <mail>`
        to = [self._GetMailStr(r) for r in recvs]
        cc = [self._GetMailStr(r) for r in cc]
        bcc = [self._GetMailStr(r) for r in bcc]

        if fromMail:
            senderMail = sender
        else:
            fromMail = sender
            senderMail = ""

        charset = "ascii"
        contentType = None
        if html:
            contentType = "html"
        if utf8:
            charset = "utf-8"

        if debug:
            mails_original = "\r\n<br>".join([self._GetMailStr(r) for r in recvs])
            body += """\r\n<br><br>\r\nDEBUG\r\n<br> Original receiver: \r\n<br>""" + mails_original
            # in debug mode use default receiver mail as receiving address for all mails
            recvs = [(debug, "")]

        message = self._PrepareMessage(
            fromMail=fromMail,
            recvs=recvs,
            title=title,
            body=body,
            fromName=fromName,
            to=to,
            cc=cc,
            bcc=bcc,
            contentType=contentType,
            charset=charset,
            sender=senderMail,
            replyTo=replyTo)

        if not host:
            raise ConfigurationError("Empty mail host")
        mailer = SMTP(host, port)
        try:
            mailer.ehlo()
            if ssl:
                mailer.starttls()
                mailer.ehlo()
        except (SMTPServerDisconnected, SMTPHeloError, SMTPException) as e:
            log.error(" %s", repr(e))
            return None, False

        if user:
            mailer.login(user, str(pass_))

        result = 1
        log.info("send to -> %s", ", ".join([r[0] for r in recvs]))
        for recv in recvs:
            try:
                if not showToListInHeader:
                    del message["To"]
                    message["To"] = self._GetMailStr(recv)

                #log.debug(message.as_string(unixfrom=False))
                info = mailer.sendmail(fromMail, recv[0], message.as_string(unixfrom=False))
                self.stream.write(recv[0] + " ok, ")
                log.debug("%s - %s - %s" % (recv[0], title, str(info)))

            except (SMTPSenderRefused, SMTPDataError) as e:
                result = 0
                log.error("%s", repr(e))
                log.error("->  %s", "%s - %s - %s" % (recv[0], recv[1], title))
                self.stream.write(str(e))

            except SMTPRecipientsRefused as e:
                result = 0
                log.warning("%s", repr(e))
                self.stream.write(str(e))

            except (SMTPServerDisconnected,) as e:
                result = 0
                log.error("%s", repr(e))
                self.stream.write(str(e))
                break

        mailer.quit()
        return None, result


    def _PrepareMessage(self, **kw):
        contentType = kw.get("contentType")
        charset = kw.get("charset", "utf-8")

        message = EmailMessage()
        message.set_content(kw.get("body"), subtype=contentType, charset=charset)
        message["Date"] = self._FormatDate()
        message["Subject"] = Header(kw.get("title"), charset=charset).encode()

        fromName = kw.get("fromName")
        fromMail = kw.get("fromMail")
        message["From"] = self._GetMailStr((fromMail, fromName))

        to = kw.get("to")
        if isinstance(to, (list,tuple)):
            to = ", ".join(to)
        message["To"] = to

        cc = kw.get("cc")
        if cc:
            if isinstance(cc, (list,tuple)):
                cc = ", ".join(cc)
            message["Cc"] = cc

        bcc = kw.get("bcc")
        if bcc:
            if isinstance(bcc, (list,tuple)):
                bcc = ", ".join(bcc)
            message["Bcc"] = bcc

        sender = kw.get("sender")
        if sender:
            message["Sender"] = sender

        replyTo = kw.get("replyTo")
        if replyTo:
            message["Reply-To"] = replyTo

        return message


    def _FormatDate(self):
        """Return the current date and time formatted for a message header."""
        weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        monthname = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        now = time.time()
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(now)
        s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (weekdayname[wd], day, monthname[month], year, hh, mm, ss)
        return s


    def _GetMailStr(self, mail):
        if isinstance(mail, str):
            return mail
        if len(mail) > 1 and mail[1]:
            return '"%s" <%s>' % ((Header(mail[1], "utf-8").encode()), mail[0])
        return mail[0]
        

    def _GetRecv(self, recvids, recvrole, force, app):
        userdb = app.root
        if not hasattr(userdb, "GetUsersWithRole"):
            userdb = app.portal.userdb.GetRoot()
        recvList = []
        # check roles
        recvids2 = []
        if recvrole:
            recvids2 = userdb.GetUsersWithRole(recvrole, activeOnly=not force)
        # get users
        if recvids:
            if isinstance(recvids, str):
                recvids = ConvertToList(recvids)
            for user in userdb.GetUserInfos(recvids+recvids2, ["name", "email", "title"], activeOnly=not force):
                if user and user["email"] != "":
                    if force or user.get("notify", 1):
                        recvList.append([user["email"], user["title"]])
        return recvList

