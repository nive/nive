
from nive.definitions import implementer, RootConf
from nive.components.iface.definitions import IIFaceRoot
from nive.container import Root


@implementer(IIFaceRoot)
class IfaceRoot(Root):
    """
    """

    def Init(self):
        pass


# Root definition ------------------------------------------------------------------
#@nive_module
configuration = RootConf(
    id = "iface",
    context = IfaceRoot,
    default = False,
    subtypes = "*",
    name = "Root",
    description = ""
)
