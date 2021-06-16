# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import re
import iso8601
import os, tempfile, json
import datetime
from mimetypes import guess_type, guess_extension
from operator import itemgetter, attrgetter

from .path import DvPath


def MakeListItems(items):
    """
    Turns a list into listItems used by form fields. Each item in the list is
    converted into a dict. e.g. ``("a","b","c")`` or ``(("a","Name a"),("b","Name b"),("c","Name c"))``

    :param items: list of items
    :return: listItems
    """
    li = []
    for i in items:
        if isinstance(i,str):
            li.append(dict(id=i, name=i))
        elif isinstance(i,(list,tuple)):
            li.append(dict(id=i[0], name=i[1]))
        else:
            i = str(i)
            li.append(dict(id=i, name=i))
    return li

def ConvertHTMLToText(html, removeReST=True, url=""):
    # requires bs4 or html2text module
    # disabled removeReST
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()
    except ImportError:
        pass
    try:
        import html2text
        return html2text.html2text(html, url)
    except ImportError:
        return html


def ConvertToDateTime(date):
    if isinstance(date, datetime.datetime):
        return date
    elif isinstance(date, datetime.date):
        return  datetime.datetime(year=date.year, month=date.month, day=date.day)
    elif isinstance(date, float):
        return datetime.datetime.fromtimestamp(date)
    elif not date:
        return None
    try:
        return iso8601.parse_date(date, default_timezone=None)
    except (iso8601.ParseError, TypeError) as e:
        pass
    # try other string format versions
    try: # 2011-12-23
        return datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        pass
    try: # 2011/12/23
        return datetime.datetime.strptime(date, "%Y/%m/%d")
    except ValueError:
        pass
    try: # 2011/12/23 13:22
        return datetime.datetime.strptime(date, "%Y/%m/%d %H:%M")
    except ValueError:
        pass
    try: # 2011/12/23 13:22:11
        return datetime.datetime.strptime(date, "%Y/%m/%d %H:%M:%S")
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(date, "%d.%m.%Y %H:%M")
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(date, "%d.%m.%Y %H:%M:%S")
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(date, "%d.%m.%Y")
    except ValueError:
        pass


def CutText(text, textlen, cutchars=" ;:,.\r\n", postfix=" ..."):
    """
    For text preview. cut the text at the last found char in cutchars.
    """
    if len(text)<textlen:
        return text
    pos = len(text)-1
    for c in cutchars:
        p = text.find(c, textlen)
        if p!=-1 and p<pos:
            pos=p
    return text[:pos] + postfix


def FormatBytesForDisplay(size):
    """Return the size of a file or directory formatted for display."""
    if size in (None,-1,0):
        return ""
    if size == 1:
        return "1 byte"
    for factor, suffix in ((1<<30, "GB"),(1<<20, "MB"),(1<<10, "kB"),(1, "bytes")):
        if size >= factor:
            break
    if factor != 1:
        return "%0.1f %s" % (float(size) / factor, suffix)
    return "%d %s" % (size / factor, suffix)

def FmtSeconds(seconds):
    # Format seconds for display
    #[$] seconds: seconds to convert
    if seconds is None: return '-' * 5
    if seconds == -1: return '-'

    minutesSingular = '%d minute '
    minutesPlural = '%d minutes '
    hoursSingular = '%d hour '
    hoursPlural = '%d hours '

    k = 60
    if (seconds > k):
        t2 = seconds / k
        if (t2 > k):
            t3 = t2 / k
            s = ""
            if t3 == 1:
                s += hoursSingular % t3
            else:
                s += hoursPlural % t3
            m = t2%k
            if m==1:
                s += minutesSingular % m
            else:
                s += minutesPlural % m
            return s
        else:
            if t2 == 1:
                return minutesSingular % t2
            return minutesPlural % t2
    else:
        return '%d seconds' % seconds


def GetMimeTypeExtension(extension):
    if extension.find(".") != -1:
        extension = DvPath(extension).GetExtension()
    # custom and uncommon
    if extension == "fla":          return "application/flash"
    # standard
    elif extension == "html":       return "text/html"
    elif extension == "txt":        return "text/plain"
    elif extension == "dtml":       return "text/html"
    elif extension == "jpg":        return "image/jpeg"
    elif extension == "gif":        return "image/gif"
    elif extension == "png":        return "image/png"
    elif extension == "jpeg":       return "image/jpeg"
    elif extension == "psd":        return "image/psd"
    elif extension == "pdf":        return "application/pdf"
    elif extension == "md":         return "text/markdown"
    elif extension == "js":         return "application/javascript"
    elif extension == "json":       return "application/json"
    elif extension == "yaml":       return "text/yaml"
    elif extension == "rst":        return "text/restructured-text"
    elif extension == "rtf":        return "text/rtf"
    elif extension == "swf":        return "application/x-shockwave-flash"
    elif extension == "flv":        return "application/x-shockwave-flash"
    elif extension == "dcr":        return "application/x-director"
    elif extension == "doc":        return "application/msword"
    elif extension == "xls":        return "application/vnd.ms-excel"
    elif extension == "ppt":        return "application/vnd.ms-powerpoint"
    elif extension == "mpp":        return "application/vnd.ms-project"
    elif extension == "gz":         return "application/gz"
    elif extension == "dat":        return "application/octet-stream"
    elif extension == "flv":        return "video/flv"
    elif extension == "ogv":        return "video/ogg"
    elif extension == "webm":       return "video/webm"
    elif extension == "mp4":        return "video/mp4"
    elif extension == "mp3":        return "audio/mp3"
    elif extension == "ogg":        return "audio/ogg"
    e = guess_type("x." + extension)
    if e[0]:                return e[0]
    return ""

def GetExtensionMimeType(mime):
    if ";" in mime:
        mime = mime.split(";")[0]
    # custom and uncommeon
    if mime == "application/flash":  return "fla"
    # standard
    elif mime == "text/html":        return "html"
    elif mime == "text/plain":       return "txt"
    elif mime == "text/html":        return "dtml"
    elif mime == "image/jpeg":       return "jpg"
    elif mime == "image/gif":        return "gif"
    elif mime == "image/png":        return "png"
    elif mime == "image/jpeg":       return "jpeg"
    elif mime == "image/psd":        return "psd"
    elif mime == "text/markdown":                    return "md"
    elif mime == "text/restructured-text":           return "rst"
    elif mime == "text/rtf":                         return "rtf"
    elif mime == "text/yaml":                        return "yaml"
    elif mime == "application/javascript":           return "js"
    elif mime == "application/json":                 return "json"
    elif mime == "application/pdf":                  return "pdf"
    elif mime == "application/x-shockwave-flash":    return "swf"
    elif mime == "application/x-director":           return "dcr"
    elif mime == "application/msword":               return "doc"
    elif mime == "application/vnd.ms-excel":         return "xls"
    elif mime == "application/vnd.ms-word":          return "doc"
    elif mime == "application/vnd.ms-powerpoint":    return "ppt"
    elif mime == "application/vnd.ms-project":       return "mpp"
    elif mime == "application/octet-stream":         return "dat"
    elif mime == "video/flv":        return "flv"
    elif mime == "video/ogg":        return "ogv"
    elif mime == "video/webm":       return "webm"
    elif mime == "video/mp4":        return "mp4"
    elif mime == "audio/mp3":        return "mp3"
    elif mime == "audio/ogg":        return "ogg"

    m = guess_extension(mime)
    if m:                            return m[1:]
    return ""


def TidyHtml(data, options=None):
    """
    clean up html by calling tidy
    """
    if not options:
        options = { 'output-xhtml'       : '1',
                    'add-xml-decl'       : '1',
                    'indent'             : 'auto',
                    'tidy-mark'          : '0',
                    'char-encoding'      : 'utf8',
                    'clean'              : '0',
                    'drop-font-tags'     : '1',
                    'enclose-block-text' : '0',
                    'logical-emphasis'   : '1',
                    'word-2000'          : '1',
                    'wrap'               : '65',
                    'write-back'         : '0'}

    cmds = ""
    for k in list(options.keys()):
        cmds += " --"+k+" "+options[k]

    # write file
    file, filename = tempfile.mkstemp(suffix='.html', prefix='tidy')
    os.write(file, data)
    os.close(file)

    # call tidy
    out = filename + "_tidy"
    cmd = """%(cmds)s -o %(out)s %(file)s""" %{"cmds": cmds, "out": out, "file": filename}

    s = os.popen("tidy " + cmd, "r")
    r = ""
    while 1:
        d = s.readline()
        if not d or d == ".\n" or d == ".\r":
            break
        r += d

    # delete file
    try:
        os.remove(filename)
    except:
        pass

    # return output
    try:
        file = open(out, "r+b")
        data2 = file.read()
        file.close()
        os.remove(out)
    except:
        return data
    return data2


def SortConfigurationList(values, sort, ascending=True):
    """
    Sorts the dictionary list `values` by attribute or key `sort`. This works for definitions.Conf() objects 
    and simple dictionaries. 
    Results can be ordered ascending or descending.
    """
    if not sort:
        return values
    try:
        values = sorted(values, key=attrgetter(sort))   
    except AttributeError:
        values = sorted(values, key=itemgetter(sort))   
    if not ascending:
        values.reverse()
    return values


# failsafe type conversion ---------------------------------------------------------------------------------------

def ConvertToStr(data, sep="\n"):
    if isinstance(data, (list, tuple)):
        return ConvertListToStr(data)
    elif isinstance(data, dict):
        v = []
        for key, value in list(data.items()):
            v.append("%s: %s"%(str(key), ConvertToStr(value, sep)))
        return sep.join(v)
    return str(data)

def ConvertToBool(data, raiseExcp = False):
    try:
        return int(data)
    except:
        if isinstance(data, str):
            if data.lower() in ("true", "yes", "checked", "ja", "qui", "si"):
                return True
            if data.lower() in ("false", "no", "nein", "non"):
                return False
        if raiseExcp:
            raise
        return False

def ConvertToInt(data, raiseExcp = False):
    try:
        return int(data)
    except:
        try:
            if ConvertToBool(data, raiseExcp):
                return 1
            else:
                return 0
        except:
            if raiseExcp:
                raise
        return 0

def ConvertToFloat(data, raiseExcp = False):
    try:
        return float(data)
    except:
        if ConvertToBool(data, raiseExcp):
            return 1.0
        else:
            return 0.0
        if raiseExcp:
            raise 
        return 0.0

def ConvertToLong(data, raiseExcp = False):
    try:
        return int(data)
    except:
        try:
            if ConvertToBool(data, raiseExcp):
                return 1
            else:
                return 0
        except:
            if raiseExcp:
                raise
        return 0

def ConvertToList(data, raiseExcp = False):
    """
    converts a string to list.
    the list items can be seperated by "," or "\n"
    """
    try:
        if not data:
            return []
        if isinstance(data, (list,tuple)):
            return data
        data = data.strip()
        if not len(data):
            return []
        if data[0] in ("[", "("):
            data = data[1:-1]

        sep = ","
        if data.find("\n") != -1:
            sep = "\n"

        result = []
        l = data.split(sep)
        for value in l:
            value = value.strip()
            if not len(value):
                continue
            if value[0] in ("'", "\""):
                value = value[1:-1]
            result.append(value)
        return result
    except:
        if raiseExcp:
            raise 
        return []

def ConvertToNumberList(data, raiseExcp = False):
    try:
        l = ConvertToList(data, raiseExcp)
        for i in range(len(l)):
            l[i] = ConvertToLong(l[i], raiseExcp)
        return l
    except:
        if raiseExcp:
            raise 
        return []


def ConvertListToStr(values, sep = ", ", textMarker = "", keepType = False):
    """
    converts a python list to string. .
    the list items are seperated by ",". list items are converted to string
    """
    if not values:
        return ""
    if isinstance(values, str):
        return "%s%s%s" % (textMarker, values, textMarker)
    s = []
    for v in values:
        if textMarker != "":
            tm = textMarker
            if keepType:
                if isinstance(v, (int, float)):
                    tm = ""
            s.append("%s%s%s" % (textMarker, str(v), textMarker))
        else:
            s.append(str(v))
    return sep.join(s)


def ConvertDictToStr(values, sep = "\n"):
    """
    converts a python dictionary to key list string.
    the list items are seperated by ",". list items are converted to string
    
    ::
        key1: value1
        key2: value2
        
    result string
    """
    s = ["%s: %s" % (key, ConvertToStr(value, sep)) for key, value in list(values.items())]
    return sep.join(s)


# Logging --------------------------------------------------------------------------


def DUMP(data, path = "dump.txt", addTime=False):
    if addTime:
        date = datetime.datetime.now()
        value = "\r\n\r\n" + date.strftime("%Y-%m-%d %H:%M:%S") + "\r\n" + str(data)
    else:
        value = "\r\n\r\n" + str(data)
    file = open(path, "ab+")
    file.write(value)
    file.close()

def STACKF(t=0, label = "", limit = 15, path = "_stackf.txt", name=""):
    import time
    import traceback
    n = time.time() - t
    date = datetime.datetime.now()
    h = "%s: %f (%s)" % (date.strftime("%Y-%m-%d %H:%M:%S"),n,name)
    if limit<2:
        DUMP("%s\r\n%s\r\n" % (h, label), path)
        return
    import io
    s = io.StringIO()
    traceback.print_stack(limit=limit, file=s)
    DUMP("%s\r\n%s\r\n%s" % (h, label, s.getvalue()), path)


