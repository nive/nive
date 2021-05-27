
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
        self.fail(FormatConfTestFailure(r))


    def test_tool(self):
        sendMail(configuration,None)
        
        
class SendMailTest2_db(__local.DefaultTestCase):

    def setUp(self):
        self._loadApp()
        self.app.Register(configuration)
        logging.basicConfig()
    
    def tearDown(self):
        self._closeApp(True)


    def test_tool(self):
        t = self.app.GetTool("sendMail")
        self.assertTrue(t)

    
    def test_toolrun1(self):
        t = self.app.GetTool("sendMail")
        self.assertTrue(t)
        try:
            r = t()
        except ConfigurationError:
            pass


    def test_toolrun2(self):
        t = self.app.GetTool("sendMail")
        self.assertTrue(t)
        try:
            r = t(recvmails=[("test@aaaaaaaa.com", "No name")], title="Testmail", body="body mail")
        except ConfigurationError:
            pass


    def test_toolrundebug(self):
        t = self.app.GetTool("sendMail")
        self.assertTrue(t)
        try:
            r = t(debug=1, recvmails=[("test@aaaaaaaa.com", "No name")], title="Testmail", body="body mail")
        except ConfigurationError:
            pass


    def test_date(self):
        t = self.app.GetTool("sendMail")
        date = t._FormatDate()
        self.assertTrue(date)


    def test_mailstr(self):
        t = self.app.GetTool("sendMail")
        self.assertTrue(t._GetMailStr("aaa@ddd.aa")=="aaa@ddd.aa")
        self.assertEqual(t._GetMailStr(("aaa@ddd.aa","ä a")), '"=?utf-8?q?=C3=A4_a?=" <aaa@ddd.aa>')
        self.assertTrue(t._GetMailStr(("aaa@ddd.aa",))=="aaa@ddd.aa")


    def test_message(self):
        t = self.app.GetTool("sendMail")
        values = dict(contentType="text/html;charset=utf-8",
                      body="aaaaa",
                      fromName="uuuu",
                      fromMail="uuu@aaa.dd",
                      to=["ooo", "ggg"],
                      cc=["ooo", "ggg"],
                      bcc=["ooo", "ggg"],
                      sender="mmmm",
                      replyTo="uoah",
                      subject="My mail")
        m = t._PrepareMessage(**values)
        self.assertTrue(str(m))

        values = dict(contentType="text/html;charset=utf-8",
                      body="aaaaa",
                      fromMail="uuu@aaa.dd",
                      to="ooo",
                      cc="ooo",
                      bcc="ooo",
                      subject="My mail")
        m = t._PrepareMessage(**values)
        self.assertTrue(str(m))
