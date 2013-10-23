# -*- coding: utf-8 -*-
# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

# bw 0.9.11: select imports here for compatibility with previous versions
# This file has been split up :
#    -> first part is now in nive.components.baseobjects 
#    -> cms part is now in nive_cms.baseobjects 


from nive.components.baseobjects import (
        ApplicationBase,
        RootBase,
        RootReadOnlyBase,
        ObjectBase,
        ObjectReadOnlyBase,
        ObjectContainerBase,
        ObjectContainerReadOnlyBase
)

try:
    from nive_cms.baseobjects import (
            PageBase,
            PageRootBase,
            PageElementBase,
            PageElementFileBase,
            PageElementContainerBase,
            FolderBase
    )
except ImportError:
    pass