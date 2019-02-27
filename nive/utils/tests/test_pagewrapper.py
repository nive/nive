import unittest
import logging
import time

from nive.definitions import Conf
from nive.utils import pageWrapper



pwfilter = (
  Conf(context=pageWrapper.string_replacer,
       orig="http://192.168.0.1:8080/start/",
       new="http://www.start.de/"),
  Conf(context=pageWrapper.content_splitter,
      start="<!-- content start -->",
      end="<!-- content end -->")
)

pwfilter2 = (
    Conf(context=pageWrapper.replace_request_var,
         marker="title</title>",
         key="wrapper_page_title",
         placeholder=" %s</title>",
         default=" Title"
    ),
)


class FakeLoad(pageWrapper.PageWrapper):
    def _Load(self):
        # return values: HTTP Status, Reason, Message, Data, Time
        try:
            self._err = ""
            data = """<html>
            <title></title>
            <body>
      <!-- content start -->

        CONTENT

      <!-- content end -->
            </body>
            </html>"""

            self._lastUpdate = time.time()
            data = self.FilterOnLoad(data)
            if self.cache:
                self._Cache(data)
            return data
        except Exception as e:
            self._err = str(e)
            self.log.exception("Load failed: " + self.url)
            return self._parts


class WrapperTests(unittest.TestCase):


    def test_wrapper(self):
        logging.basicConfig()
        w = FakeLoad(url="", loadFilter=pwfilter, viewFilter=pwfilter2)

        self.assertTrue(len(w.Parts(view={"wrapper_page_title": "aaaaaaaaaa"}) )==3)
        self.assertTrue(w.Header(view={"wrapper_page_title": "aaaaaaaaaa"}))
        self.assertTrue(w.Footer(view={"wrapper_page_title": "aaaaaaaaaa"}))

        # reuse without reload
        tt = w._lastUpdate
        self.assertTrue(len(w.Parts(view={"wrapper_page_title": "aaaaaaaaaa"}) )==3)
        self.assertTrue(w.Header(view={"wrapper_page_title": "aaaaaaaaaa"}))
        self.assertTrue(w.Footer(view={"wrapper_page_title": "aaaaaaaaaa"}))
        self.assertTrue(tt == w._lastUpdate)
