# Copyright 2012-2020 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt

import inspect

from pyramid.httpexceptions import HTTPForbidden
from pyramid import renderers

from nive.definitions import ViewModuleConf, ViewConf, Conf, ModuleConf
from nive.definitions import IObject, IContainer
from nive.definitions import ConfigurationError

from nive.workflow import WorkflowNotAllowed
from nive.views import BaseView
from nive.components.reform.forms import MakeCustomizedViewForm
from nive.security import Allow, Everyone, Authenticated, ALL_PERMISSIONS
from nive.helper import ResolveName

from nive.i18n import _
import collections

# view module definition ------------------------------------------------------------------
"""

Setup module configuration in app: 
    # web api (view layer)
    "nive.components.webapi",
    "nive.components.webapi.view.stringRendererConf",

"""


# shortcut to add the context to view definitions.
_ic = "nive.definitions.IContainer"
_io = "nive.definitions.IObject"

#@nive_module
configuration = ViewModuleConf(
    id = "DatastoreAPIv1",
    name = "Data storage api",
    containment = "nive.application.Application",
    view = "nive.components.webapi.view.APIv1",
    views = (
        # container views ---------------------------------------------------------------------------
        # these views only apply to container like objects and root

        # add a new item
        ViewConf(name="newItem",    attr="newItem",    permission="api-newItem",     renderer="json",   context=_ic),
        # list and search
        ViewConf(name="list",       attr="listItems",  permission="api-list",        renderer="json",   context=_ic),
        ViewConf(name="search",     attr="search",     permission="api-search",      renderer="json",   context=_ic),
        # rendering
        ViewConf(name="subtree",    attr="subtree",    permission="api-subtree",     renderer="string", context=_ic),
        ViewConf(name="render",     attr="renderTmpl", permission="api-render",                         context=_ic ),
        # forms
        ViewConf(name="newItemForm",attr="newItemForm",permission="api-newItemForm", renderer="string", context=_ic),

        # object views ---------------------------------------------------------------------------
        # read
        ViewConf(name="getItem",    attr="getItem",    permission="api-getItem",     renderer="json",   context=_io),
        # update
        ViewConf(name="setItem",    attr="setContext", permission="api-setItem",     renderer="json",   context=_io),
        # delete
        ViewConf(name="deleteItem", attr="deleteItem", permission="api-deleteItem",  renderer="json",   context=_io),
        # rendering
        ViewConf(name="subtree",    attr="subtree",    permission="api-subtree",     renderer="string", context=_io),
        ViewConf(name="render",     attr="renderTmpl", permission="api-render",                         context=_io),
        # forms
        ViewConf(name="setItemForm",attr="setItemForm",permission="api-setItemForm", renderer="string", context=_io),
        # workflow
        ViewConf(name="action",     attr="action",     permission="api-action",      renderer="json",   context=_io),
        ViewConf(name="state",      attr="state",      permission="api-state",       renderer="json",   context=_io),
    ),
    acl = (
        (Allow, Everyone,       "api-getItem"),
        (Allow, Everyone,       "api-subtree"),
        (Allow, Everyone,       "api-render"),
        (Allow, Everyone,       "api-list"),
        (Allow, Everyone,       "api-search"),

        (Allow, Authenticated,  "api-newItem"),
        (Allow, Authenticated,  "api-newItemForm"),

        (Allow, "group:owner",  "api-setItem"),
        (Allow, "group:owner",  "api-setItemForm"),
        (Allow, "group:owner",  "api-deleteItem"),
        (Allow, "group:owner",  "api-action"),
        (Allow, "group:owner",  "api-state"),

        (Allow, "group:editor", ALL_PERMISSIONS),
        (Allow, "group:admin",  ALL_PERMISSIONS),
    )
)

DefaultMaxStoreItems = 50
DefaultMaxBatchItems = 100
jsUndefined = ("", "null", "undefined", None)


class APIv1(BaseView):

    # json datastore api

    def getItem(self):
        """
        Returns one or multiple items. This function either returns the current item if called without
        parameter or if `id` is passed as request form value one or multiple child items.

        **Request parameter:**

        - *id*: the items' id or a list of multiple items. leave empty to get the current
                item. Ignored if `strict` is true.

        Returns json encoded data

        **Settings:**

        - *toJson*: (list) fields included in json result. Can be type specific. The data fields included in the result are
                    rendered based on customized view settings or the types' default `toJson` value.
        - *render*: (list) list of fields to be rendered before being included in the result. The result depends on the
                    individual fields. E.g. list fields would be returned as readable name not the raw data value.
        - *strict*: (bool) If `True` only the single item matching the current url is included in the result.
        - *maxBatchItems*: (number) the maximum number of returned in one call
        - *deserialize*: (callback) pluginpoint for a custom deserialization callback. The callback is once for the whole result.
                         Takes two parameters `items, view` and should return the processed items.

        You can also turn on strict the mode. If turned on `getItem` can only be called for the
        object to be retrieved itself, not for the container.

        Customized `getItem` view ::

            bookmark = ViewConf(
                name="read-bookmark",
                attr="getItem",
                # ...
                settings={
                    "toJson": ("link", "share", "comment"),
                    "render": ("pool_create",),
                    "strict": True,
                }
            )

        To define the returned fields of multiple object types use a dict instead of a tuple and use the type id
        as key ::

            bookmark = ViewConf(
                name="read-bookmark",
                attr="getItem",
                # ...
                settings = {
                    "toJson": {"bookmark": ("link", "share", "comment")},
                    "strict": False
                }
            )

        To mix defaults for multiple types and specific fields for other types use `default__` as key. ::

            bookmark = ViewConf(
                name="read-bookmark",
                attr="getItem",
                # ...
                settings = {
                    "toJson": {
                        "default__": ("id", "pool_type"),
                        "bookmark": ("link", "share", "comment") },
                    "strict": False
                }
            )

        The default value for `toJson` is loaded from the types' ObjectConf.toJson settings ::

            collection1 = ObjectConf(
                id = "bookmark",
                #...
                toJson = ("link", "share", "comment"),
            )

        In all cases each returned json bookmark item contains the values for `link`, `share` and `comment`.
        """
        fields = render = deserialize = None
        strict = False
        maxBatchItems = self.context.app.configuration.get("maxBatchItems") or DefaultMaxBatchItems

        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            fields = viewconf.settings.get("toJson")
            strict = viewconf.settings.get("strict", False)
            render = viewconf.settings.get("render")
            deserialize = viewconf.settings.get("deserialize")
            maxBatchItems = viewconf.settings.get("maxBatchItems") or maxBatchItems

        # lookup the id in the current form submission. if not none try to load and update the
        # child with id=id
        id = self.GetFormValue("id")
        if id is None or strict:
            # return only the single item matching the current url
            item = self.context
            return DeserializeItems(self, item, fields)[0]

        if not isinstance(id, (list,tuple)):
            try:
                id = [int(id)]
            except (ValueError, TypeError):
                # set http response code (invalid request)
                self.request.response.status = "400 Invalid id"
                return {"error": "Invalid id"}

        if isinstance(id, (list, tuple)) and len(id)==0:
            # set http response code (invalid request)
            self.request.response.status = "400 Empty id"
            return {"error": "Empty id"}

        items = []
        cnt = 0
        for obj in self.context.GetObjsBatch(id):
            if not self.Allowed("api-getItem", obj):
                # fails silently in list mode
                continue
            items.append(obj)
            if len(items) == maxBatchItems:
                break

        # turn into json
        items = DeserializeItems(self, items, fields, render)
        if isinstance(deserialize, collections.abc.Callable):
            return deserialize(items, self)
        return items


    def newItem(self):
        """
        Creates a single item or a set of items as batch. Values are serialized and
        validated by 'newItem' form subset or the form setup configured for the customized view.

        **Request parameter:**

        - *type*: the new type to be created. Must be set for each item.
        - *<fields>*: A single item can be passed directly as form values without wraping it as `items`.
        - *items*: One or multiple items to be stored. Multiple items have to be passed as array.

        Returns json encoded result: {"result": list of new item ids}

        **Settings:**

        - *type*: (string/tuple) the type id created by the function. If set the type id passed in the request must match
                  the settings. Use a tuple to allow multiple type ids.
        - *form*: (dict) form setup for validation settings. If not set the default form setup is loaded from the types'
                  configuration.
        - *values*: (dict) a slot for default values not part of the form.
        - *maxStoreItems*: (number) the maximum number of items stored in one call.
        - *serialize*: (callback) pluginpoint for a custom serialization callback. The callback is invoked before each item is created.
                       Takes three parameters `data, typename, view` and should return the processed data dict. If  `ValueError`
                       is raised the item is skipped and the next is processed.

        Customized `newItem` view example ::

            bookmark = ViewConf(
                name="add-bookmark",
                attr="newItem",
                # ...
                settings={"form": {"fields": ("link", "share", "comment")},
                          "type": "bookmark",
                          "maxStoreItems": 3,
                          "values": {"source": "webapi"}
                }
            )

        The default `forms` setting is loaded from the types' ObjectConf.forms settings for `newItem` ::

            collection1 = ObjectConf(
                id = "bookmark",
                # ...
                forms = {
                    "newItem": {"fields": ("link", "share", "comment"),
                                "defaults": {"share": True}},
                },
                # ...
            )

        In all examples `newItem` validates and stores 3 form fields: `link, share, comment`.

        If you are using the default `newItem` view you have to pass the type id to be
        created by the function as form parameter ``type=bookmark``. If you are using a customized
        view the type can be part of the views options slot ``settings={"type": "bookmark"}``.
        """
        # lookup settings
        typename = ""
        values = serialize = None
        subset = "newItem"
        maxStoreItems = self.context.app.configuration.get("maxStoreItems") or DefaultMaxStoreItems

        # look up the new type and validation fields in custom view definition
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            typename = viewconf.settings.get("type")
            values = viewconf.settings.get("values")
            serialize = viewconf.settings.get("serialize")
            subset = viewconf.settings.get("form") or subset
            maxStoreItems = viewconf.settings.get("maxStoreItems") or maxStoreItems

        user = self.User()
        response = self.request.response
        items = self.GetFormValue("items")
        if not items:
            # create a single item
            data = self.GetFormValues()
            if not typename:
                typename = data.get("type") or data.get("pool_type")
                if not typename:
                    response.status = "400 No type given"
                    return {"error": "No type given", "result":[]}
            typeconf = self.context.app.configurationQuery.GetObjectConf(typename)
            if not typeconf:
                response.status = "400 Unknown type"
                return {"error": "Unknown type", "result":[]}

            # set up the form. subset might be the form configuration up to here.
            form, subset = MakeCustomizedViewForm(view=self,
                                                  forContext=self.context,
                                                  formSettingsOrSubset=subset,
                                                  typeconf=typeconf,
                                                  defaultSettings=self._formDefaults("newItem"),
                                                  loadFromViewModuleConf=self.configuration)
            form.Setup(subset=subset)
            result, data, errors = form.ValidateSchema(data)
            if not result:
                response.status = "400 Validation error"
                return {"error": str(errors), "result":[]}

            #values = SerializeItem(self, values, typeconf)
            if isinstance(values, dict):
                data.update(values)
            item = self.context.Create(typename, data=data, user=user)
            if not item:
                response.status = "400 Validation error"
                return {"error": "Validation error", "result":[]}
            return {"result": [item.id]}

        if len(items) > maxStoreItems:
            response.status = "413 Too many items"
            return {"error": "Too many items.", "result":[]}

        validated = []
        errors = []
        cnt = 0
        for data in items:
            cnt += 1
            if isinstance(typename, (list, tuple)):
                tn = data.get("type") or data.get("pool_type")
                if not tn in typename:
                    errors.append("Invalid type: "+tn)
                    continue
            else:
                tn = typename or data.get("type") or data.get("pool_type")

            if not tn:
                errors.append("No type given: "+str(cnt))
                continue

            typeconf = self.context.app.configurationQuery.GetObjectConf(tn)
            if not typeconf:
                errors.append("Unknown type")
                continue

            # set up the form. subset might be the form configuration up to here.
            form, subset = MakeCustomizedViewForm(view=self,
                                                  forContext=self.context,
                                                  formSettingsOrSubset=subset,
                                                  typeconf=typeconf,
                                                  defaultSettings=self._formDefaults("newItem"),
                                                  loadFromViewModuleConf=self.configuration)
            form.Setup(subset=subset)
            result, data, err = form.ValidateSchema(data)
            if not result:
                if isinstance(err, list):
                    errors.extend(err)
                elif err is not None:
                    errors.append(str(err))
                continue

            if isinstance(values, dict):
                data.update(values)
            if isinstance(serialize, collections.abc.Callable):
                try:
                    data = serialize(data, tn, self)
                except ValueError:
                    continue
            item = self.context.Create(tn, data=data, user=user)
            if item:
                validated.append(item.id)

        return {"result": validated, "error": errors}


    def setItem(self):
        """
        Store a single item or a set of items as batch. Values are serialized and
        validated by 'setItem' form subset or the form setup configured for the customized view.

        **Request parameter:**
        
        - *<fields>*: A single item can be passed as form values.
        - *items*: One or multiple items to be stored. Multiple items have to be passed as array.
          
        Returns json encoded result: {"result": list of stored item ids}

        **Settings:**

        - *strict*: (bool) If `True` only the single item matching the current url will be updated.
        - *form*: (dict) form setup for validation settings. If not set the default form setup is loaded from the types'
                  configuration.
        - *values*: (dict) a slot for default values not part of the form
        - *maxStoreItems*: (number) the maximum number of items store in one call
        - *serialize*: (callable) pluginpoint for a custom serialization callback. The callback is invoked before each item is created.
                       Takes three parameters `data, typename, view` and should return the processed data dict.

        You can also turn on strict the mode. If turned on `setItem` can only be called for the
        object to be updated itself, not for the container.

        Customized `setItem` view ::

            bookmark = ViewConf(
                name="update-bookmark",
                attr="setItem",
                ...
                settings = {
                    "form": {"fields": ("link", "share", "comment"),
                             "defaults": {"share": True}},
                    "strict": True
                }
            )

        The default `forms` setting is loaded from the types' ObjectConf.forms settings for `setItem` ::

            collection1 = ObjectConf(
                id = "bookmark",
                # ...
                forms = {
                    "setItem": {"fields": ("link", "share", "comment")},
                },
                # ...
            )

        In all examples `setItem` validates and stores 3 form fields: `link, share, comment`.
        """
        # lookup subset
        values = serialize = None
        strict = False
        subset = "setItem"
        maxStoreItems = self.context.app.configuration.get("maxStoreItems") or DefaultMaxStoreItems

        # look up the new type in custom view definition
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            values = viewconf.settings.get("values")
            serialize = viewconf.settings.get("serialize")
            strict = viewconf.settings.get("strict")
            subset = viewconf.settings.get("form") or subset
            maxStoreItems = viewconf.settings.get("maxStoreItems") or maxStoreItems


        items = self.GetFormValue("items")
        if strict or items is None:
            if strict:
                setObject = self.context
            else:
                # lookup id in form values
                id = self.GetFormValue("id")
                if id:
                    setObject = self.context.obj(id)
                else:
                    setObject = self.context
            if not setObject:
                self.request.response.status = "404 Not found"
                return {"error": "Not found", "result": []}
            if not self.Allowed("api-setItem", setObject):
                self.request.response.status = "403 Not allowed"
                return {"error": "Not allowed", "result": []}

            typeconf = setObject.configuration
            # set up the form. subset might be the form configuration up to here.
            form, subset = MakeCustomizedViewForm(view=self,
                                                  forContext=setObject,
                                                  formSettingsOrSubset=subset,
                                                  typeconf=typeconf,
                                                  defaultSettings=self._formDefaults("setItem"),
                                                  loadFromViewModuleConf=self.configuration)
            form.Setup(subset=subset)
            result, data, errors = form.ValidateSchema(self.GetFormValues())
            if not result:
                self.request.response.status = "400 Validation error"
                return {"error": errors, "result": []}
            # update configured values
            if values is not None:
                data.update(values)
            # callback if set
            if isinstance(serialize, collections.abc.Callable):
                data = serialize(data, typeconf.id, self)
            result = setObject.Update(data=data, user=self.User())
            return {"result": result}

        response = self.request.response
        user = self.User()

        if not items or isinstance(items, dict):
            response.status = "400 Validation error"
            return {"error": "items: Not a list", "result": []}

        if len(items) > maxStoreItems:
            response.status = "413 Too many items"
            return {"error": "Too many items.", "result": []}
        
        validated = []
        errors = []
        cnt = 0
        for data in items:
            cnt += 1
            id = data.get("id")
            if not id:
                errors.append("No id given: Item number "+str(cnt))
                continue
            item = self.context.GetObj(id)
            if not item:
                errors.append("Not found: Item id "+str(id))
                continue

            typeconf = item.configuration
            # set up the form. subset might be the form configuration up to here.
            form, subset = MakeCustomizedViewForm(view=self,
                                                  forContext=item,
                                                  formSettingsOrSubset=subset,
                                                  typeconf=typeconf,
                                                  defaultSettings=self._formDefaults("setItem"),
                                                  loadFromViewModuleConf=self.configuration)
            form.Setup(subset=subset)
            result, data, err = form.ValidateSchema(data)
            if not result:
                if isinstance(err, list):
                    errors.extend(err)
                else:
                    errors.append(str(err))
                continue

            if not self.Allowed("api-setItem", item):
                errors.append("Not allowed: Item id "+str(id))
                continue

            if values is not None:
                data.update(values)
            result = item.Update(data=data, user=user)
            if result:
                validated.append(id)

        return {"result": validated, "error": errors}

    
    def deleteItem(self):
        """
        Delete one or more items.

        For customized views you change the behaviour whether contained objects are removed
        recursively or not. By default recursive is True.

        You can also turn on strict the mode. If turned on `deleteItem` can only be called for the
        object to be deleted itself, not for the container.

        Another supported option is a confirmation id. If used the item will only be deleted if the
        confirmation is present in the request. In combination with template renderers you can easily
        build a confirmation dialog box to get input from the user. By default `confirm` is None.

        **Request parameter:**

        - *id*: (number,list) the items' id or a list of ids if `strict` is set to `False`
        - *confirmation*: the confirmation token if enabled.

        Returns json encoded result: {"result": list of deleted item ids}

        **Settings:**

        - *strict*: (bool) If `True` only the single item matching the current url will be updated.
        - *recursive*: (bool) If `False` deleteItem will not remove container items havng children.
        - *confirmation*: (string) a confirmation token required to be passed in the request.
        - *maxDeleteItems*: (number) the maximum number of items deleted in one call. Recursively deleted
                            items are not counted.

        You can also turn on strict the mode. If turned on `setItem` can only be called for the
        object to be updated itself, not for the container.

        1) Customized `deleteItem` view ::

            bookmark = ViewConf(
                name="delete-bookmark",
                attr="deleteItem",
                ...
                settings = {
                    "strict": True,
                    "recursive": False,
                    "confirm": "g3d4ea8b1",
                    "maxDeleteItems": 3
                }
            )

        """
        response = self.request.response
        maxStoreItems = self.context.app.configuration.get("maxStoreItems") or DefaultMaxStoreItems
        strict = False
        recursive = True
        confirmation = None
        root = self.context.root

        # look up the new type in custom view definition
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            strict = viewconf.settings.get("strict")
            recursive = viewconf.settings.get("recursive")
            confirmation = viewconf.settings.get("confirmation")
            maxStoreItems = viewconf.settings.get("maxDeleteItems") or maxStoreItems

        if confirmation and self.GetFormValue("confirmation")!=confirmation:
            return {"result": [], "error": "Please confirm."}

        if strict:
            # delete the context itself
            user = self.User()
            obj = self.context
            if not recursive:
                sub = root.search.Select(parameter={"pool_unitref":obj.id}, fields=["id"], max=2)
                if sub:
                    # not empty -> return
                    return {"result": [], "error": "Not empty"}
            id = obj.id
            result = self.context.parent.Delete(obj, user=user)
            #del obj
            if result:
                return {"result": [id]}
            return {"result": [], "error": "Sorry. Delete failed."}

        else:
            ids = self.GetFormValue("id")

        if not ids:
            # set http response code (invalid request)
            response.status = "400 Empty id"
            return {"error": "Empty id", "result": []}

        if not isinstance(ids, list):
            try:
                ids = [int(ids)]
            except ValueError:
                # set http response code (invalid request)
                response.status = "400 Invalid id"
                return {"error": "Invalid id.", "result": []}

        if len(ids) > maxStoreItems:
            response.status = "413 Too many items"
            return {"error": "Too many items.", "result": []}

        deleted = []
        error = ""
        user = self.User()
        for obj in self.context.GetObjsBatch(ids):
            if not self.Allowed("api-delete", obj):
                error = "Not allowed"
                continue
            if not recursive:
                sub = root.search.Select(parameter={"pool_unitref":obj.id}, fields=["id"], max=2)
                if sub:
                    # not empty -> continue
                    error = "Not empty"
                    continue
            id = obj.id
            result = self.context.Delete(obj, user=user)
            del obj
            if result:
                deleted.append(id)

        return {"result": deleted, "error": error}
            

    # list and search ----------------------------------------------------------------------------------

    def listItems(self):
        """
        Returns a list of batched items for a single or all types stored in the current container.
        Fast and efficient listing function. `listItems` uses the access permissions of the container and
        does not check access permissions for items included in the result.
        The result can only inlcude meta layer fields and type fields for a single type.

        For an advanced listing function use `subtree` or `search`.

        **Request parameter:**

        - *sort*: sort field. a meta field or if type is not empty, one of the types fields.
        - *order*: '<','>'. order the result list based on values ascending '<' or descending '>'
        - *size*: number of batched items. maximum is 100.
        - *start*: start number of batched result sets.

        Returns json encoded result set: {"items":[[item values], [item values]], "start":number}

        **Settings:**

        - *type*: (string) the type id to load data fields from. Can be empty if only meta fields are included
                  in the result.
        - *fields*: (list) fields included in json result. Either meta layer field ids or type specific fields
                    for a single type.
        - *maxBatchItems*: (number) the maximum number of returned in one call
        - *deserialize*: (callback) pluginpoint for a custom deserialization callback. The callback is invoked once for
                         the whole result.
                         Takes two parameters `items, view` and should return the processed items.

        Customized `listItems` view ::

            bookmark = ViewConf(
                name="list-bookmark",
                attr="listItems",
                ...
                settings = {
                    "fields": ("link", "share", "comment", "pool_create"),
                    "type": "bookmark"
                }
            )


        """
        response = self.request.response
        typename = deserialize = None
        maxBatchItems = self.context.app.configuration.get("maxBatchItems") or DefaultMaxBatchItems
        fields = ("id",)
        viewconf = self.GetViewConf()
        sort = None
        order = None
        if viewconf and viewconf.get("settings"):
            fields = viewconf.settings.get("fields") or fields
            typename = viewconf.settings.get("type")
            deserialize = viewconf.settings.get("deserialize")
            maxBatchItems = viewconf.settings.get("maxBatchItems") or maxBatchItems
            sort = viewconf.settings.get("sort")
            order = viewconf.settings.get("order")

        values = self.GetFormValues()
        typename = typename or values.get("type") or values.get("pool_type")

        try:
            start = ExtractJSValue(values, "start", 0, "int")
        except ValueError:
            # set http response code (invalid request)
            response.status = "400 Invalid parameter"
            return {"error": "Invalid parameter: start", "items": []}

        try:
            size = ExtractJSValue(values, "size", maxBatchItems, "int")
            if size > maxBatchItems:
                size = maxBatchItems
        except ValueError:
            # set http response code (invalid request)
            response.status = "400 Invalid parameter"
            return {"error": "Invalid parameter: size", "items": []}

        order = values.get("order", order)
        if order == "<":
            ascending = 1
        else:
            ascending = 0

        sort = values.get("sort", sort)
        if not sort in [v["id"] for v in self.context.app.configurationQuery.GetAllMetaFlds(False)]:
            if typename:
                if self.context.app.configurationQuery.GetObjectConf(typename) is None:
                    raise TypeError("unknown type")
                if not sort in [v["id"] for v in self.context.app.configurationQuery.GetAllObjectFlds(typename)]:
                    sort = None

        parameter = {"pool_unitref": self.context.id}
        data = self.context.root.search.Select(typename,
                                              parameter=parameter,
                                              fields=fields,
                                              start=start,
                                              max=size,
                                              ascending=ascending,
                                              sort=sort)
        if isinstance(deserialize, collections.abc.Callable):
            data = deserialize(data, self)
        return {"items": data, "start": start}


    def search(self):
        """
        Advanced search functions with many optionsand support for preconfigured search
        profiles. The functions returns a set of batched items encoded as json.

        Search profiles can be preconfigured and stored in the datastore application configuration or
        for each customized view.

        **Request parameter**

        - *profile*: (string) the search profile name if not set in the configuration.

        All other values extracted from the request and used in the search as parameter or batching, sort, order have to be
        defined in the configuration as `settings["dynamic"] = {}` values.

        **Return value**

        - *items*: list of items
        - *start*: if batched the current start number
        - *size*: maximum batch size
        - *total*: number of items in total
        - *fields*: (list) a list of data fields used in search

        The return value is based on the linked renderer. By default the result is returned as json
        encoded result set: ::

            {"items":[items], "start":number, "size":number, "total":number}

        **Settings:**

        - *sort*: (string) is a field name and used to sort the result.
        - *order*: (string) either '<','>' or empty. Orders the result list based on values ascending '<' or descending '>'
        - *size*: (number) number of batched items.
        - *start*: (number) start number of batched result sets.
        - *type*: (string) type id. If ``type`` is not empty this function uses `nive.search.SearchType`, if empty `nive.search.Search`.
                  The data fields to be included in the result have to be assigned respectively. In other words
                  if `type` is given the types data fields can be included in the result, otherwise not.
        - *container*: (bool) determines whether to search in the current container or search all items in the tree.
        - *fields*: (list) a list of data fields to be included in the result set. See `nive.search`.
        - *parameter*: (dict/callback) is a dictionary or callable of fixed query parameters used in the select statement. These values cannot
                       be changed through request form values. The callback takes two parameters `context` and `request` and should return
                       a dictionary. E.g. ::

                           def makeParam(context, request):
                               return {"id": context.id}

                           settings = {
                               # ...
                               # adds the contexts file as parameter
                               "parameter": makeParam,
                               # ...
                           }

                       or as inline function definition ::

                           settings = {
                               # ...
                               # adds the contexts file as parameter
                               "parameter": lambda context, request, view: {"id": context.id},
                               # ...
                           }

        - *dynamic*: (dict) these values are extracted from the request. The values listed here are the defaults
                     if not found in the request. The `dynamic` values are mixed with the fixed parameters and passed
                     to the query. If you need custom value processing use a callback with the `parameter` option.
        - *operators*: (dict) fieldname:operator entries used for search conditions. See `nive.search`.
        - *ignoreEmpty*: (bool) automatically removes empty dynamic values and so these are not included in select statements.
        - *advanced*: (dict) search options like group restraints. See `nive.search` for details and all supported options.
        - *groups*: (string/list) use the groups defintion to restrict the execution to users assigned to one of the groups.
                    For customized views it is recommended to use the view permissions directly.
        - *deserialize*: (callback) pluginpoint for a custom deserialization callback. The callback is invoked once for
                         the whole result.
                         Takes two parameters `items, view` and should return the processed items.

        Here is a simple example how to search for all bookmarks ::

            settings = {
                "type": "bookmark",
                "container": False,
                "fields": ["id", "link", "comment"],
                "parameter": {"share": True},
                "dynamic": {"start": 0},
                "sort": "pool_change",
                "order": "<",
                "size": 30,
            }

        The same example extended with text search in comment. This one allows you to pass in a text matched against
        the comment field of each bookmark ::

            settings = {
                "type": "bookmark",
                "container": False,
                "fields": ["id", "link", "comment"],
                "parameter": {"share": True},
                "dynamic": {"start": 0, "text": ""},
                "operators": {"text": "LIKE"},
                "sort": "pool_change",
                "order": "<",
                "size": 30,
            }

        The system provides two options to configure search profiles. The first one uses the application configuration ::

            datastore = AppConf(
                search = {
                    # the default profile if no name is given
                    "default": {
                        # profile values go here
                    },
                    "extended": {
                        # profile values go here
                    },
                }
            )

        To use the `extended` profile pass the profiles name as query parameter
        e.g. `http://myapp.com/storage/search?profile=extended`. This way search will always return json.

        The second option is to add a custom view based on `search`. This way you can add a custom renderer,
        view name and permissions ::

            search = ViewConf(
                name="list",
                attr="search",
                context="nive.root.Root",
                permission="view",
                renderer="myapp:templates/list.pt",
                settings = {
                    # search profile values go here
                }
            )

        """
        response = self.request.response
        profile = deserialize = None
        maxBatchItems = self.context.app.configuration.get("maxBatchItems") or DefaultMaxBatchItems

        viewconf = self.GetViewConf()
        # look up the profile in two places
        if viewconf and viewconf.get("settings"):
            maxBatchItems = viewconf.settings.get("maxBatchItems") or maxBatchItems
            deserialize = viewconf.settings.get("deserialize")
            # 1) in custom view definition
            profile = viewconf.settings

        else:
            # 2) in app.configuration.search
            profiles = self.context.app.configuration.get("search")
            if not profiles:
                response.status = "400 No search profiles found"
                return {"error": "No search profiles found", "items":[]}

            profilename = self.GetFormValue("profile", "default")
            if not profilename:
                response.status = "400 Empty search profile name"
                return {"error": "Empty search profile name", "items":[]}
            profile = profiles.get(profilename)
            if not profile:
                response.status = "400 Unknown profile"
                return {"error": "Unknown profile", "items":[]}

        if profile.get("groups"):
            grps = profile.get("groups")
            user = self.User()
            #TODO check local groups
            if not user or not user.InGroups(grps):
                raise HTTPForbidden("Profile not allowed")

        # get dynamic values
        values = {}
        web = self.GetFormValues()
        dynamic = profile.get("dynamic", {})
        if dynamic:
            ie = profile.get("ignoreEmpty")
            # values treated as empty
            null = ("", None)
            for dynfield, dynvalue in list(dynamic.items()):
                value = web.get(dynfield, dynvalue)
                if value in null:
                    continue
                values[dynfield] = value

        if "start" in dynamic:
            try:
                start = ExtractJSValue(values, "start", 0, "int")
            except ValueError:
                # set http response code (invalid request)
                response.status = "400 Invalid parameter"
                return {"error": "Invalid parameter: start", "items":[]}
            del values["start"]
        else:
            start = profile.get("start",0)

        if "size" in dynamic:
            try:
                size = ExtractJSValue(values, "size", maxBatchItems, "int")
                if size > maxBatchItems:
                    size = maxBatchItems
            except ValueError:
                # set http response code (invalid request)
                response.status = "400 Invalid parameter"
                return {"error": "Invalid parameter: size", "items":[]}
            del values["size"]
        else:
            size = profile.get("size", maxBatchItems)

        if "order" in dynamic:
            order = values.get("order",None)
            del values["order"]
        else:
            order = profile.get("order")
        if order == "<":
            ascending = 1
        elif order == ">":
            ascending = 0
        else:
            ascending = None

        # fixed values
        typename = profile.get("type") or profile.get("pool_type")

        if "sort" in dynamic:
            sort = values.get("sort",None)
            if not sort in [v["id"] for v in self.context.app.configurationQuery.GetAllMetaFlds(False)]:
                if typename:
                    if not sort in [v["id"] for v in self.context.app.configurationQuery.GetAllObjectFlds(typename)]:
                        sort = None
            del values["sort"]
        else:
            sort = profile.get("sort")

        # get the configured parameters. if it is a callable call it with current
        # request and context.
        p = profile.get("parameter", None)
        if isinstance(p, collections.abc.Callable):
            if "view" in inspect.getfullargspec(p).args:
                p = p(*(self.context, self.request, self))
            else:
                p = p(*(self.context, self.request))
        if p:
            values.update(p)

        if profile.get("container"):
            values["pool_unitref"] = self.context.id
        parameter = values
        operators = profile.get("operators")
        fields = profile.get("fields")

        # prepare keywords
        kws = {}
        if profile.get("advanced"):
            kws.update(profile["advanced"])

        if start is not None and start!=0:
            # Search Functions use 0 based index, search 1 based index
            kws["start"] = start-1
        if size is not None:
            kws["max"] = size
        if ascending is not None:
            kws["ascending"] = ascending
        if sort is not None:
            kws["sort"] = sort

        # run the query and handle the result
        if typename:
            result = self.context.root.search.SearchType(typename, parameter=parameter, fields=fields, operators=operators, **kws)
        else:
            result = self.context.root.search.Search(parameter=parameter, fields=fields, operators=operators, **kws)
        values = {"items": result["items"],
                  "start": result["start"]+1,
                  "size": result["count"],
                  "total": result["total"],
                  "fields": fields}
        if isinstance(deserialize, collections.abc.Callable):
            values["items"] = deserialize(result["items"], self)
        return values


    # tree renderer ----------------------------------------------------------------------------------

    def subtree(self):
        """
        Returns complex results like parts of a subtree including multiple levels. Contained items
        can be accessed through `items` in the result. `subtree` uses the items configuration
        `render` option to determine the result values rendered in a json document. If `render` is None the item will
        not be rendered at all.

        **Request parameter**

        - *profile*: (string) the subtree profile name if not set in the configuration.

        **Return values**

        The return value is based on the linked renderer. By default the result is returned as json
        encoded result set: ::

            {"items": {"items": {<values>}, <values>}, <values>}

        **Settings**

        - *levels*: (number) the number of levels to include, 0=include all (default)
        - *secure*: (bool) if true the `api-subtree` permission is checked for each item
        - *descent*: (item type, interface) item types or interfaces to descent into subtree e.g. `(IContainer,)`
        - *toJson*: (dict or tuple) result values. If empty uses the types `toJson` defaults
        - *parameter*: (dict) query parameter for result selection e.g. `{"pool_state": 1}`
        - *addContext*: (bool) adds the item object as `context` to the result

        A simple configuration looks as follows ::

            settings = {
                "levels": 0,
                "descent": (IContainer,),
                "toJson": {"bookmark": ("comment", share")},
                "parameter": {"pool_state": 1}
            }

        The system provides two options to configure subtree profiles. The first one uses the application configuration ::

            datastore = AppConf(
                subtree = {
                    # the default profile if no name is given
                    "default": {
                        # profile values go here
                    },
                    "extended": {
                        # profile values go here
                    },
                }
            )

        To use the `extended` profile pass the profiles name as query parameter
        e.g. `http://myapp.com/storage/subtree?profile=extended`. In this case `subtree()` will always return json.

        The second option is to add a custom view based on `subtree`. This way you can add a custom renderer,
        view name and permissions::

            subtree = ViewConf(
                name="tree",
                attr="subtree",
                context="nive.root.Root",
                permission="view",
                renderer="myapp:templates/tree.pt",
                settings={
                    # subtree profile values go here
                }
            )

        """

        profile = None
        viewconf = self.GetViewConf()

        if viewconf and viewconf.get("settings"):
            # look up the profile in two places
            # 1) in custom view definition
            profile = viewconf.settings
        else:
            # 2) in app.configuration.search
            def returnError(error, status):
                #data = json.dumps(error)
                #return self.SendResponse(data, mime="application/json", raiseException=False, status=status)
                self.request.response.status = status
                return error

            profiles = self.context.app.configuration.get("subtree")
            if not profiles:
                status = "400 No subtree profile found"
                return returnError({"error": "No subtree profile found"}, status)

            profilename = self.GetFormValue("profile") or self.context.app.configuration.get("defaultSubtree")
            if not profilename:
                status = "400 Empty subtree profile name"
                return returnError({"error": "Empty subtree profile name"}, status)
            profile = profiles.get(profilename)
            if not profile:
                status = "400 Unknown profile"
                return returnError({"error": "Unknown profile"}, status)

        if isinstance(profile, dict):
            profile = Conf(**profile)

        values = self._renderTree(self.context, profile)
        return values


    def _renderTree(self, context, profile):
        # cache field ids and types
        fields = {}
        for conf in context.app.configurationQuery.GetAllObjectConfs():
            if isinstance(profile.get("toJson"), dict) and conf.id in profile.get("toJson"):
                # custom list of fields in profile for type 
                fields[conf.id] = profile.get("toJson")[conf.id]
                continue
            # use type default
            render = conf.get("toJson")
            if not render:
                continue
            fields[conf.id] = render
        
        # prepare parameter
        parameter = {}
        if profile.get("parameter"):
            parameter.update(profile.parameter)
        if not "pool_type" in parameter:
            parameter["pool_type"] = list(fields.keys())
        
        # prepare types to descent in tree structure
        temp = profile.get("descent",[])
        descenttypes = []
        for t in temp:
            resolved = ResolveName(t)
            if resolved:
                descenttypes.append(resolved)
            elif t in parameter["pool_type"]:
                descenttypes.append(t)
        if "pool_type" in parameter and isinstance(parameter["pool_type"], (list,tuple)):
            operators={"pool_type":"IN"}
        else:
            operators = {}
        if profile.get("operators"):
            operators.update(profile.operators)
            
        # lookup levels
        levels = profile.get("levels")
        if levels is None:
            levels = 10000

        def itemValues(item):
            iv = {}
            if item.IsRoot():
                return iv
            name = item.GetTypeID()
            if profile.get("addContext"):
                iv["context"] = item
            if not name in fields:
                return iv
            for field in fields[item.GetTypeID()]:
                iv[field] = item.GetFld(field)
            return iv
        
        _c_descent = [[],[]]
        def descent(item):
            # cache values: first list = descent, second list = do not descent
            t = item.GetTypeID()
            if t in _c_descent[0]:
                return True
            if t in _c_descent[1]:
                return False
            
            for t in descenttypes:
                if isinstance(t, str):
                    if item.GetTypeID()==t:
                        if not t in _c_descent[0]:
                            _c_descent[0].append(t)
                        return True
                else:
                    if t.providedBy(item):
                        if not t in _c_descent[0]:
                            _c_descent[0].append(item.GetTypeID())
                        return True
            if not t in _c_descent[1]:
                _c_descent[1].append(item.GetTypeID())
            return False
            
        def itemSubtree(item, lev, includeSubtree=False):
            if profile.get("secure",True) and not self.request.has_permission("api-subtree", item):
                return {}
            current = itemValues(item)
            if (includeSubtree or descent(item)) and lev>0 and IContainer.providedBy(item):
                lev -= 1
                current["items"] = []
                items = item.GetObjs(parameter=parameter, operators=operators)
                for i in items:
                    current["items"].append(itemSubtree(i, lev))
            return current

        return itemSubtree(context, levels, includeSubtree=True)
        
    
    # form rendering ------------------------------------------------------------

    def newItemForm(self):
        """
        Renders and executes a web form based on the configured form setup. All form validation and processing is handled
        automatically and if the processing succeeds the new item will be stored with the values submitted.

        The form setup requires the items type either passed in the request or configured as part of the settings.

        **Request parameter**

        - *assets*: You can call `newItemForm?assets=only` to get the required css+js assets only. The form
                    iteself will not be processed. Use this in combination with `settings["includeAssets"] = False`
                    for single page applications or to load assets only once.

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.

        **Settings**

        - *type*: (string) type id of new item to be created. if empty type is extracted from request.
        - *form*: (dict/string) the form setup as form definition including form fields and options or the subset
                  to be loaded from the types configuration settings. This slot supports all `nive.HTMLForm` options
        - *values*: (dict) additional values used for the new item. These values are independent from fields or
                    form defaults.
        - *includeAssets*: (bool) include js/css assets required by the form in the html markup. default true.

        For example the configuration for a new item form might loook like ::

            settings = {
                "form": {"fields": ("link", "share", "comment"),
                         "use_ajax": True}
                "type": "bookmark",
                "includeAssets": False,
                "values": {"source": "webform"}
            }

        Configuration lookup order :

        1) Customized `newItemForm` view ::

            bookmark = ViewConf(
                name="add-bookmark",
                attr="newItemForm",
                # ...
                settings={"form": {"fields": ("link", "share", "comment"),
                                   "use_ajax": True}
                          "type": "bookmark",
                          "values": {"source": "webform"}
                }
            )

        2) The types' ObjectConf.forms settings for `newItem`  ::

            collection1 = ObjectConf(
                id = "bookmark",
                # ...
                forms = {
                    "newItem": {"fields": ("link", "share", "comment"),
                                "use_ajax": True},
                    "setItem": {"fields": ("link", "share", "comment"),
                                "use_ajax": True}
                },
                # ...
            )

        defines the `newItem` form in both cases with 3 form fields and to use ajax submissions ::
        
            {"fields": ("link", "share", "comment"), "use_ajax": True}

        If you are using the default `newItemForm` view you have to pass the type id to be
        created by the function as form parameter ``type=bookmark``. If you are using a customized
        view the type can be part of the views options slot ``settings={"type": "bookmark"}``.
        
        To get required assets in a seperate call use `?assets=only` as query parameter. This will
        return the required css and js assets for the specific form only.
        """
        typename = subset = ""
        values = redirectSuccess = defaults = None
        includeAssets = True
        # look up the new type in custom view definition
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            typename = viewconf.settings.get("type")
            subset = viewconf.settings.get("form") or "newItem"
            values = viewconf.settings.get("values")
            redirectSuccess = viewconf.settings.get("redirectSuccess")
            includeAssets = viewconf.settings.get("includeAssets", includeAssets)
        else:
            subset = self.GetFormValue("subset") or "newItem"

        if not typename:
            typename = self.GetFormValue("type") or self.GetFormValue("pool_type")
            if not typename:
                self.AddHeader("X-Result", "false")
                return {"content": "Type is empty"}

        typeconf = self.context.app.configurationQuery.GetObjectConf(typename)

        # set up the form. subset might be the form configuration up to here.
        form, subset = MakeCustomizedViewForm(view=self,
                                              forContext=self.context,
                                              formSettingsOrSubset=subset,
                                              typeconf=typeconf,
                                              defaultSettings=self._formDefaults("newItem"),
                                              loadFromViewModuleConf=self.configuration)
        form.Setup(subset=subset, addTypeField=True)

        if self.GetFormValue("assets")=="only":
            self.AddHeader("X-Result", "true")
            return {"content": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets])}

        # process and render the form.
        result, data, action = form.Process(pool_type=typename, defaults=defaults, values=values, redirectSuccess=redirectSuccess)
        if IObject.providedBy(result):
            result = result.id

        self.AddHeader("X-Result", str(result).lower())
        if includeAssets:
            # if assets are enabled add required js+css for form except those defined
            # in the view modules asset list
            head = form.HTMLHead(ignore=[a[0] for a in self.configuration.assets])
            return {"content": head+data}

        return {"content": data}


    def setItemForm(self):
        """
        Renders and executes a web form based on the configured form setup. All form validation and processing is handled
        automatically and if the processing succeeds the item will be updated with the values submitted.

        **Request parameter**

        - *assets*: You can call `setItemForm?assets=only` to get the required css, js assets only. The form
                    iteself will not be processed. Use this in combination with `settings["includeAssets"] = False`
                    for single page applications or to load assets only once.

        **Return values**

        - *body*: This function returns rendered html code as body.
        - *X-Result header*: http header indicating whether the new item has been created or not.

        **Settings**

        - *form*: (dict/string) the form setup as form definition including form fields and options or the subset
                  to be loaded from the types configuration settings. This slot supports all `nive.HTMLForm` options
        - *values*: (dict) additional values used for the new item. These values are independent from fields or
                    form defaults.
        - *includeAssets*: (bool) include js/css assets required by the form in the html markup. default true.

        For example the configuration for a new item form might loook like ::

            settings = {
                "form": {"fields": ("link", "share", "comment"),
                         "use_ajax": True}
                "values": {"source": "webform"}
            }

        Configuration lookup order :

        1) Customized `setItemForm` view ::

            bookmark = ViewConf(
                name="update-bookmark",
                attr="setItemForm",
                # ...
                settings={"form": {"fields": ("link", "share", "comment"),
                                   "use_ajax": True}
                          "values": {"source": "webform"}
                }
            )

        2) The types' ObjectConf.forms settings for `setItem` ::

            collection1 = ObjectConf(
                id = "bookmark",
                # ...
                forms = {
                    "newItem": {"fields": ("link", "share", "comment"),
                                "use_ajax": True},
                    "setItem": {"fields": ("link", "share", "comment"),
                                "use_ajax": True}
                },
                # ...
            )

        defines the `setItem` form in both cases with 3 form fields and to use ajax submissions ::

            {"fields": ("link", "share", "comment"), "use_ajax": True}

        If you are using the default `setItemForm` view you have to pass the type id to be
        created by the function as form parameter ``type=bookmark``. If you are using a customized
        view the type can be part of the views options slot ``settings={"type": "bookmark"}``.

        To get required assets in a seperate call use `?assets=only` as query parameter. This will
        return the required css and js assets for the specific form only.
        """
        values = redirectSuccess = None
        includeAssets = True
        # look up the new type in custom view definition
        viewconf = self.GetViewConf()
        if viewconf and viewconf.get("settings"):
            subset = viewconf.settings.get("form") or "setItem"
            values = viewconf.settings.get("values")
            redirectSuccess = viewconf.settings.get("redirectSuccess")
            includeAssets = viewconf.settings.get("includeAssets", includeAssets)
        else:
            subset = self.GetFormValue("subset") or "setItem"

        setObject = self.context
        typeconf = setObject.configuration

        # set up the form. subset might be the form configuration up to here.
        form, subset = MakeCustomizedViewForm(view=self,
                                              forContext=setObject,
                                              formSettingsOrSubset=subset,
                                              typeconf=typeconf,
                                              defaultSettings=self._formDefaults("setItem"),
                                              loadFromViewModuleConf=self.configuration)
        form.Setup(subset=subset)

        if self.GetFormValue("assets")=="only":
            self.AddHeader("X-Result", "true")
            return {"content": form.HTMLHead(ignore=[a[0] for a in self.configuration.assets])}

        # process and render the form.
        result, data, action = form.Process(values=values, redirectSuccess=redirectSuccess)
        if IObject.providedBy(result):
            result = result.id

        self.AddHeader("X-Result", str(result).lower())
        if includeAssets:
            # if assets are enabled add required js+css for form except those defined
            # in the view modules asset list
            head = form.HTMLHead(ignore=[a[0] for a in self.configuration.assets])
            return {"content": head+data}

        return {"content": data}


    def _formDefaults(self, action):
        # customize form widget. values are applied to form.widget
        values = dict(
            use_ajax = True,
            action = self.request.url
        )
        values["widget.item_template"] = "field_onecolumn"
        values["widget.action_template"] = "form_actions_onecolumn"

        # add actions
        if action == "newItem":
            values["actions"] = (Conf(id="create", method="CreateObj", name=_("Submit"), hidden=False, css_class="btn btn-primary"),)
            values["defaultAction"] = Conf(id="default", method="StartFormRequest", name="Init", hidden=True,  css_class="")
        elif action == "setItem":
            values["actions"] = (Conf(id="edit", method="UpdateObj", name=_("Submit"), hidden=False, css_class="btn btn-primary"),)
            values["defaultAction"] = Conf(id="defaultEdit", method="StartObject", name="Init", hidden=True, css_class="")

        return values


    # workflow functions ------------------------------------------------------------

    def action(self):
        """
        Trigger a workflow action based on the contexts current state.
        
        Parameters: 
        - action: action name to be triggered
        - transition (optional): transition if multiple match action 
        - test (optional): if 'true' the action is not triggered but only
          tested if the current user is allowed to run the action in
          the current context.
          
        returns the action result and new state information
        
        {"result":true/false, "messages": [], "state": {}}
        """
        action = self.GetFormValue("action") or "newItem"
        if not action:
            return {"result": False, "messages": ["Action is empty"]}
        transition = self.GetFormValue("transition")
        test = self.GetFormValue("test")=="true"
        
        result = {"result": False, "messages": None}
        if test:
            result["result"] = self.context.workflow.WfAllow(action, self.user, transition)
            if result["result"]:
                result["messages"] = ["Allowed"]
            else:
                result["messages"] = ["Not allowed"]
        else:
            try:
                result["result"] = self.context.workflow.WfAction(action, self.user, transition)
                result["messages"] = ["OK"]
                result["state"] = self.state()
            except WorkflowNotAllowed:
                result["result"] = False
                result["messages"] = ["Not allowed"]
        return result
    

    def state(self):
        """
        Get the current contexts' workflow state.
        
        returns state information
        
        - id: the state id
        - name: the state name
        - process: id and name of active workflow process
        - transistions: list of possible transitions for the current state
        
        each transition includes 

        - id: the id
        - name: the name
        - fromstate: the current state
        - tostate: new state after axcecution
        - actions: list of triggering actions for the transition
        
        """
        state = self.context.workflow.GetWfInfo(self.user)
        if not state:
            return {"result":False, "messages": ["No workflow loaded for object"]}

        def _serI(info):
            return {"id":info.id, "name":info.name} 
        
        def _serT(transition):
            return {"id":transition.id, 
                    "name":transition.name, 
                    "fromstate":transition.fromstate,
                    "tostate":transition.tostate,
                    "actions":[_serI(a) for a in transition.actions]}

        return {"id": state["state"].id,
                "name": state["state"].name,
                "process": _serI(state["process"]),
                "transitions": [_serT(t) for t in state["transitions"]],
                "result": True}


    def renderTmpl(self, template=None):
        """
        Renders the items template defined in the configuration (`ObjectConf.template`). The template
        will be called with a dictionary containing the `item`, `request` and `view`.

        See `pyramid.renderers` for possible template engines.

        Link the template in the objects type configuration ::

            collection1 = ObjectConf(
                id = "bookmark",
                template="bookmark.pt",
                # ...
            )

        You can now add a custom view and use the objects template without linking it in the view definition.

            bookmark = ViewConf(
                name="render-me",
                attr="renderTmpl",
                # ...
            )

        """
        values = {}
        values["item"] = self.context
        values["view"] = self
        values["request"] = self.request
        return self.DefaultTemplateRenderer(values, template)


    def tmpl(self):
        """
        For view based template rendering. An instance of the view class is automatically
        passed to the template as `view`. The current context can be accessed as `context`.

        See `pyramid.renderers` for possible template engines.

        Configuration example ::

            bookmark = ViewConf(
                name="render-me",
                attr="tmpl",
                renderer="myapp:templates/bookmark.pt",
                #  ...
            )

        """
        return {}


    # list rendering ------------------------------------------------------------

    def renderListItem(self, values, typename=None, template=None, **kw):
        """
        This function renders data records (non object) returned by Select or Search
        functions with the object configuration defined `listing` renderer.

        Unlike the object renderer this function does not require full object loads like
        `renderTmpl` but works with simple dictionary lists.

        Make sure all values required to render the template are passed to `renderListItems`
        i.e. included as result in the select functions.

        E.g.

        Configuration ::

            ObjectConf(id="article", listing="article-list.pt", ...)

        Template ::

            <h2>${name}</h2>
            <p>${text}</p>
            <a href="${pool_filename}">read all</a>

        Usage ::

            <div tal:content="structure view.renderListItem(values, 'article')"
                 class="col-lg-12"></div>

        :values:
        :typename:
        :template:
        """
        if template:
            values["view"] = self
            return renderers.render(template, values, request=self.request)
        typename = typename or values.get("type")
        if not typename:
            return "-no type-"
        if not hasattr(self, "_c_listing_"+typename):
            typeconf = self.context.app.configurationQuery.GetObjectConf(typename)
            tmpl = typeconf.get("listing")
            setattr(self, "_c_listing_"+typename, tmpl)
        else:
            tmpl = getattr(self, "_c_listing_"+typename)
        v2 = {}
        v2.update(values)
        v2["options"] = kw
        v2["view"] = self
        return renderers.render(tmpl, v2, request=self.request)


# internal data processing ------------------------------------------------------------

def DeserializeItems(view, items, fields, render=()):
    # Convert item objects to dicts before returning to the user
    if not isinstance(items, (list,tuple)):
        items = [items]
    if render is None:
        render = ()

    ff = fields
    values = []
    for item in items:
        data = {}
        # loop result fields
        if isinstance(fields, dict):
            ff = fields.get(item.GetTypeID())
            if ff is None:
                ff = fields.get("default__")
        elif fields is None:
            ff = item.configuration.get("toJson", ff)

        if ff is None:
            raise ConfigurationError("toJson fields are not defined")

        for field in ff:
            if view is not None and field in render:
                data[field] = view.RenderField(field, context=item)
            else:
                data[field] = item.GetFld(field)

        values.append(data)
    return values


def ExtractJSValue(values, key, default, format):
    value = values.get(key, default)
    if value in jsUndefined:
        return default
    elif format=="int":
        return int(value)
    elif format=="bool":
        if value in (1, True, "1","true","True","Yes","yes","checked"):
            return True
        return False
    elif format=="float":
        return float(value)
    return value



"""
A string renderer extension to support dictionaries for better compatibility with template renderer.
Return a single value 'content' to the renderer and the content will be returned as
the responses body. ::

    # view result
    {"content": "<h1>The response!</h1>"}
    # is returned as
    "<h1>The response!</h1>"

To activate the renderer add 'stringRendererConf' to the applications modules. ::

    configuration.modules.append("nive.components.webapi.view.stringRendererConf")

"""

def string_renderer_factory(info):
    def _render(value, system):
        if isinstance(value, dict) and "content" in value:
            value = value["content"]
        elif not isinstance(value, str):
            value = str(value)
        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = 'text/plain'
        return value
    return _render

def SetupStringRenderer(app, pyramidConfig):
    if pyramidConfig:
        # pyramidConfig is None in tests
        pyramidConfig.add_renderer('string', string_renderer_factory)

stringRendererConf = ModuleConf(
    id = "stringRenderer",
    events = (Conf(event="startRegistration", callback=SetupStringRenderer),),
)

