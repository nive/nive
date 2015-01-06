
import time
import unittest
import logging
from smtplib import SMTPServerDisconnected

from nive.definitions import *
from nive.tools.sendMail import sendMail, configuration

from nive.tests import __local


from nive.helper import FormatConfTestFailure



# -----------------------------------------------------------------

class SendMailTest1(unittest.TestCase):


    def test_conf1(self):
        r=configuration.test()
        if not r:
            return
        print FormatConfTestFailure(r)
        self.assert_(False, "Configuration Error")

    def test_tool(self):
        sendMail(configuration,None)
        
        
class SendMailTest2_db(__local.DefaultTestCase):

    def setUp(self):
        self._loadApp()
        self.app.Register(configuration)
        logging.basicConfig()
    
    def tearDown(self):
        self.app.Close()


    def test_tool(self):
        t = self.app.GetTool("sendMail")
        self.assert_(t)

    
    def test_toolrun1(self):
        t = self.app.GetTool("sendMail")
        self.assert_(t)
        try:
            r,v = t()
        except ConfigurationError:
            pass


    def test_toolrun2(self):
        t = self.app.GetTool("sendMail")
        self.assert_(t)
        try:
            r,v = t(recvmails=[("test@aaaaaaaa.com", "No name")], title="Testmail", body="body mail")
        except ConfigurationError:
            pass


    def test_toolrundebug(self):
        t = self.app.GetTool("sendMail")
        self.assert_(t)
        try:
            r,v = t(debug=1, recvmails=[("test@aaaaaaaa.com", "No name")], title="Testmail", body="body mail")
        except ConfigurationError:
            pass


    def test_date(self):
        t = self.app.GetTool("sendMail")
        date = t._FormatDate()
        self.assert_(date)


    def test_mailstr(self):
        t = self.app.GetTool("sendMail")
        self.assert_(t._GetMailStr("aaa@ddd.aa")=="aaa@ddd.aa")
        self.assert_(t._GetMailStr(("aaa@ddd.aa","a a"))=='"=?utf-8?q?a_a?=" <aaa@ddd.aa>', t._GetMailStr(("aaa@ddd.aa","a a")))
        self.assert_(t._GetMailStr(("aaa@ddd.aa",))=="aaa@ddd.aa")


    def test_message(self):
        t = self.app.GetTool("sendMail")
        values = dict(contentType="text/html;charset=utf-8",
                      body=u"aaaaa",
                      fromName=u"uuuuu",
                      fromMail=u"uuu@aaa.dd",
                      to=[u"ooo", u"ggg"],
                      cc=[u"ooo", u"ggg"],
                      bcc=[u"ooo", u"ggg"],
                      sender=u"mmmm",
                      replyTo=u"uoah",
                      subject=u"My mail")
        m = t._PrepareMessage(**values)
        self.assert_(str(m))

        values = dict(contentType="text/html;charset=utf-8",
                      body=u"aaaaa",
                      fromMail=u"uuu@aaa.dd",
                      to=u"ooo",
                      cc=u"ooo",
                      bcc=u"ooo",
                      subject=u"My mail")
        m = t._PrepareMessage(**values)
        self.assert_(str(m))
