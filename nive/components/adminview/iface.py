
from nive.definitions import Conf

from nive.components.iface.definitions import IFaceConf
from nive.i18n import _


# iface configuration------------------------------------------------------------------
configuration = IFaceConf(
    name = "Kalender Administration",
    sections = (
        Conf(name=_("Basics"), ref="system", id="system"),
        Conf(name=_("Tools"), ref="sys-tools", id="sys-tools"),
        Conf(name=_("Modules"), ref="sys-modules", id="sys-modules",
             description=_("Read only listing of all registered modules and settings.")),
        Conf(name=_("Views"), ref="sys-views", id="sys-views",
             description=_("Read only listing of all registered views grouped by view modules.")),

        # Conf(name=_("Root"),      ref="sys-root", id="sys-root"),
        # Conf(name=_("Global"),    ref="sys-portal",       id="sys-portal"),

    ),
    backlink = Conf(id="root.",         name="Start"),
    headlink = Conf(id="/userdb/logout",name="Abmelden"),
    headoptions = (
    ),
    currentSection = "system",
    slogan = "Administration",
    static="nive.components.iface:static/",
    path = False
)

# navigation
configuration.navigation = (
    Conf(
        id = "root.view",
        name = "",
        widget = "navigation_section",
        links = (
            Conf(name=_("Basics"), id="system"),
            Conf(name=_("Tools"), id="sys-tools"),
            Conf(name=_("Modules"), id="sys-modules"),
            Conf(name=_("Views"), id="sys-views",)
        )
    )
)

# object defaults. can be replaced on type base.
configuration.tabs = ()
configuration.shortcuts = ()
configuration.settings = ()

# object fields
configuration.addflds = None
configuration.editflds = None
configuration.metaflds = None
configuration.dataflds = None

configuration.searchconf = Conf()


