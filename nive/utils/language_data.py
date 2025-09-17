#
""" -*- coding: utf-8 -*-"""

from copy import deepcopy


LANGUAGES = dict()  # 3 char codes
LANGUAGES2 = dict() # 2 char codes + mapping 3 chars


#[s] api -------------------------------------------

def GetConf(langcode):
    """
    Load language configuration by code (3 letters)
    """
    if len(langcode)==2:
        langcode = LANGUAGES2.get(langcode)
        if not langcode:
            return empty
    return LANGUAGES.get(langcode, empty)


def GetLanguages(level=0):
    """
    load codelist of LANGUAGES and cache
    """
    _cl = []
    for code, lang in LANGUAGES.items():
        if lang["level"]>level:
            continue
        _cl.append({"id": lang["code"], "name": lang["name"]})
    return _cl


def GetLanguages2(level=0):
    """
    load codelist of LANGUAGES and cache
    """
    _cl = []
    for code2, mapping in LANGUAGES2.items():
        lang = LANGUAGES[mapping]
        if lang["level"]>level:
            continue
        _cl.append({"id": code2, "title": lang["name"], "name": "%s (%s)"%(code2, lang["name"])})
    return _cl



# default ------------------------------------------------
empty = dict()
empty["code"] = ""
empty["code2"] = ""
empty["name"] = ""
empty["local"] = ""
empty["articles_used"] = 0 # 1=article, 2=f+m, 3=f+m+n
empty["articles"] = dict()
empty["article_abbr"] = ""
empty["verb_prefix"] = ""
empty["plural"] = ""
empty["codepage"] = ""
empty["remove_chars"] = "\t\r\n"
empty["special_chars"] = ""

# level for sublist:
#    0 = active LANGUAGES/countries
#    1-8 = uncommon LANGUAGES rarely used in EU apps
#    9 = not linked to countries/local LANGUAGES/dialects,
empty["level"] = 0


#[s] LANGUAGES -------------------------------------------

noArticle = "no-article"

def _add(info):
    LANGUAGES[info["code"]] = info
    LANGUAGES2[info["code2"]] = info["code"]

# variants: en-gb en-us uh-hans zh-hant

# ger ---------------------------------------------------
ger = deepcopy(empty)
ger["code"] = "ger"
ger["code2"] = "de"
ger["name"] = "Deutsch"
ger["local"] = "Deutsch"
ger["articles_used"] = 3
ger["articles"] = {"m": "der", "f": "die", "n": "das"}
ger["verb_prefix"] = ""
ger["plural"] = "s"
ger["codepage"] = "iso-8859-15"
ger["special_chars"] = "äöüÄÖÜß"
_add(ger)

# eng ---------------------------------------------------
eng = deepcopy(empty)
eng["code"] = "eng"
eng["code2"] = "en"
eng["name"] = "Englisch"
eng["local"] = "English"
eng["articles_used"] = 1
eng["articles"] = {"a": "the"}
eng["verb_prefix"] = "to"
eng["plural"] = "s"
eng["codepage"] = "iso-8859-1"
eng["special_chars"] = ""
_add(eng)

# ita ---------------------------------------------------
ita = deepcopy(empty)
ita["code"] = "ita"
ita["code2"] = "it"
ita["name"] = "Italienisch"
ita["local"] = "Italiano"
ita["articles_used"] = 2
ita["articles"] = {"m": "il", "f": "la"}
ita["article_abbr"] = "l'"
ita["verb_prefix"] = ""
ita["plural"] = ""
ita["codepage"] = "iso-8859-15"
ita["special_chars"] = "ÀÈÉÌÒÙàèéìòù"
_add(ita)

# spa ---------------------------------------------------
spa = deepcopy(empty)
spa["code"] = "spa"
spa["code2"] = "es"
spa["name"] = "Spanisch"
spa["local"] = "Español"
spa["articles_used"] = 2
spa["articles"] = {"m": "el", "f": "la"}
spa["article_abbr"] = ""
spa["verb_prefix"] = ""
spa["plural"] = "s"
spa["codepage"] = "iso-8859-15"
spa["special_chars"] = "ÁÉÍÑÓÚÜáéíñóúü"
_add(spa)

# fra ---------------------------------------------------
fra = deepcopy(empty)
fra["code"] = "fra"
fra["code2"] = "fr"
fra["name"] = "Französisch"
fra["local"] = "Français"
fra["articles_used"] = 2
fra["articles"] = {"m": "le", "f": "la"}
fra["article_abbr"] = "l’"
fra["verb_prefix"] = ""
fra["plural"] = ""
fra["codepage"] = "iso-8859-15"
fra["special_chars"] = "ÀÂÇÈÉÊËÎÏÔŒÙÛÜŸàâçèéêëîïôœùûüÿ"
_add(fra)

# por ---------------------------------------------------
por = deepcopy(empty)
por["code"] = "por"
por["code2"] = "pt"
por["name"] = "Portugiesisch"
por["local"] = "Português"
por["articles_used"] = 2
por["articles"] = {"m": "o", "f": "a"}
por["article_abbr"] = ""
por["verb_prefix"] = ""
por["plural"] = ""
por["codepage"] = "iso-8859-15"
por["special_chars"] = "ÀÁÂÃÇÉÊÍÓÔÕÚÜàáâãçéêíóôõúü"
_add(por)


# dan ---------------------------------------------------
dan = deepcopy(empty)
dan["code"] = "dan"
dan["code2"] = "da"
dan["name"] = "Dänisch"
dan["local"] = "Dansk"
dan["articles_used"] = 0
dan["articles"] = {}
dan["article_abbr"] = ""
dan["verb_prefix"] = ""
dan["plural"] = "r, e"
dan["codepage"] = "iso-8859-10"
dan["special_chars"] = "ÅÆØåæø"
_add(dan)

# dut ---------------------------------------------------
dut = deepcopy(empty)
dut["code"] = "dut"
dut["code2"] = "nl"
dut["name"] = "Niederländisch"
dut["local"] = "Nederlands"
dut["articles_used"] = 3
dut["articles"] = {"m": "de",  "f": "de", "n": "het"}
dut["article_abbr"] = ""
dut["verb_prefix"] = ""
dut["plural"] = ""
dut["codepage"] = "iso-8859-15"
dut["special_chars"] = "ÄÈÉÊÖÜäèéêöü"
_add(dut)

# pol ---------------------------------------------------
pol = deepcopy(empty)
pol["code"] = "pol"
pol["code2"] = "pl"
pol["name"] = "Polnisch"
pol["local"] = "Polski"
pol["articles_used"] = 4
pol["articles"] = {"ma": "maskulin belebt", "mi": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
pol["article_abbr"] = ""
pol["verb_prefix"] = ""
pol["plural"] = ""
pol["codepage"] = "iso-8859-2"
pol["special_chars"] = "ĄĆĘŁŃÓŚŹŻąćęłłńóśźż "
_add(pol)

# swe ---------------------------------------------------
swe = deepcopy(empty)
swe["code"] = "swe"
swe["code2"] = "sv"
swe["name"] = "Schwedisch"
swe["local"] = "Svenska"
swe["articles_used"] = 2
swe["articles"] = {"": "en", "n": "ett"}
swe["article_abbr"] = ""
swe["verb_prefix"] = ""
swe["plural"] = ""
swe["codepage"] = "iso-8859-10"
swe["special_chars"] = "ÄÅÖäåö "
_add(swe)

# cze ---------------------------------------------------
cze = deepcopy(empty)
cze["code"] = "cze"
cze["code2"] = "cs"
cze["name"] = "Tschechisch"
cze["local"] = "Čeština"
cze["articles_used"] = 4
cze["articles"] = {"ma": "maskulin belebt", "mi": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
cze["article_abbr"] = ""
cze["verb_prefix"] = ""
cze["plural"] = ""
cze["codepage"] = "iso-8859-2"
cze["special_chars"] = "áéíóúýčďěňřšťžů"
_add(cze)

# tur ---------------------------------------------------
tur = deepcopy(empty)
tur["code"] = "tur"
tur["code2"] = "tr"
tur["name"] = "Türkisch"
tur["local"] = "Türkçe"
tur["articles_used"] = 0
tur["articles"] = { }
tur["article_abbr"] = ""
tur["verb_prefix"] = ""
tur["plural"] = ""
tur["codepage"] = "iso-8859-9"
tur["special_chars"] = "ÂÇĞİÖŞÜâçğıöşü"
_add(tur)

# fin ---------------------------------------------------
fin = deepcopy(empty)
fin["code"] = "fin"
fin["code2"] = "fi"
fin["name"] = "Finnisch"
fin["local"] = "Suomi"
fin["articles_used"] = 0
fin["articles"] = { }
fin["article_abbr"] = ""
fin["verb_prefix"] = ""
fin["plural"] = ""
fin["codepage"] = "iso-8859-10"
fin["special_chars"] = "ÄÅÖŠŽäåöšž"
_add(fin)

# rus ---------------------------------------------------
rus = deepcopy(empty)
rus["code"] = "rus"
rus["code2"] = "ru"
rus["name"] = "Russisch"
rus["local"] = "Россия"
rus["articles_used"] = 4
rus["articles"] = {"ma": "maskulin belebt", "mi": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
rus["article_abbr"] = ""
rus["verb_prefix"] = ""
rus["plural"] = ""
rus["codepage"] = "iso-8859-5"
rus["special_chars"] = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"
_add(rus)

# gre ---------------------------------------------------
gre = deepcopy(empty)
gre["code"] = "gre"
gre["code2"] = "el"
gre["name"] = "Griechisch"
gre["local"] = "Ελληνικα"
gre["articles_used"] = 3
gre["articles"] = {"m": "o", "f": "η", "n": "το"}
gre["article_abbr"] = ""
gre["verb_prefix"] = ""
gre["plural"] = ""
gre["codepage"] = "iso-8859-7"
gre["special_chars"] = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψως"
_add(gre)

# rum ---------------------------------------------------
rum = deepcopy(empty)
rum["code"] = "rum"
rum["code2"] = "ro"
rum["name"] = "Rumänisch"
rum["local"] = "Română"
rum["articles_used"] = 3
rum["articles"] = {"m": "m", "f": "f"}
rum["article_abbr"] = "l'"
rum["verb_prefix"] = ""
rum["plural"] = ""
rum["codepage"] = "iso-8859-16"
rum["special_chars"] = "ÂĂÎȘȚâăîșț"
_add(rum)

# ukr ---------------------------------------------------
ukr = deepcopy(empty)
ukr["code"] = "ukr"
ukr["code2"] = "uk"
ukr["name"] = "Ukrainisch"
ukr["local"] = "українська"
ukr["codepage"] = "iso-8859-5"
_add(ukr)

# bul ---------------------------------------------------
bul = deepcopy(empty)
bul["code"] = "bul"
bul["code2"] = "bg"
bul["name"] = "Bulgarisch"
bul["local"] = "Български език"
bul["articles_used"] = 4
bul["articles"] = {"ma": "maskulin belebt", "mi": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
bul["article_abbr"] = ""
bul["verb_prefix"] = ""
bul["plural"] = ""
bul["codepage"] = "iso-8859-5"
bul["special_chars"] = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"
_add(bul)

# zho ------------------------------------------------
zho = deepcopy(empty)
zho["code"] = "zho"
zho["code2"] = "zh"
zho["name"] = "Chinesisch"
zho["local"] = "中文"
zho["codepage"] = "utf-8"
zho["special_chars"] = "地球" # test
_add(zho)

# est ---------------------------------------------------
est = deepcopy(empty)
est["code"] = "est"
est["code2"] = "et"
est["name"] = "Estnisch"
est["local"] = "Eesti keel"
est["codepage"] = "iso-8859-15"
_add(est)


# ara ---------------------------------------------------
ara = deepcopy(empty)
ara["code"] = "ara"
ara["code2"] = "ar"
ara["name"] = "Arabisch"
ara["local"] = "للغة العربية‎"
ara["codepage"] = "utf-8"
ara["special_chars"] = ara["name"]
_add(ara)

# hun ---------------------------------------------------
hun = deepcopy(empty)
hun["code"] = "hun"
hun["code2"] = "hu"
hun["name"] = "Ungarisch"
hun["local"] = "Magyar nyelv"
hun["codepage"] = "iso-8859-1"
_add(hun)

# jpn ---------------------------------------------------
jpn = deepcopy(empty)
jpn["code"] = "jpn"
jpn["code2"] = "ja"
jpn["name"] = "Japanisch"
jpn["local"] = "日本語"
jpn["codepage"] = "utf-8"
_add(jpn)

# kor ---------------------------------------------------
kor = deepcopy(empty)
kor["code"] = "kor"
kor["code2"] = "ko"
kor["name"] = "Koreanisch"
kor["local"] = "韓國語"
kor["codepage"] = "utf-8"
_add(kor)

# lav ---------------------------------------------------
lav = deepcopy(empty)
lav["code"] = "lav"
lav["code2"] = "lv"
lav["name"] = "Lättisch"
lav["local"] = "Latviešu valoda"
lav["codepage"] = "iso-8859-4"
_add(lav)

# lit ---------------------------------------------------
lit = deepcopy(empty)
lit["code"] = "lit"
lit["code2"] = "lt"
lit["name"] = "Litauisch"
lit["local"] = "Lietuvių kalba"
lit["codepage"] = "iso-8859-4"
_add(lit)

# nor ---------------------------------------------------
nor = deepcopy(empty)
nor["code"] = "nor"
nor["code2"] = "no"
nor["name"] = "Norwegisch"
nor["local"] = "Norsk"
nor["codepage"] = "iso-8859-1"
_add(nor)

# nor ---------------------------------------------------
nob = deepcopy(empty)
nob["code"] = "nob"
nob["code2"] = "nb"
nob["name"] = "Norwegisch Bokmål"
nob["local"] = "Bokmål"
nob["codepage"] = "iso-8859-1"
_add(nob)

# slk ---------------------------------------------------
slk = deepcopy(empty)
slk["code"] = "slk"
slk["code2"] = "sk"
slk["name"] = "Slovakisch"
slk["local"] = "Slovenčina"
slk["codepage"] = "iso-8859-2"
_add(slk)

# slv ---------------------------------------------------
slk = deepcopy(empty)
slk["code"] = "slv"
slk["code2"] = "sl"
slk["name"] = "Slovenisch"
slk["local"] = "Slovene"
slk["codepage"] = "iso-8859-2"
_add(slk)

# ind ---------------------------------------------------
ind = deepcopy(empty)
ind["code"] = "ind"
ind["code2"] = "id"
ind["name"] = "Indonesisch"
ind["local"] = "Bahasa Indonesia"
ind["codepage"] = "iso-8859-1"
_add(ind)



""" 2nd level languages """

# per ---------------------------------------------------
per = deepcopy(empty)
per["code"] = "per"
per["code2"] = "fa"
per["name"] = "Persisch"
per["local"] = "فارسی"
per["codepage"] = "iso-8859-6"
per["level"] = 2
_add(per)
# srp ---------------------------------------------------
srp = deepcopy(empty)
srp["code"] = "srp"
srp["code2"] = "sr"
srp["name"] = "Serbisch"
srp["local"] = "Srpski jezik"
srp["codepage"] = "iso-8859-2"
srp["level"] = 2
_add(srp)
# swa ---------------------------------------------------
swa = deepcopy(empty)
swa["code"] = "swa"
swa["code2"] = "sw"
swa["name"] = "Kiswahili"
swa["local"] = "Kiswahili"
swa["codepage"] = "iso-8859-1"
swa["level"] = 2
_add(swa)
# tha ---------------------------------------------------
tha = deepcopy(empty)
tha["code"] = "tha"
tha["code2"] = "th"
tha["name"] = "Thailändisch"
tha["local"] = "ภาษาไทย"
tha["codepage"] = "iso-8859-11"
tha["level"] = 2
_add(tha)
# vie ---------------------------------------------------
vie = deepcopy(empty)
vie["code"] = "vie"
vie["code2"] = "vi"
vie["name"] = "Vietnamesisch"
vie["local"] = "Tiếng Việt"
vie["codepage"] = "iso-8859-1"
vie["level"] = 2
_add(vie)
# hrv ---------------------------------------------------
hrv = deepcopy(empty)
hrv["code"] = "hrv"
hrv["code2"] = "hr"
hrv["name"] = "Kroatisch"
hrv["local"] = "Hrvatski"
hrv["articles_used"] = 0
hrv["articles"] = {}
hrv["article_abbr"] = ""
hrv["verb_prefix"] = ""
hrv["plural"] = ""
hrv["codepage"] = "iso-8859-2"
hrv["special_chars"] = "ĆČĐŠŽćčđšž"
hrv["level"] = 2
_add(hrv)
# afr ---------------------------------------------------
afr = deepcopy(empty)
afr["code"] = "afr"
afr["code2"] = "af"
afr["name"] = "Afrikaans"
afr["local"] = "Afrikaans"
afr["codepage"] = "iso-8859-15"
afr["special_chars"] = "ÈèÉéÊêËëÎîÏïÔôÛû"
afr["level"] = 2
_add(afr)
# alb ---------------------------------------------------
alb = deepcopy(empty)
alb["code"] = "alb"
alb["code2"] = "sq"
alb["name"] = "Albanisch"
alb["name"] = "Gjuha Shqipe"
alb["codepage"] = "iso-8859-16"
alb["special_chars"] = "ËëÇç"
alb["level"] = 2
_add(alb)
# bel ---------------------------------------------------
bel = deepcopy(empty)
bel["code"] = "bel"
bel["code2"] = "be"
bel["name"] = "Weisrussisch"
bel["local"] = "беларуская мова"
bel["articles_used"] = 4
bel["articles"] = {"ma": "maskulin belebt", "mi": "maskulin unbelebt", "f": "feminin", "n": "neutrum"}
bel["article_abbr"] = ""
bel["verb_prefix"] = ""
bel["plural"] = ""
bel["codepage"] = "iso-8859-5"
bel["special_chars"] = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"
bel["level"] = 2
_add(bel)
# bos---------------------------------------------------
bos = deepcopy(empty)
bos["code"] = "bos"
bos["code2"] = "bs"
bos["name"] = "Bosnisch"
bos["local"] = "Bosanski jezik"
bos["codepage"] = "iso-8859-2"
bos["special_chars"] = "čćžšž"
bos["level"] = 2
_add(bos)
# tib------------------------------------------------
tib = deepcopy(empty)
tib["code"] = "tib"
tib["code2"] = "bo"
tib["name"] = "Tibetisch"
tib["local"] = "Bod yig"
tib["codepage"] = "utf-8"
tib["special_chars"] = ""
tib["level"] = 2
_add(tib)
# kat ---------------------------------------------------
kat = deepcopy(empty)
kat["code"] = "kat"
kat["code2"] = "ka"
kat["name"] = "Georgisch"
kat["local"] = "Kartuli Ena"
kat["codepage"] = "utf-8"
kat["level"] = 2
_add(kat)
# heb ---------------------------------------------------
heb = deepcopy(empty)
heb["code"] = "heb"
heb["code2"] = "iw"
heb["name"] = "Hebräisch"
heb["local"] = " עברית"
heb["codepage"] = "iso-8859-8"
heb["level"] = 2
_add(heb)
# hin ---------------------------------------------------
hin = deepcopy(empty)
hin["code"] = "hin"
hin["code2"] = "hi"
hin["name"] = "Hindi"
hin["codepage"] = "utf-8"
hin["level"] = 2
_add(hin)
# isi ---------------------------------------------------
isi = deepcopy(empty)
isi["code"] = "isi"
isi["code2"] = "is"
isi["name"] = "Isländisch"
isi["local"] = "Íslenska"
isi["codepage"] = "iso-8859-1"
isi["level"] = 2
_add(isi)

""" 3rd level languages """
# amh ---------------------------------------------------
amh = deepcopy(empty)
amh["code"] = "amh"
amh["code2"] = "am"
amh["name"] = "Amarəñña"
amh["local"] = "Amarəñña"
amh["codepage"] = "utf-8"
amh["special_chars"] = ""
amh["level"] = 3
_add(amh)

# arm -------------------------------------------------
arm = deepcopy(empty)
arm["code"] = "arm"
arm["code2"] = "hy"
arm["name"] = "Hajeren les"
arm["local"] = "Hajeren les"
arm["codepage"] = "utf-8"
arm["special_chars"] = ""
arm["level"] = 3
_add(arm)

# aze ---------------------------------------------------
aze = deepcopy(empty)
aze["code"] = "aze"
aze["code2"] = "az"
aze["name"] = "Azərbaycan dili"
aze["local"] = "Azərbaycan dili"
aze["codepage"] = "iso-8859-9"
aze["special_chars"] = ""
aze["level"] = 3
_add(aze)

# ben---------------------------------------------------
ben = deepcopy(empty)
ben["code"] = "ben"
ben["code2"] = "bn"
ben["name"] = "Bangla bhasha"
ben["local"] = "Bangla bhasha"
ben["codepage"] = "utf-8"
ben["special_chars"] = ""
ben["level"] = 3
_add(ben)

# fil ---------------------------------------------------
fil = deepcopy(empty)
fil["code"] = "fil"
fil["code2"] = "fl"
fil["name"] = "Filipino"
fil["local"] = "Filipino"
fil["codepage"] = "iso-8859-1"
fil["level"] = 3
_add(fil)

# hau ---------------------------------------------------
hau = deepcopy(empty)
hau["code"] = "hau"
hau["code2"] = "ha"
hau["name"] = "Hausa"
hau["local"] = "Hausa"
hau["codepage"] = "iso-8859-1"
hau["level"] = 9
_add(hau)

# mon ---------------------------------------------------
mon = deepcopy(empty)
mon["code"] = "mon"
mon["code2"] = "mn"
mon["name"] = "халх монгол хэл"
mon["local"] = "халх монгол хэл"
mon["codepage"] = "iso-8859-5"
mon["level"] = 3
_add(mon)

# nep ---------------------------------------------------
nep = deepcopy(empty)
nep["code"] = "nep"
nep["code2"] = "ne"
nep["name"] = "Nepali"
nep["local"] = "Nepali"
nep["codepage"] = "utf-8"
nep["level"] = 3
_add(nep)

# san ---------------------------------------------------
san = deepcopy(empty)
san["code"] = "san"
san["code2"] = "sa"
san["name"] = "Sanskrit"
san["local"] = "Sanskrit"
san["codepage"] = "utf-8"
san["level"] = 3
_add(san)


# ell ---------------------------------------------------
ell = deepcopy(empty) # alt for gre
ell["code"] = "ell"
ell["code2"] = "gr"
ell["name"] = "Griechisch (alt)"
ell["local"] = "ελληνική γλώσσα"
ell["codepage"] = "iso-8859-7"
ell["level"] = 9
_add(ell)
# cat ---------------------------------------------------
cat = deepcopy(empty)
cat["code"] = "cat"
cat["code2"] = "ca"
cat["name"] = "Katalanisch"
cat["local"] = "Catalán"
cat["articles_used"] = 2
cat["articles"] = {"m": "el", "f": "la"}
cat["article_abbr"] = ""
cat["verb_prefix"] = ""
cat["plural"] = "s"
cat["codepage"] = "iso-8859-15"
cat["special_chars"] = "ÁÉÍÑÓÚÜáéíñóúü"
cat["level"] = 9
_add(cat)
# epo ---------------------------------------------------
epo = deepcopy(empty)
epo["code"] = "epo"
epo["code2"] = "eo"
epo["name"] = "Esperanto"
epo["local"] = "Esperanto"
epo["articles_used"] = 0
epo["articles"] = { }
epo["article_abbr"] = ""
epo["verb_prefix"] = ""
epo["plural"] = ""
epo["codepage"] = "iso-8859-3"
epo["special_chars"] = "ĉĝĥĵŝŭ"
epo["level"] = 9
_add(epo)
# lat ---------------------------------------------------
lat = deepcopy(empty)
lat["code"] = "lat"
lat["code2"] = "la"
lat["name"] = "Latein"
lat["local"] = "Lingua Latina"
lat["articles_used"] = 0
lat["articles"] = {}
lat["article_abbr"] = ""
lat["verb_prefix"] = ""
lat["plural"] = ""
lat["codepage"] = "iso-8859-15"
lat["special_chars"] = "ÆŒæœ"
lat["level"] = 9
_add(lat)

