# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request

from nive.tool import Tool, ToolView
from nive.helper import FakeLocalizer
from nive.definitions import ToolConf, IApplication
from nive.definitions import ViewConf
from nive.i18n import _

from nive.utils.utils import FormatBytesForDisplay

configuration = ToolConf(
    id = "cmsstatistics",
    context = "nive.tools.cmsstatistics.cmsstatistics",
    name = _(u"CMS Statistics"),
    description = _("This function provides a short summary of elements and data contained in the website."),
    apply = (IApplication,),
    mimetype = "text/html",
    data = [],
    views = [
        ViewConf(name="", view=ToolView, attr="run", permission="system", context="nive.tools.cmsstatistics.cmsstatistics")
    ]
)


class cmsstatistics(Tool):
    """
    """

    def _Run(self, **values):

        try:
            localizer = get_localizer(get_current_request())
        except:
            localizer = FakeLocalizer()

        app = self.app
        datapool = app.db
        conn = datapool.connection
        c = conn.cursor()

        self.stream.write(u"<table class='table table-bordered'>\n")

        sql = "select count(*) from pool_meta"
        c.execute(sql)
        rec = c.fetchall()
        self.stream.write(localizer.translate(_(u"<tr><th>Elements in total</th><td>${value}</td></tr>\n", mapping={u"value": rec[0][0]})))

        sql = "select count(*) from pool_files"
        c.execute(sql)
        rec = c.fetchall()
        self.stream.write(localizer.translate(_(u"<tr><th>Physical files</th><td>${value}</td></tr>\n", mapping={u"value": rec[0][0]})))

        sql = "select sum(size) from pool_files"
        c.execute(sql)
        rec = c.fetchall()
        self.stream.write(localizer.translate(_(u"<tr><th>Physical files size</th><td>${value}</td></tr>\n", mapping={u"value": FormatBytesForDisplay(rec[0][0])})))

        for t in app.GetAllObjectConfs():
            sql = "select count(*) from pool_meta where pool_type='%s'" % t.id
            c.execute(sql)
            rec = c.fetchall()
            self.stream.write(localizer.translate(_(u"<tr><th>${name}</th><td>${value}</td></tr>\n", mapping={u"name": t.name, u"value": rec[0][0]})))
        
        self.stream.write(u"</table>\n")

        c.close()
        return 1

