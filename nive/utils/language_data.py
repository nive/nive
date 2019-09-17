#
""" -*- coding: utf-8 -*-"""

from copy import deepcopy


# default ------------------------------------------------
empty = {}
empty["code"] = ""
empty["code2"] = ""
empty["name"] = ""
empty["articles_used"] = 0 # 1=article, 2=f+m, 3=f+m+n
empty["articles"] = {}
empty["article_abbr"] = ""
empty["verb_prefix"] = ""
empty["plural"] = ""
empty["codepage"] = ""
empty["remove_chars"] = "\t\r\n"
empty["special_chars"] = ""


#[s] languages -------------------------------------------

noArticle = "keine Zuordnung"
languages = ("ger", "eng", "ita", "spa", "fra", "por", "lat", "dan", "dut", "pol", "swe", "cze", "tur", "epo",
             "rus", "fin", "gre", "rum", "afr", "ara", "alb", "amh", "arm", "aze", "bel", "ben",
             "tib", "bos", "bul", "cat", "zho", "hrv", "esp", "est", "fil", "kat", "ell", "hau", "heb",
             "hin", "hun", "isi", "ind", "jpn", "kor", "lav", "lit", "mon", "nep", "nor", "per", "pol",
             "ron", "san", "srp", "slk", "swa", "tha", "ukr", "vie")
# disabled : "grc"

# ger ---------------------------------------------------
ger = deepcopy(empty)
ger["code"] = "ger"
ger["code2"] = "de"
ger["name"] = "Deutsch"
ger["articles_used"] = 3
ger["articles"] = {"m": "der", "f": "die", "n": "das"}
ger["verb_prefix"] = ""
ger["plural"] = "s"
ger["codepage"] = "iso-8859-15"
ger["special_chars"] = "äöüÄÖÜß"

# eng ---------------------------------------------------
eng = deepcopy(empty)
eng["code"] = "eng"
eng["code2"] = "en"
eng["name"] = "English"
eng["articles_used"] = 1
eng["articles"] = {"a": "the"}
eng["verb_prefix"] = "to"
eng["plural"] = "s"
eng["codepage"] = "iso-8859-1"
eng["special_chars"] = ""

# ita ---------------------------------------------------
ita = deepcopy(empty)
ita["code"] = "ita"
ita["code2"] = "it"
ita["name"] = "Italiano"
ita["articles_used"] = 2
ita["articles"] = {"m": "il", "f": "la"}
ita["article_abbr"] = "l'"
ita["verb_prefix"] = ""
ita["plural"] = ""
ita["codepage"] = "iso-8859-15"
ita["special_chars"] = "ÀÈÉÌÒÙàèéìòù"

# spa ---------------------------------------------------
spa = deepcopy(empty)
spa["code"] = "spa"
spa["code2"] = "es"
spa["name"] = "Español"
spa["articles_used"] = 2
spa["articles"] = {"m": "el", "f": "la"}
spa["article_abbr"] = ""
spa["verb_prefix"] = ""
spa["plural"] = "s"
spa["codepage"] = "iso-8859-15"
spa["special_chars"] = "ÁÉÍÑÓÚÜáéíñóúü"


# fra ---------------------------------------------------
fra = deepcopy(empty)
fra["code"] = "fra"
fra["code2"] = "fr"
fra["name"] = "Français"
fra["articles_used"] = 2
fra["articles"] = {"m": "le", "f": "la"}
fra["article_abbr"] = "l’"
fra["verb_prefix"] = ""
fra["plural"] = ""
fra["codepage"] = "iso-8859-15"
fra["special_chars"] = "ÀÂÇÈÉÊËÎÏÔŒÙÛÜŸàâçèéêëîïôœùûüÿ"


# por ---------------------------------------------------
por = deepcopy(empty)
por["code"] = "por"
por["code2"] = "pt"
por["name"] = " Português"
por["articles_used"] = 2
por["articles"] = {"m": "o", "f": "a"}
por["article_abbr"] = ""
por["verb_prefix"] = ""
por["plural"] = ""
por["codepage"] = "iso-8859-15"
por["special_chars"] = "ÀÁÂÃÇÉÊÍÓÔÕÚÜàáâãçéêíóôõúü"


# lat ---------------------------------------------------
lat = deepcopy(empty)
lat["code"] = "lat"
lat["code2"] = "la"
lat["name"] = "Lingua Latina"
lat["articles_used"] = 0
lat["articles"] = {}
lat["article_abbr"] = ""
lat["verb_prefix"] = ""
lat["plural"] = ""
lat["codepage"] = "iso-8859-15"
lat["special_chars"] = "ÆŒæœ"

# dan ---------------------------------------------------
dan = deepcopy(empty)
dan["code"] = "dan"
dan["code2"] = "da"
dan["name"] = "Dansk"
dan["articles_used"] = 0
dan["articles"] = {}
dan["article_abbr"] = ""
dan["verb_prefix"] = ""
dan["plural"] = "r, e"
dan["codepage"] = "iso-8859-10"
dan["special_chars"] = "ÅÆØåæø"

# dut ---------------------------------------------------
dut = deepcopy(empty)
dut["code"] = "dut"
dut["code2"] = "nl"
dut["name"] = "Nederlands"
dut["articles_used"] = 3
dut["articles"] = {"m": "de",  "f": "de", "n": "het"}
dut["article_abbr"] = ""
dut["verb_prefix"] = ""
dut["plural"] = ""
dut["codepage"] = "iso-8859-15"
dut["special_chars"] = "ÄÈÉÊÖÜäèéêöü"

# pol ---------------------------------------------------
pol = deepcopy(empty)
pol["code"] = "pol"
pol["code2"] = "pl"
pol["name"] = "Polski"
pol["articles_used"] = 4
pol["articles"] = {"mb": "maskulin belebt", "mu": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
pol["article_abbr"] = ""
pol["verb_prefix"] = ""
pol["plural"] = ""
pol["codepage"] = "iso-8859-2"
pol["special_chars"] = "ĄĆĘŁŃÓŚŹŻąćęłłńóśźż "

# swe ---------------------------------------------------
swe = deepcopy(empty)
swe["code"] = "swe"
swe["code2"] = "sv"
swe["name"] = "Svenska"
swe["articles_used"] = 2
swe["articles"] = {"": "en", "n": "ett"}
swe["article_abbr"] = ""
swe["verb_prefix"] = ""
swe["plural"] = ""
swe["codepage"] = "iso-8859-10"
swe["special_chars"] = "ÄÅÖäåö "

# cze ---------------------------------------------------
cze = deepcopy(empty)
cze["code"] = "cze"
cze["code2"] = "cs"
cze["name"] = " Čeština"
cze["articles_used"] = 4
cze["articles"] = {"mb": "maskulin belebt", "mu": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
cze["article_abbr"] = ""
cze["verb_prefix"] = ""
cze["plural"] = ""
cze["codepage"] = "iso-8859-2"
cze["special_chars"] = "áéíóúýčďěňřšťžů"

# tur ---------------------------------------------------
tur = deepcopy(empty)
tur["code"] = "tur"
tur["code2"] = "tr"
tur["name"] = " Türkçe"
tur["articles_used"] = 0
tur["articles"] = { }
tur["article_abbr"] = ""
tur["verb_prefix"] = ""
tur["plural"] = ""
tur["codepage"] = "iso-8859-9"
tur["special_chars"] = "ÂÇĞİÖŞÜâçğıöşü"

# epo ---------------------------------------------------
epo = deepcopy(empty)
epo["code"] = "epo"
epo["code2"] = "eo"
epo["name"] = "Esperanto"
epo["articles_used"] = 0
epo["articles"] = { }
epo["article_abbr"] = ""
epo["verb_prefix"] = ""
epo["plural"] = ""
epo["codepage"] = "iso-8859-3"
epo["special_chars"] = "ĉĝĥĵŝŭ"

# fin ---------------------------------------------------
fin = deepcopy(empty)
fin["code"] = "fin"
fin["code2"] = "fi"
fin["name"] = "Suomi"
fin["articles_used"] = 0
fin["articles"] = { }
fin["article_abbr"] = ""
fin["verb_prefix"] = ""
fin["plural"] = ""
fin["codepage"] = "iso-8859-10"
fin["special_chars"] = "ÄÅÖŠŽäåöšž"

# rus ---------------------------------------------------
rus = deepcopy(empty)
rus["code"] = "rus"
rus["code2"] = "ru"
rus["name"] = "Россия"
rus["articles_used"] = 4
rus["articles"] = {"mb": "maskulin belebt", "mu": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
rus["article_abbr"] = ""
rus["verb_prefix"] = ""
rus["plural"] = ""
rus["codepage"] = "iso-8859-5"
rus["special_chars"] = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"

# gre ---------------------------------------------------
gre = deepcopy(empty)
gre["code"] = "gre"
gre["code2"] = "el"
gre["name"] = "Ελληνικα"
gre["articles_used"] = 3
gre["articles"] = {"m": "o", "f": "η", "n": "το"}
gre["article_abbr"] = ""
gre["verb_prefix"] = ""
gre["plural"] = ""
gre["codepage"] = "iso-8859-7"
gre["special_chars"] = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψως"

# grc ---------------------------------------------------
grc = deepcopy(empty)
grc["code"] = "grc"
grc["code2"] = "gr"
grc["name"] = "ἡ Ἑλληνικὴ γλῶσσα"
grc["articles_used"] = 3
grc["articles"] = {"m": "o", "f": "η", "n": "το"}
grc["article_abbr"] = ""
grc["verb_prefix"] = ""
grc["plural"] = ""
grc["codepage"] = "iso-8859-7"
grc["special_chars"] = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψως"

# hrv ---------------------------------------------------
hrv = deepcopy(empty)
hrv["code"] = "hrv"
hrv["code2"] = "hr"
hrv["name"] = " Hrvatski"
hrv["articles_used"] = 0
hrv["articles"] = {}
hrv["article_abbr"] = ""
hrv["verb_prefix"] = ""
hrv["plural"] = ""
hrv["codepage"] = "iso-8859-2"
hrv["special_chars"] = "ĆČĐŠŽćčđšž"

# rum ---------------------------------------------------
rum = deepcopy(empty)
rum["code"] = "rum"
rum["code2"] = "ro"
rum["name"] = "Română"
rum["articles_used"] = 3
rum["articles"] = {"m": "m", "f": "f"}
rum["article_abbr"] = "l'"
rum["verb_prefix"] = ""
rum["plural"] = ""
rum["codepage"] = "iso-8859-16"
rum["special_chars"] = "ÂĂÎȘȚâăîșț"

# afr ---------------------------------------------------
afr = deepcopy(empty)
afr["code"] = "afr"
afr["code2"] = "af"
afr["name"] = "Afrikaans"
afr["codepage"] = "iso-8859-15"
afr["special_chars"] = "ÈèÉéÊêËëÎîÏïÔôÛû"

# ara ---------------------------------------------------
ara = deepcopy(empty)
ara["code"] = "ara"
ara["code2"] = "ar"
ara["name"] = "للغة العربية‎"
ara["codepage"] = "utf-8"
ara["special_chars"] = ara["name"]

# alb ---------------------------------------------------
alb = deepcopy(empty)
alb["code"] = "alb"
alb["code2"] = "sq"
alb["name"] = "Gjuha Shqipe"
alb["codepage"] = "iso-8859-16"
alb["special_chars"] = "ËëÇç"

# amh ---------------------------------------------------
amh = deepcopy(empty)
amh["code"] = "amh"
amh["code2"] = "am"
amh["name"] = "Amarəñña"
amh["codepage"] = "utf-8"
amh["special_chars"] = ""

# arm -------------------------------------------------
arm = deepcopy(empty)
arm["code"] = "arm"
arm["code2"] = "hy"
arm["name"] = "Hajeren les"
arm["codepage"] = "utf-8"
arm["special_chars"] = ""

# aze ---------------------------------------------------
aze = deepcopy(empty)
aze["code"] = "aze"
aze["code2"] = "tr"
aze["name"] = "Azərbaycan dili"
aze["codepage"] = "iso-8859-9"
aze["special_chars"] = ""

# bel ---------------------------------------------------
bel = deepcopy(empty)
bel["code"] = "bel"
bel["code2"] = "be"
bel["name"] = "беларуская мова"
bel["articles_used"] = 4
bel["articles"] = {"mb": "maskulin belebt", "mu": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
bel["article_abbr"] = ""
bel["verb_prefix"] = ""
bel["plural"] = ""
bel["codepage"] = "iso-8859-5"
bel["special_chars"] = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"

# ben---------------------------------------------------
ben = deepcopy(empty)
ben["code"] = "ben"
ben["code2"] = "bn"
ben["name"] = "Bangla bhasha"
ben["codepage"] = "utf-8"
ben["special_chars"] = ""

# tib------------------------------------------------
tib = deepcopy(empty)
tib["code"] = "tib"
tib["code2"] = "bo"
tib["name"] = "Bod yig"
tib["codepage"] = "utf-8"
tib["special_chars"] = ""

# bos---------------------------------------------------
bos = deepcopy(empty)
bos["code"] = "bos"
bos["code2"] = "bs"
bos["name"] = "Bosanski jezik"
bos["codepage"] = "iso-8859-2"
bos["special_chars"] = "čćžšž"

# bul ---------------------------------------------------
bul = deepcopy(empty)
bul["code"] = "bul"
bul["code2"] = "bg"
bul["name"] = "Български език"
bul["articles_used"] = 4
bul["articles"] = {"mb": "maskulin belebt", "mu": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
bul["article_abbr"] = ""
bul["verb_prefix"] = ""
bul["plural"] = ""
bul["codepage"] = "iso-8859-5"
bul["special_chars"] = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"

# cat ---------------------------------------------------
cat = deepcopy(empty)
cat["code"] = "cat"
cat["code2"] = "ca"
cat["name"] = "Catalán"
cat["articles_used"] = 2
cat["articles"] = {"m": "el", "f": "la"}
cat["article_abbr"] = ""
cat["verb_prefix"] = ""
cat["plural"] = "s"
cat["codepage"] = "iso-8859-15"
cat["special_chars"] = "ÁÉÍÑÓÚÜáéíñóúü"

# zho ------------------------------------------------
zho = deepcopy(empty)
zho["code"] = "zho"
zho["code2"] = "zh"
zho["name"] = "中文"
zho["codepage"] = "utf-8"
zho["special_chars"] = "地球" # test


# esp ---------------------------------------------------
esp = deepcopy(empty)
esp["code"] = "esp"
esp["code2"] = "ep"
esp["name"] = "Esperanto"
esp["codepage"] = "iso-8859-15"

# est ---------------------------------------------------
est = deepcopy(empty)
est["code"] = "est"
est["code2"] = "et"
est["name"] = "Eesti keel"
est["codepage"] = "iso-8859-15"

# fil ---------------------------------------------------
fil = deepcopy(empty)
fil["code"] = "fil"
fil["code2"] = "fl"
fil["name"] = "Filipino"
fil["codepage"] = "iso-8859-1"

# kat ---------------------------------------------------
kat = deepcopy(empty)
kat["code"] = "kat"
kat["code2"] = "ka"
kat["name"] = "Kartuli Ena"
kat["codepage"] = "utf-8"

# ell ---------------------------------------------------
ell = deepcopy(empty)
ell["code"] = "ell"
ell["code2"] = "el"
ell["name"] = "ελληνική γλώσσα"
ell["codepage"] = "iso-8859-7"

# hau ---------------------------------------------------
hau = deepcopy(empty)
hau["code"] = "hau"
hau["code2"] = "ha"
hau["name"] = "Hausa"
hau["codepage"] = "iso-8859-1"

# heb ---------------------------------------------------
heb = deepcopy(empty)
heb["code"] = "heb"
heb["code2"] = "iw"
heb["name"] = " עברית"
heb["codepage"] = "iso-8859-8"

# hin ---------------------------------------------------
hin = deepcopy(empty)
hin["code"] = "hin"
hin["code2"] = "hi"
hin["name"] = "Hindi"
hin["codepage"] = "utf-8"

# hun ---------------------------------------------------
hun = deepcopy(empty)
hun["code"] = "hun"
hun["code2"] = "hu"
hun["name"] = "Magyar nyelv"
hun["codepage"] = "iso-8859-1"

# isi ---------------------------------------------------
isi = deepcopy(empty)
isi["code"] = "isi"
isi["code2"] = "is"
isi["name"] = "Íslenska"
isi["codepage"] = "iso-8859-1"

# ind ---------------------------------------------------
ind = deepcopy(empty)
ind["code"] = "ind"
ind["code2"] = "in"
ind["name"] = "Bahasa Indonesia"
ind["codepage"] = "iso-8859-1"

# jpn ---------------------------------------------------
jpn = deepcopy(empty)
jpn["code"] = "jpn"
jpn["code2"] = "ja"
jpn["name"] = "日本語"
jpn["codepage"] = "utf-8"

# kor ---------------------------------------------------
kor = deepcopy(empty)
kor["code"] = "kor"
kor["code2"] = "ko"
kor["name"] = "韓國語"
kor["codepage"] = "utf-8"

# lav ---------------------------------------------------
lav = deepcopy(empty)
lav["code"] = "lav"
lav["code2"] = "lv"
lav["name"] = "Latviešu valoda"
lav["codepage"] = "iso-8859-4"

# lit ---------------------------------------------------
lit = deepcopy(empty)
lit["code"] = "lit"
lit["code2"] = "lt"
lit["name"] = "Lietuvių kalba"
lit["codepage"] = "iso-8859-4"

# mon ---------------------------------------------------
mon = deepcopy(empty)
mon["code"] = "mon"
mon["code2"] = "mn"
mon["name"] = "халх монгол хэл"
mon["codepage"] = "iso-8859-5"

# nep ---------------------------------------------------
nep = deepcopy(empty)
nep["code"] = "nep"
nep["code2"] = "ne"
nep["name"] = "Nepali"
nep["codepage"] = "utf-8"

# nor ---------------------------------------------------
nor = deepcopy(empty)
nor["code"] = "nor"
nor["code2"] = "no"
nor["name"] = "Norsk"
nor["codepage"] = "iso-8859-1"

# per ---------------------------------------------------
per = deepcopy(empty)
per["code"] = "per"
per["code2"] = "fa"
per["name"] = "فارسی"
per["codepage"] = "iso-8859-6"

# pol ---------------------------------------------------
pol = deepcopy(empty)
pol["code"] = "pol"
pol["code2"] = "pl"
pol["name"] = "Język polski"
pol["codepage"] = "iso-8859-2"

# ron ---------------------------------------------------
ron = deepcopy(empty)
ron["code"] = "ron"
ron["code2"] = "ro"
ron["name"] = "Limba româna"
ron["codepage"] = "iso-8859-1"

# san ---------------------------------------------------
san = deepcopy(empty)
san["code"] = "san"
san["code2"] = "sa"
san["name"] = "Sanskrit"
san["codepage"] = "utf-8"

# srp ---------------------------------------------------
srp = deepcopy(empty)
srp["code"] = "srp"
srp["code2"] = "sr"
srp["name"] = "Srpski jezik"
srp["codepage"] = "iso-8859-2"

# slk ---------------------------------------------------
slk = deepcopy(empty)
slk["code"] = "slk"
slk["code2"] = "sk"
slk["name"] = "slovenčina"
slk["codepage"] = "iso-8859-2"

# swa ---------------------------------------------------
swa = deepcopy(empty)
swa["code"] = "swa"
swa["code2"] = "sw"
swa["name"] = "Kiswahili"
swa["codepage"] = "iso-8859-1"

# tha ---------------------------------------------------
tha = deepcopy(empty)
tha["code"] = "tha"
tha["code2"] = "th"
tha["name"] = "ภาษาไทย"
tha["codepage"] = "iso-8859-11"

# ukr ---------------------------------------------------
ukr = deepcopy(empty)
ukr["code"] = "ukr"
ukr["code2"] = "uk"
ukr["name"] = "українська"
ukr["codepage"] = "iso-8859-5"

# vie ---------------------------------------------------
vie = deepcopy(empty)
vie["code"] = "vie"
vie["code2"] = "vi"
vie["name"] = "Tiếng Việt"
vie["codepage"] = "iso-8859-1"



#[s] functions -------------------------------------------

_cl = []
for l in languages:
    lang = globals().get(l)
    if not lang["code"]:
        continue
    _cl.append({"id": lang["code"], "name": lang["name"]})

def GetConf(langcode):
    """
    Load language configuration by code (3 letters)
    """
    if langcode in languages:
        return globals().get(langcode)
    if len(langcode)==2:
        for l in languages:
            c = globals().get(l)
            if c["code2"] == langcode:
                return c
    return empty


def GetLanguages():
    """
    load codelist of languages and cache
    """
    global _cl
    return _cl
    #cl = []
    #for l in languages:
    #    cl.append({"id": l["code"], "name": l["name"]})
    #_cl = cl
    #return cl
