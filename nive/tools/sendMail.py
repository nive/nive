# -*- coding: utf-8 -*-

# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Receivers are looked up by user ids or roles. Sender name, receiver, title, and body can be set as values by call.

mails as list with [(email, name),...] ("name@mail.com","Name")
"""

import types, string
import time
import logging

from smtplib import SMTP
from smtplib import SMTPServerDisconnected, SMTPRecipientsRefused, SMTPHeloError, SMTPSenderRefused, SMTPDataError, SMTPException

from email.message import Message
from email.header import Header

from nive.utils.utils import ConvertToList
from nive.definitions import ConfigurationError
from nive.definitions import ToolConf, FieldConf
from nive.tool import Tool
from nive.i18n import _

configuration = ToolConf(
    id = "sendMail",
    context = "nive.tools.sendMail.sendMail",
    name = _(u"Send mails to registered users"),
    description = __doc__,
    apply = None,
    data = (
        FieldConf(id="host",    name=_(u"SMTP host"),       datatype="string",       required=1,     readonly=1, default=u"",    description=u""),
        FieldConf(id="port",    name=_(u"SMTP port"),       datatype="number",       required=1,     readonly=1, default=21,     description=u""),
        FieldConf(id="sender",  name=_(u"SMTP sender mail"),datatype="email",        required=1,     readonly=1, default=u"",    description=u""),
        FieldConf(id="user",    name=_(u"SMTP user"),       datatype="string",       required=0,     readonly=1, default=u"",    description=u""),
        FieldConf(id="pass_",   name=_(u"SMTP password"),   datatype="password",     required=0,     readonly=1, default=u"",    description=u""),

        FieldConf(id="fromName",  name=_(u"Sender name"),   datatype="string",       required=0,     readonly=0, default=u"",    description=u""),
        FieldConf(id="fromMail",  name=_(u"Sender mail"),   datatype="string",       required=0,     readonly=0, default=u"",    description=u""),
        FieldConf(id="replyTo",   name=_(u"Reply to"),      datatype="string",       required=0,     readonly=0, default=u"",    description=u""),
        FieldConf(id="recvrole",  name=_(u"Receiver role"),    datatype="string",    required=1,     readonly=0, default=u"",    description=u""),
        FieldConf(id="recvids",   name=_(u"Receiver User IDs"),datatype="string",    required=1,     readonly=0, default=u"",    description=u""),
        FieldConf(id="recvmails", name=_(u"Receiver Mail"),    datatype="string",    required=1,     readonly=0, default=u"",    description=u""),
        FieldConf(id="force",     name=_(u"Ignore notify settings"),datatype="bool", required=0,     readonly=0, default=0,      description=u""),
        FieldConf(id="cc",        name=_(u"CC"),            datatype="string",       required=0,     readonly=0, default=u"",    description=u""),
        FieldConf(id="bcc",       name=_(u"BCC"),           datatype="string",       required=0,     readonly=0, default=u"",    description=u""),

        FieldConf(id="title", name=_(u"Title"),             datatype="string",       required=1,     readonly=0, default=u"",    description=u""),
        FieldConf(id="body",  name=_(u"Text"),              datatype="htext",        required=0,     readonly=0, default=u"",    description=u""),
        FieldConf(id="html",  name=_(u"Html format"),       datatype="bool",         required=0,     readonly=0, default=1,      description=u""),
        FieldConf(id="utf8",  name=_(u"UTF-8 encoding"),    datatype="bool",         required=0,     readonly=0, default=1,      description=u""),
        FieldConf(id="ssl",   name=_(u"Use SSL"),           datatype="bool",         required=0,     readonly=0, default=1,      description=u""),
        FieldConf(id="maillog",  name=_(u"Log mails"),      datatype="string",       required=0,     readonly=0, default=u"",    description=u""),
        FieldConf(id="showToListInHeader",name=_(u"Show all receivers in header"), datatype="bool", required=0, readonly=0, default=0,    description=u""),

        FieldConf(id="debug", name=_(u"Debug mail receiver"),datatype="email",       required=0,     readonly=0, default=u"",    description=_(u"If not empty all mails are sent to this address. The original mail receivers are ignored.")),
    ),
    mimetype = "text/html"
    #modules = WidgetConf(name=_(u"Root"),      viewmapper="rootsettings",id="admin.rootsettings",sort=1100,   apply=(IApplication,), widgetType=IAdminWidgetConf),
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

        # lookup receivers
        # `recvs` is the raw list of mails in the form of `(mail, name)` tuples
        recvs = []
        if recvmails:
            if isinstance(recvmails, basestring):
                recvs.append((recvmails, u""))
            else:
                recvs.extend(recvmails)
        if recvids or recvrole:
            recvs.extend(self._GetRecv(recvids, recvrole, force, self.app))

        if len(recvs) == 0:
            self.stream.write(_(u"No receiver for the e-mail! Aborting."))
            return 0

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
            senderMail = u""

        if html:
            contentType = u"text/html"
        else:
            contentType = u"text/plain"
        if utf8:
            contentType += u"; charset=utf-8"

        if debug:
            mails_original = u"\r\n<br>".join([self._GetMailStr(r) for r in recvs])
            body += u"""\r\n<br><br>\r\nDEBUG\r\n<br> Original receiver: \r\n<br>""" + mails_original
            # in debug mode use default receiver mail as receiving address for all mails
            recvs = [(debug, u"")]

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
            sender=senderMail,
            replyTo=replyTo)

        if not host:
            raise ConfigurationError, "Empty mail host"
        mailer = SMTP(host, port)
        try:
            mailer.ehlo()
            if ssl:
                mailer.starttls()
                mailer.ehlo()
        except (SMTPServerDisconnected, SMTPHeloError, SMTPException), e:
            log.error(" %s", repr(e))
            return False

        if user:
            mailer.login(user, str(pass_))

        result = 1
        log.info(u"send to -> %s", u", ".join([r[0] for r in recvs]))
        for recv in recvs:
            try:
                if not showToListInHeader:
                    del message["To"]
                    message["To"] = self._GetMailStr(recv)

                info = mailer.sendmail(fromMail, recv[0], message.as_string(unixfrom=False))
                self.stream.write(recv[0] + u" ok, ")
                log.debug(u"%s - %s - %s" % (recv[0], title, str(info)))

            except (SMTPSenderRefused, SMTPDataError), e:
                result = 0
                log.error("%s", repr(e))
                log.error(u"->  %s", u"%s - %s - %s" % (recv[0], recv[1], title))
                self.stream.write(str(e))

            except SMTPRecipientsRefused, e:
                result = 0
                log.error("%s", repr(e))
                self.stream.write(str(e))

            except (SMTPServerDisconnected,), e:
                result = 0
                log.error("%s", repr(e))
                self.stream.write(str(e))
                break

        mailer.quit()
        return result


    def _PrepareMessage(self, **kw):
        contentType = kw.get("contentType")
        charset = "utf-8"
        if contentType and contentType.find("charset=")!=-1:
            charset = contentType.split("charset=")[1]

        message = Message()
        message.set_charset(charset)
        message.set_payload(kw.get("body"), charset)
        message["Date"] = self._FormatDate()
        message["Subject"] = Header(kw.get("title"))
        try:
            del message["Content-Type"]
        except:
            pass
        message["Content-Type"] = contentType
        try:
            del message["Content-Transfer-Encoding"]
        except:
            pass
        message["Content-Transfer-Encoding"] = "8bit"

        fromName = kw.get("fromName")
        fromMail = kw.get("fromMail")
        message["From"] = self._GetMailStr((fromMail, fromName))

        to = kw.get("to")
        if isinstance(to, (list,tuple)):
            to = u", ".join(to)
        message["To"] = to

        cc = kw.get("cc")
        if cc:
            if isinstance(cc, (list,tuple)):
                cc = u", ".join(cc)
            message["Cc"] = cc

        bcc = kw.get("bcc")
        if bcc:
            if isinstance(bcc, (list,tuple)):
                bcc = u", ".join(bcc)
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
        weekdayname = [u'Mon', u'Tue', u'Wed', u'Thu', u'Fri', u'Sat', u'Sun']
        monthname = [None, u'Jan', u'Feb', u'Mar', u'Apr', u'May', u'Jun', u'Jul', u'Aug', u'Sep', u'Oct', u'Nov', u'Dec']
        now = time.time()
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(now)
        s = u"%s, %02d %3s %4d %02d:%02d:%02d GMT" % (weekdayname[wd], day, monthname[month], year, hh, mm, ss)
        return s


    def _GetMailStr(self, mail):
        if isinstance(mail, basestring):
            return mail
        if len(mail) > 1 and mail[1]:
            return u'"%s" <%s>' % (str(Header(mail[1], "utf-8")), mail[0])
        return mail[0]
        

    def _GetRecv(self, recvids, recvrole, force, app):
        userdb = app.root()
        if not hasattr(userdb, "GetUsersWithRole"):
            userdb = app.portal.userdb.GetRoot()
        recvList = []
        # check roles
        recvids2 = []
        if recvrole:
            recvids2 = userdb.GetUsersWithRole(recvrole, activeOnly=not force)
        # get users
        if recvids:
            if isinstance(recvids, basestring):
                recvids = ConvertToList(recvids)
            for user in userdb.GetUserInfos(recvids+recvids2, ["name", "email", "title"], activeOnly=not force):
                if user and user["email"] != u"":
                    if force or user.get("notify", 1):
                        recvList.append([user["email"], user["title"]])
        return recvList

