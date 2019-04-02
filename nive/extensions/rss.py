

try:
    from PyRSS2Gen import PyRSS2Gen
except:
    pass
from datetime import datetime

from nive.definitions import Conf, ViewConf
from nive.views import BaseView


class RSSView(BaseView):

    def rss(self):
        """
        default rss publishing function
        """
        feedData = dict(link=self.Url())
        feed = self.context.RssSearch(feedData)
        return self.SendResponse(feed, mime="application/rss+xml")


    def RssSearch(self, feedData, view=None):
        """
        generate the folder contents as rss feed

        opotions:
        rssTypes = list. default: all non-folders. list of pool_type to be published
        count = number. default:30. number of entries
        condition = default none. select condition.
        operators = default none.
        itemFieldMap = dictionary. default:{"title": meta.title, "link": item.GetURL(), "description": data.description, "pubDate": pool_change}.
                       a mapping table of fields to generate the feeds.
        includeSubfolder = bool. default: true

        add in tmpl header: <link rel="alternate" type="application/rss+xml"  href="rss" title="title">


        :param feedData:
        :param view: required if item link is not set
        :return:
        """

        conf = self.context.configuration.rss
        root = self.context.root

        parameter = conf.parameter.copy()
        if conf.container and not "pool_unitref" in parameter:
            parameter["pool_unitref"] = self.context.id

        # search
        if not conf.pool_type:
            items = root.search.Search(parameter, fields=conf.fields, operators=conf.operators, sort=conf.sort, max=conf.count)
        else:
            items = root.search.SearchType(conf.pool_type, parameter, fields=conf.fields, operators=conf.operators, sort=conf.sort, max=conf.count)

        return self.RssXml(items, feedData, conf, view)


    def RssXml(self, items, feedData, conf, view):
        """

        :param items:
        :param feedData:
        :param conf:
        :param view:
        :return:
        """
        context = self.context
        if not "title" in feedData:
            feedData["title" ] = context.meta.title
        if not "description" in feedData:
            feedData["description" ] = context.data.get("description") or conf.description
        if not "inputEncoding" in feedData and conf.inputEncoding:
            feedData["inputEncoding" ] = conf.inputEncoding

        feed = RssWriter(**feedData)
        itemFieldMap = conf.itemFieldMap
        root = self.context.root
        for i in items["items"]:
            item = {}
            if "link" in itemFieldMap:
                item["link"] = i[itemFieldMap["link"]]
            else:
                item["link"] = view.Url(root.LookupObj(i["id"], preload="skip"))
            item["guid"] = item["link"]
            if "pubDate" in itemFieldMap:
                item["pubDate"] = renderGMT(i[itemFieldMap["pubDate"]], "0200")
            for k in itemFieldMap:
                if k in ("link", "pubDate"):
                    continue
                item[k] = i[itemFieldMap[k]]

            feed.AddItem(**item)

        data = feed.Publish(feedData)
        data = data.replace("&lt;", "<")
        data = data.replace("&gt;", ">")
        return data



class RssWriter(object):
    """
    Generates rss 2 feeds from dictionary lists (Uses PyRSS2Gen module)

    Feed:
        title = "The title of the feed"
        link = URL
        description = "long description of the feed"
        lastBuildDate = default: now

      extended:
        language = None
        copyright = None
        managingEditor = None
        webMaster = None
        pubDate = None  		# a datetime, *in* *GMT*

        categories = None 		# list of strings or Category
        generator = _generator_name
        docs = "http://blogs.law.harvard.edu/tech/rss"
        cloud = (domain, port, path, registerProcedure, protocol) default:None			# a Cloud
        ttl = None	  			# integer number of minutes

        image = (url, title, link, width = None, height = None, description = None) default:None			# an Image
        rating = string default:None			# a string; I don't know how it's used
        textInput = (title, description, name, link) default:None 		# a special element TextInput
        skipHours = [12,13,14] default:None 		# a SkipHours with a list of integers
        skipDays = ["Sat", "Sun"] default:None  		# a SkipDays with a list of strings
        inputEncoding = default: utf-8

    Items:
        title = "The title of the item"
        link = URL
        description = "long description of the item"
        guid = (baseUrl, itemPath)
        pubDate = default: now

      extended:
        author = None	  	# email address as string
        categories = None  	# list of string or Category
        comments = None  	# url as string
        enclosure = (url, length, type) default:None 	# an Enclosure
        guid = None			# a unique string
        source = None  		# a Source
    """

    _generator_name = "rss.2"
    _input_encoding = "utf-8"
    _xmlns = {"xmlns:atom": "http://www.w3.org/2005/Atom"}


    def __init__(self, title, link, description, lastBuildDate = None, **kw):
        self.Set(title, link, description, lastBuildDate = None, **kw)


    def Set(self, title, link, description, lastBuildDate = None, **kw):
        """
        set feed content
        """
        self.inputEncoding = kw.get("inputEncoding", self._input_encoding)
        if not lastBuildDate:
            lastBuildDate = datetime.now()

        categories = kw.get("categories")
        if categories:
            if not isinstance(categories, (list, tuple)):
                categories = PyRSS2Gen.Category(*categories)
        cloud = kw.get("cloud")
        if cloud:
            cloud = PyRSS2Gen.Cloud(*cloud)
        image = kw.get("image")
        if image:
            image = PyRSS2Gen.Image(*image)
        textInput = kw.get("textInput")
        if textInput:
            textInput = PyRSS2Gen.TextInput(*textInput)
        skipHours = kw.get("skipHours")
        if skipHours:
            skipHours = PyRSS2Gen.SkipHours(*skipHours)
        skipDays = kw.get("skipDays")
        if skipDays:
            skipDays = PyRSS2Gen.SkipDays(*skipDays)

        self.feed = PyRSS2Gen.RSS2(title,
                                   link,
                                   description,

                                   language = kw.get("language"),
                                   copyright = kw.get("copyright"),
                                   managingEditor = kw.get("managingEditor"),
                                   webMaster = kw.get("webMaster"),
                                   pubDate = kw.get("pubDate"),
                                   lastBuildDate = lastBuildDate,

                                   categories = categories,
                                   cloud = cloud,
                                   image = image,
                                   rating = kw.get("rating"),
                                   textInput = textInput,
                                   skipHours = skipHours,
                                   skipDays = skipDays,
                                   ttl = kw.get("ttl"),
                                   inputEncoding = self.inputEncoding,

                                   generator = self._generator_name,
                                   docs = "http://blogs.law.harvard.edu/tech/rss"
                                   )
        self.feed.rss_attrs.update(self._xmlns)


    def AddItem(self, title, link, **kw):
        """
        add an item to the feed
        """
        categories = kw.get("categories")
        if categories:
            if type(categories) == type(""):
                categories = [categories]
        #categories = PyRSS2Gen.Category(*categories)

        enclosure = kw.get("enclosure")
        #if enclosure:
        #	if type(enclosure) == type(""):
        #		enclosure = [enclosure]
        #	enclosure = PyRSS2Gen.Enclosure(*enclosure)

        guid = kw.get("guid")
        #if guid:
        #	if type(guid) == type(""):
        #		guid = [guid]
        #	guid = PyRSS2Gen.Guid(*guid)

        source = kw.get("source")
        #if source:
        #	if type(source) == type(""):
        #		source = [source]
        #	source = PyRSS2Gen.Source(*source)
        content = kw.get("content")

        item = PyRSS2Gen.RSSItem(title,
                                 link,
                                 description = kw.get("description"),
                                 author = kw.get("author"),
                                 categories = categories,
                                 comments = kw.get("comments"),
                                 enclosure = enclosure,
                                 guid = guid,
                                 pubDate = kw.get("pubDate"),
                                 source = source,
                                 content = content,
                                 inputEncoding = self.inputEncoding
                                 )

        self.feed.items.append(item)


    def Publish(self, encoding="utf-8"):
        """
        Publish RSS stream. returns stream as string
        """
        return self.feed.to_xml(encoding)


    def PublishFile(self, filename, encoding="utf-8"):
        """
        Publish RSS stream as file.
        """
        with open(filename, "rw") as file:
            self.feed.write_xml(file, encoding)
            file.close()
        return



def renderGMT(dt, offset=None):
    if offset:
        offset = "+" + offset
    return "%s, %02d %s %04d %02d:%02d:%02d %s" % (
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()],
        dt.day,
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][dt.month - 1],
        dt.year, dt.hour, dt.min, dt.sec, offset)



# include as configuration.rss in the contexts configuration and fill settings as required
settings = Conf(
    pool_type = None,
    operators = dict(),
    parameter = dict(pool_state=1),
    container = True,
    itemFieldMap = dict(title="title", pubDate="pool_change"),
    sort = "pool_change",
    language = "de",
    author = "",
    inputEncoding = ""
)

view_configuration = ViewConf(
    id = "rss_view_conf",
    attr = "rss",
    name = "rss",
    context = None, # required
    view = RSSView,
    permission = None
)

