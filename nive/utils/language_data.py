#
""" -*- coding: utf-8 -*-"""

from copy import deepcopy


LANGUAGES = dict()  # 2 char codes + variants
LANGUAGES3 = dict() # mapping 3 chars


#[s] api -------------------------------------------

def GetConf(langcode):
    """
    Load language configuration by code (3 letters)
    """
    if len(langcode)==3:
        langcode = LANGUAGES3.get(langcode)
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
        _cl.append({"id": lang["code2"], "name": lang["name"], "local": lang["local"], "en": lang.get("en",lang["name"])})
    return _cl


def GetLanguages3(level=0):
    """
    load codelist of LANGUAGES and cache
    """
    _cl = []
    for code3, mapping in LANGUAGES3.items():
        lang = LANGUAGES[mapping]
        if lang["level"]>level:
            continue
        _cl.append({"id": code3, "title": lang["name"], "name": "%s (%s)"%(code3, lang["name"])})
    return _cl

def ExtendLanguages(languages):
    for l in languages:
        _add(l)

# default ------------------------------------------------
empty = dict()
empty["code"] = ""
empty["code2"] = ""
empty["name"] = ""
empty["local"] = ""
empty["en"] = ""
empty["articles_used"] = 0 # 1=article, 2=f+m, 3=f+m+n
empty["articles"] = dict()
empty["article_abbr"] = ""
empty["verb_prefix"] = ""
empty["plural"] = ""
empty["codepage"] = ""
empty["remove_chars"] = "\t\r\n"
empty["special_chars"] = ""

# level for sublist:
#    1 = active LANGUAGES/countries
#    2-8 = uncommon LANGUAGES rarely used in EU apps
#    9 = not linked to countries/local LANGUAGES/dialects,
empty["level"] = 1


#[s] LANGUAGES -------------------------------------------

noArticle = "no-article"

def _add(info):
    LANGUAGES3[info["code"]] = info["code"]
    LANGUAGES[info["code2"]] = info

# variants: en-gb en-us uh-hans zh-hant
def _addVariant(info):
    LANGUAGES[info["code2"]] = info

# ger ---------------------------------------------------
ger = deepcopy(empty)
ger["code"] = "ger"
ger["code2"] = "de"
ger["name"] = "Deutsch"
ger["local"] = "Deutsch"
ger["en"] = "German"
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
eng["en"] = "English"
eng["articles_used"] = 1
eng["articles"] = {"a": "the"}
eng["verb_prefix"] = "to"
eng["plural"] = "s"
eng["codepage"] = "iso-8859-1"
eng["special_chars"] = ""
_add(eng)

eng2 = deepcopy(eng)
eng2["code2"] = "en-gb"
eng2["name"] = "Englisch (Britisch)"
eng2["local"] = "English (GB)"
_addVariant(eng2)

eng3 = deepcopy(eng)
eng3["code2"] = "en-us"
eng3["name"] = "Englisch (Amerikanisch)"
eng3["local"] = "English (US)"
_addVariant(eng3)


# ita ---------------------------------------------------
ita = deepcopy(empty)
ita["code"] = "ita"
ita["code2"] = "it"
ita["name"] = "Italienisch"
ita["local"] = "Italiano"
ita["en"] = "Italian"
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
spa["en"] = "Spanish"
spa["articles_used"] = 2
spa["articles"] = {"m": "el", "f": "la"}
spa["article_abbr"] = ""
spa["verb_prefix"] = ""
spa["plural"] = "s"
spa["codepage"] = "iso-8859-15"
spa["special_chars"] = "ÁÉÍÑÓÚÜáéíñóúü"
_add(spa)

spa2 = deepcopy(spa)
spa2["code2"] = "es-419"
spa2["name"] = "Spanisch (Lateinamerika)"
spa2["local"] = "Español (Latino)"
_add(spa2)

# fra ---------------------------------------------------
fra = deepcopy(empty)
fra["code"] = "fra"
fra["code2"] = "fr"
fra["name"] = "Französisch"
fra["local"] = "Français"
fra["en"] = "French"
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
por["en"] = "Portuguese"
por["articles_used"] = 2
por["articles"] = {"m": "o", "f": "a"}
por["article_abbr"] = ""
por["verb_prefix"] = ""
por["plural"] = ""
por["codepage"] = "iso-8859-15"
por["special_chars"] = "ÀÁÂÃÇÉÊÍÓÔÕÚÜàáâãçéêíóôõúü"
_add(por)

por2 = deepcopy(por)
por2["code2"] = "pt-br"
por2["name"] = "Portugiesisch (Brasilianisch)"
por2["local"] = "Português (BR)"
_add(por2)

por3 = deepcopy(por)
por3["code2"] = "pt-pt"
por3["name"] = "Portugiesisch (Portugiesisch)"
por3["local"] = "Português (BR)"
_add(por3)

# dan ---------------------------------------------------
dan = deepcopy(empty)
dan["code"] = "dan"
dan["code2"] = "da"
dan["name"] = "Dänisch"
dan["local"] = "Dansk"
dan["en"] = "Danish"
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
dut["en"] = "Dutch"
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
pol["en"] = "Polish"
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
swe["en"] = "Swedish"
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
cze["en"] = "Czech"
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
tur["en"] = "Turkish"
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
fin["en"] = "Finnish"
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
rus["local"] = "Русский"
rus["en"] = "Russian"
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
gre["en"] = "Greek"
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
rum["en"] = "Romanian"
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
ukr["en"] = "Ukrainian"
ukr["codepage"] = "iso-8859-5"
_add(ukr)

# bul ---------------------------------------------------
bul = deepcopy(empty)
bul["code"] = "bul"
bul["code2"] = "bg"
bul["name"] = "Bulgarisch"
bul["local"] = "Български език"
bul["en"] = "Bulgarian"
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
zho["en"] = "Chinese"
zho["codepage"] = "utf-8"
zho["special_chars"] = "地球" # test
_add(zho)

zho2 = deepcopy(zho)
zho2["code2"] = "zh-hans"
zho2["name"] = "Chinesisch (Einfach)"
_add(zho2)

zho3 = deepcopy(zho)
zho3["code2"] = "zh-hant"
zho3["name"] = "Chinesisch (Traditional)"
_add(zho3)

# est ---------------------------------------------------
est = deepcopy(empty)
est["code"] = "est"
est["code2"] = "et"
est["name"] = "Estnisch"
est["local"] = "Eesti keel"
est["en"] = "Estonian"
est["codepage"] = "iso-8859-15"
_add(est)

# ara ---------------------------------------------------
ara = deepcopy(empty)
ara["code"] = "ara"
ara["code2"] = "ar"
ara["name"] = "Arabisch"
ara["local"] = "للغة العربية‎"
ara["en"] = "Arabic"
ara["codepage"] = "utf-8"
ara["special_chars"] = ara["name"]
_add(ara)

# hun ---------------------------------------------------
hun = deepcopy(empty)
hun["code"] = "hun"
hun["code2"] = "hu"
hun["name"] = "Ungarisch"
hun["local"] = "Magyar nyelv"
hun["en"] = "Hungarian"
hun["codepage"] = "iso-8859-1"
_add(hun)

# jpn ---------------------------------------------------
jpn = deepcopy(empty)
jpn["code"] = "jpn"
jpn["code2"] = "ja"
jpn["name"] = "Japanisch"
jpn["local"] = "日本語"
jpn["en"] = "Japanese"
jpn["codepage"] = "utf-8"
_add(jpn)

# kor ---------------------------------------------------
kor = deepcopy(empty)
kor["code"] = "kor"
kor["code2"] = "ko"
kor["name"] = "Koreanisch"
kor["local"] = "韓國語"
kor["en"] = "Korean"
kor["codepage"] = "utf-8"
_add(kor)

# lav ---------------------------------------------------
lav = deepcopy(empty)
lav["code"] = "lav"
lav["code2"] = "lv"
lav["name"] = "Lättisch"
lav["local"] = "Latviešu valoda"
lav["en"] = "Latvian"
lav["codepage"] = "iso-8859-4"
_add(lav)

# lit ---------------------------------------------------
lit = deepcopy(empty)
lit["code"] = "lit"
lit["code2"] = "lt"
lit["name"] = "Litauisch"
lit["local"] = "Lietuvių kalba"
lit["en"] = "Lithuanian"
lit["codepage"] = "iso-8859-4"
_add(lit)

# nor ---------------------------------------------------
nob = deepcopy(empty)
nob["code"] = "nob"
nob["code2"] = "nb"
nob["name"] = "Norwegisch Bokmål"
nob["local"] = "Bokmål"
nob["en"] = "Norwegian"
nob["codepage"] = "iso-8859-1"
_add(nob)

# slk ---------------------------------------------------
slk = deepcopy(empty)
slk["code"] = "slk"
slk["code2"] = "sk"
slk["name"] = "Slovakisch"
slk["local"] = "Slovenčina"
slk["en"] = "Slovak"
slk["codepage"] = "iso-8859-2"
_add(slk)

# slv ---------------------------------------------------
slk = deepcopy(empty)
slk["code"] = "slv"
slk["code2"] = "sl"
slk["name"] = "Slovenisch"
slk["local"] = "Slovene"
slk["en"] = "Slovenian"
slk["codepage"] = "iso-8859-2"
_add(slk)

# per ---------------------------------------------------
per = deepcopy(empty)
per["code"] = "per"
per["code2"] = "fa"
per["name"] = "Persisch"
per["local"] = "فارسی"
per["en"] = "Persian"
per["codepage"] = "iso-8859-6"
_add(per)

# hrv ---------------------------------------------------
hrv = deepcopy(empty)
hrv["code"] = "hrv"
hrv["code2"] = "hr"
hrv["name"] = "Kroatisch"
hrv["local"] = "Hrvatski"
hrv["en"] = "Croatian"
hrv["articles_used"] = 0
hrv["articles"] = {}
hrv["article_abbr"] = ""
hrv["verb_prefix"] = ""
hrv["plural"] = ""
hrv["codepage"] = "iso-8859-2"
hrv["special_chars"] = "ĆČĐŠŽćčđšž"
_add(hrv)

# srp ---------------------------------------------------
srp = deepcopy(empty)
srp["code"] = "srp"
srp["code2"] = "sr"
srp["name"] = "Serbisch"
srp["local"] = "Srpski jezik"
srp["en"] = "Serbian"
srp["codepage"] = "iso-8859-2"
_add(srp)

# hin ---------------------------------------------------
hin = deepcopy(empty)
hin["code"] = "hin"
hin["code2"] = "hi"
hin["name"] = "Hindi"
hin["local"] = "Hindi"
hin["en"] = "Hindi"
hin["codepage"] = "utf-8"
_add(hin)

""" 2nd level languages """

# ind ---------------------------------------------------
ind = deepcopy(empty)
ind["code"] = "ind"
ind["code2"] = "id"
ind["name"] = "Indonesisch"
ind["local"] = "Bahasa Indonesia"
ind["en"] = "Indonesian"
ind["codepage"] = "iso-8859-1"
ind["level"] = 2
_add(ind)
# swa ---------------------------------------------------
swa = deepcopy(empty)
swa["code"] = "swa"
swa["code2"] = "sw"
swa["name"] = "Kiswahili"
swa["local"] = "Kiswahili"
swa["en"] = "Swahili"
swa["codepage"] = "iso-8859-1"
swa["level"] = 2
_add(swa)
# tha ---------------------------------------------------
tha = deepcopy(empty)
tha["code"] = "tha"
tha["code2"] = "th"
tha["name"] = "Thailändisch"
tha["local"] = "ภาษาไทย"
tha["en"] = "Thai"
tha["codepage"] = "iso-8859-11"
tha["level"] = 2
_add(tha)
# vie ---------------------------------------------------
vie = deepcopy(empty)
vie["code"] = "vie"
vie["code2"] = "vi"
vie["name"] = "Vietnamesisch"
vie["local"] = "Tiếng Việt"
vie["en"] = "Vietnamese"
vie["codepage"] = "iso-8859-1"
vie["level"] = 2
_add(vie)
# afr ---------------------------------------------------
afr = deepcopy(empty)
afr["code"] = "afr"
afr["code2"] = "af"
afr["name"] = "Afrikaans"
afr["local"] = "Afrikaans"
afr["en"] = "Afrikaans"
afr["codepage"] = "iso-8859-15"
afr["special_chars"] = "ÈèÉéÊêËëÎîÏïÔôÛû"
afr["level"] = 2
_add(afr)
# alb ---------------------------------------------------
alb = deepcopy(empty)
alb["code"] = "alb"
alb["code2"] = "sq"
alb["name"] = "Albanisch"
alb["local"] = "Gjuha Shqipe"
alb["en"] = "Albanian"
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
bel["en"] = "Belarusian"
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
bos["en"] = "Bosnian"
bos["codepage"] = "iso-8859-2"
bos["special_chars"] = "čćžšž"
bos["level"] = 2
_add(bos)
# kat ---------------------------------------------------
kat = deepcopy(empty)
kat["code"] = "kat"
kat["code2"] = "ka"
kat["name"] = "Georgisch"
kat["local"] = "Kartuli Ena"
kat["en"] = "Georgian"
kat["codepage"] = "utf-8"
kat["level"] = 2
_add(kat)
# heb ---------------------------------------------------
heb = deepcopy(empty)
heb["code"] = "heb"
heb["code2"] = "he"
heb["name"] = "Hebräisch"
heb["local"] = " עברית"
heb["en"] = "Hebrew"
heb["codepage"] = "iso-8859-8"
heb["level"] = 2
_add(heb)
# isi ---------------------------------------------------
isi = deepcopy(empty)
isi["code"] = "isi"
isi["code2"] = "is"
isi["name"] = "Isländisch"
isi["local"] = "Íslenska"
isi["en"] = "Icelandic"
isi["codepage"] = "iso-8859-1"
isi["level"] = 2
_add(isi)
# hau ---------------------------------------------------
hau = deepcopy(empty)
hau["code"] = "hau"
hau["code2"] = "ha"
hau["name"] = "Hausa"
hau["local"] = "Hausa"
hau["en"] = "Hausa"
hau["codepage"] = "iso-8859-1"
hau["level"] = 2
_add(hau)

""" other languages --------------------------------------------------------------------------------- """

# arm -------------------------------------------------
arm = deepcopy(empty)
arm["code"] = "arm"
arm["code2"] = "hy"
arm["name"] = "Armenian"
arm["local"] = "Hajeren les"
arm["en"] = "Armenian"
arm["codepage"] = "utf-8"
arm["special_chars"] = ""
arm["level"] = 3
_add(arm)

# aze ---------------------------------------------------
aze = deepcopy(empty)
aze["code"] = "aze"
aze["code2"] = "az"
aze["name"] = "Azerbaijani"
aze["local"] = "Azərbaycan dili"
aze["en"] = "Azerbaijani"
aze["codepage"] = "iso-8859-9"
aze["special_chars"] = ""
aze["level"] = 3
_add(aze)

# ben---------------------------------------------------
ben = deepcopy(empty)
ben["code"] = "ben"
ben["code2"] = "bn"
ben["name"] = "Bengali"
ben["local"] = "Bangla bhasha"
ben["en"] = "Bengali"
ben["codepage"] = "utf-8"
ben["special_chars"] = ""
ben["level"] = 3
_add(ben)
# mon ---------------------------------------------------
mon = deepcopy(empty)
mon["code"] = "mon"
mon["code2"] = "mn"
mon["name"] = "Mongolian"
mon["local"] = "халх монгол хэл"
mon["en"] = "Mongolian"
mon["codepage"] = "iso-8859-5"
mon["level"] = 3
_add(mon)
# nep ---------------------------------------------------
nep = deepcopy(empty)
nep["code"] = "nep"
nep["code2"] = "ne"
nep["name"] = "Nepali"
nep["local"] = "Nepali"
nep["en"] = "Nepali"
nep["codepage"] = "utf-8"
nep["level"] = 3
_add(nep)
# mk -------------------------------------------------
mk = deepcopy(empty)
mk["code"] = "mkd"
mk["code2"] = "mk"
mk["name"] = "Macedonian"
mk["local"] = "македонски јазик"
mk["en"] = "Macedonian"
mk["codepage"] = "iso-8859-5"
mk["level"] = 3
_add(mk)


# san ---------------------------------------------------
san = deepcopy(empty)
san["code"] = "san"
san["code2"] = "sa"
san["name"] = "Sanskrit"
san["local"] = "Sanskrit"
san["en"] = "Sanskrit"
san["codepage"] = "utf-8"
san["level"] = 4
_add(san)


# cat ---------------------------------------------------
cat = deepcopy(empty)
cat["code"] = "cat"
cat["code2"] = "ca"
cat["name"] = "Katalanisch"
cat["local"] = "Catalán"
cat["en"] = "Catalan"
cat["articles_used"] = 2
cat["articles"] = {"m": "el", "f": "la"}
cat["article_abbr"] = ""
cat["verb_prefix"] = ""
cat["plural"] = "s"
cat["codepage"] = "iso-8859-15"
cat["special_chars"] = "ÁÉÍÑÓÚÜáéíñóúü"
cat["level"] = 4
_add(cat)

# eu -------------------------------------------------
eu = deepcopy(empty)
eu["code"] = "eus"
eu["code2"] = "eu"
eu["name"] = "Basque"
eu["local"] = "Euskara"
eu["en"] = "Basque"
eu["level"] = 4
_add(eu)

# ga -------------------------------------------------
ga = deepcopy(empty)
ga["code"] = "irl"
ga["code2"] = "ga"
ga["name"] = "Irisch"
ga["local"] = "Irish"
ga["en"] = "Irish"
ga["level"] = 4
_add(ga)



# amh ---------------------------------------------------
amh = deepcopy(empty)
amh["code"] = "amh"
amh["code2"] = "am"
amh["name"] = "Ethiopisch"
amh["local"] = "Amarəñña"
amh["en"] = "Ethiopian"
amh["codepage"] = "utf-8"
amh["special_chars"] = ""
amh["level"] = 8
_add(amh)

# fil ---------------------------------------------------
fil = deepcopy(empty)
fil["code"] = "fil"
fil["code2"] = "fl"
fil["name"] = "Filipino"
fil["local"] = "Filipino"
fil["en"] = "Filipino"
fil["codepage"] = "iso-8859-1"
fil["level"] = 8
_add(fil)



""" old languages / not actively used """
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

