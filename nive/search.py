# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
This file provides global *search* functionality, database lookup and sql query 
wrappers. It is usually attached to root objects.

Search parameter handling
--------------------------
Most functions support a similar parameter handling for generating sql queries.  

===========  ===========================================================================
Parameters
===========  ===========================================================================
fields       list of database fields (field ids) to include in result.
             prefix '-': special fields or aggregate functions can be inserted by adding 
                         a '-' in front of the field. -COUNT(*) or -MAX(field1)
             prefix '+': special fields skipped in SQL query e.g. '+preview'
parameter    dictionary with fieldname:value entries used for search conditions
operators    dictionary with fieldname:operator entries used for search conditions
             default: strings=*LIKE*, all others='='
             possible values: ``=, LIKE, NOT IN, IN, >, <, <=, >=, !=, BETWEEN ``
sort         result sort field or list if multiple
ascending    sort ascending or decending
start        start position in result
max          maximum number of result records
===========  ===========================================================================

Parameter for operator BETWEEN has to be formatted: e.g. '2006/10/10' AND '2006/10/11'

================  =====================================================================
Keyword options   (Not supported by all functions)
================  =====================================================================
logicalOperator   link between conditions. default: *AND*. possible: ``AND, OR, NOT``
condition         custom sql condition statement appended to WHERE clause 
groupby           used as sql GROUP BY statement
join              adds a custom custom sql join statement
jointype          left, inner, right. default = inner (used by ``SearchType()``)
mapJoinFld        fieldname to map title by left/right join (used by ``SearchType()``)
addID             Add fld.id in query without showing in result list. used for custom 
                  columns e.g. -(select ...)
skipRender        render result flds as html element. 
                  default: ``pool_type, pool_wfa, pool_wfp`` 
                  to skip all: *True*, or a list of fields  ("pool_wfa","pool_type")
skipCount         enable or disable second query to get the number of all records.
relation          Resolve a relation and load the related entry as object. For example
                  you load the user object by settings `relation=pool_createdby`. The
                  result set will include the user object instead of the user name.
================  =====================================================================

Adding custom join statements

    "join" = "inner join pool_meta as __parent on __parent.id = meta__.pool_unitref"

    fields = ["-__parent.pool_filename as profile_filename"]


=============  ========================================================================
Search result  (supported by Search*() functions)
=============  ========================================================================
criteria       dictionary containing parameters used in search
count          number of records contained in result
total          total number of records matching the query
items          result list. each record as dictionary. Each field is rendered for 
               display depending on *skipRender* keyword. This means list entries are
               replaced by their readable names, dates are rendered readable. 
start          record start number in result 
max            maximum number of records 
next           start number of next record set
nextend        end number of next record set
prev           start number of previous record set
prevend        end number of previous record set
sql            the sql statement used
=============  ========================================================================

"""

import time

from nive.utils.utils import ConvertToNumberList
from nive.views import FieldRenderer
from nive.definitions import IFieldConf
from nive.definitions import FieldConf
from nive.definitions import ConfigurationError, ConnectionError


class Search(object):
    """ Provides search functionality  """

    def __init__(self, root):
        self.root = root

    @property
    def app(self):
        return self.root.app

    @property
    def db(self):
        return self.root.db


    # Simple search functions ----------------------------------------------------------------------------------------------
    
    def Select(self, pool_type=None, parameter=None, fields=None, operators=None, sort=None, ascending=1, start=0, max=0, **kw):
        """
        Fast and simple sql query. 
        
        If *pool_type* is not set the query will apply to the meta layer only. In this case you can
        only include pool_meta.fields in *fields*. To use a single table pass *dataTable* as keyword.
        
        If *pool_type* is set you can use meta and data *fields*. The query is restricted to a single 
        type.
        
        Supported keywords: ``groupby, logicalOperator, condition, dontAddType, dataTable, db``
        
        The following example selects all children of the current object ::
            
            fields = ["id", "title", "pool_type"]
            parameter["pool_unitref"] = self.id
            records = self.root.search.Select(parameter=parameter, fields=fields)
        
        returns records as list
        """
        parameter = parameter or {}
        operators = operators or {}
        fields = fields or ["id"]
        db = kw.get("db") or self.db
        if pool_type is None:
            dataTable=kw.get("dataTable") or "pool_meta"
            sql, values = db.FmtSQLSelect(fields, 
                                          parameter, 
                                          dataTable=dataTable, 
                                          singleTable=1, 
                                          operators=operators, 
                                          sort=sort, 
                                          ascending=ascending, 
                                          start=start, 
                                          max=max, 
                                          groupby=kw.get("groupby"), 
                                          logicalOperator=kw.get("logicalOperator"), 
                                          condition=kw.get("condition"))
        else:
            if "pool_type" not in parameter and not kw.get("dontAddType"):
                parameter["pool_type"] = pool_type
            if "pool_type" not in operators:
                operators["pool_type"] = "="
            typeInf = self.app.configurationQuery.GetObjectConf(pool_type)
            if not typeInf:
                raise ConfigurationError(pool_type + " type not found")
            sql, values = db.FmtSQLSelect(fields, 
                                          parameter, 
                                          dataTable=typeInf["dbparam"], 
                                          operators=operators, 
                                          sort=sort, 
                                          ascending=ascending, 
                                          start=start, 
                                          max=max, 
                                          groupby=kw.get("groupby"), 
                                          logicalOperator=kw.get("logicalOperator"), 
                                          condition=kw.get("condition"))
        recs = db.Query(sql, values)
        return recs


    def SelectDict(self, pool_type=None, parameter=None, fields=None, operators=None, sort=None, ascending=1, start=0, max=0, **kw):
        """
        Fast and simple sql query. 
        
        If *pool_type* is not set the query will apply to the meta layer only. In this case you can
        only include pool_meta.fields in *fields*. 
        
        If *pool_type* is set you can use meta and data *fields*. The query is restricted to a single 
        type.
        
        Supported keywords: ``groupby, logicalOperator, condition``
        
        Records are returned as dictionaries
        
        The following example selects all children *not* of type *image* of the current object ::
            
            fields = ["id", "title", "pool_type"]
            parameter = {"pool_unitref": self.id}
            operators = {"pool_type": "!="}
            records = self.root.search.SelectDict("image",
                                               parameter=parameter, 
                                               fields=fields, 
                                               operators=operators)
        
        returns records as dict list
        """
        fields = fields or ["id"]
        recs = self.Select(pool_type=pool_type,
                           parameter=parameter, 
                           fields=fields, 
                           operators=operators, 
                           sort=sort, 
                           ascending=ascending, 
                           start=start, 
                           max=max, 
                           **kw)
        if len(recs)==0:
            return recs
        # convert
        if len(fields) > len(recs[0]):
            raise TypeError("Too many fields")
        for i in range(len(fields)):
            name = fields[i]
            if name.find(" as ")!=-1:
                name = name.split(" as ")[1]
                fields[i] = name
        return [dict(list(zip(fields, r))) for r in recs]


    # Extended search functions ----------------------------------------------------------------------------------------------
    
    def Search(self, parameter, fields=None, operators=None, **kw):
        """
        Extended meta layer search function. Supports all keyword options and search result. 
        
        Example ::
        
            root.()Search({"title":"test"}, 
                          fields=["id", "pool_type", "title"], 
                          start=0, max=50, 
                          operators={"title":"="})
        
        returns search result (See above)
        """
        t = time.time()
        fields = fields or []
        operators = operators or {}
        start, max, kw = self._SearchKWs(kw)
        # lookup field definitions
        fields, fldList, groupcol = self._PrepareFields(fields)
        removeID = self._HandleGroupByQueries(fields, fldList, groupcol, kw)

        db = self.db
        if not db:
            raise ConnectionError("No database connection")
        
        sql, values = db.FmtSQLSelect(fldList, 
                                      parameter=parameter, 
                                      operators=operators, 
                                      start=start,
                                      max=max,
                                      **kw)
        records = db.Query(sql, values)

        # convert records
        fldList = self._RenameFieldAlias(fldList)
        converter = self._PrepareRenderer(kw, fldList)
        items, cnt = self._ConvertRecords(records, converter, fields, fldList, kw)

        # total records
        total = len(items) + start
        if (total==max or start>0) and kw.get("skipCount") != 1:
            if "sort" in kw:
                del kw["sort"]
            if not kw.get("groupby"):
                sql2, values = db.FmtSQLSelect(["-count(*)"], 
                                               parameter=parameter, 
                                               operators=operators, 
                                               start=None, 
                                               max=None,
                                               **kw)
                val = db.Query(sql2, values)
                total = val[0][0] if val else 0
            else:
                sql2, values = db.FmtSQLSelect(["-count(DISTINCT %s)" % (kw.get("groupby"))], 
                                               parameter=parameter, 
                                               operators=operators, 
                                               start=None, 
                                               max=None, 
                                               **kw)
                val = db.Query(sql2, values)
                total = len(val) if val else 0

        items = self._HandleRelations(kw.get("relations"), items, kw)
        result = self._PrepareResult(items, parameter, cnt, total, start, max, t, sql)
        return result


    def SearchType(self, pool_type, parameter=None, fields=None, operators=None, **kw):
        """
        Extended meta and data layer search function. Supports all keyword options and search result. 
        
        Example ::
        
            root.()SearchType("image", 
                              parameter={"title":"test"}, 
                              fields=["id", "pool_type", "title"], 
                              start=0, max=50, 
                              operators={"title":"="})
        
        returns search result (See above)
        """
        t = time.time()
        fields = fields or []
        operators = operators or {}
        start, max, kw = self._SearchKWs(kw)
        # lookup field definitions
        fields, fldList, groupcol = self._PrepareFields(fields, pool_type)
        removeID = self._HandleGroupByQueries(fields, fldList, groupcol, kw)
        self._HandleTypeJoins(pool_type, parameter, operators, kw)

        typeInf = self.app.configurationQuery.GetObjectConf(pool_type)
        if not typeInf:
            raise ConfigurationError("Type not found (%s)" % (pool_type))

        db = self.db
        if db is None:
            raise ConnectionError("No database connection")

        sql, values = db.FmtSQLSelect(fldList, 
                                      parameter=parameter,  
                                      operators=operators,
                                      start=start, 
                                      max=max, 
                                      dataTable=typeInf["dbparam"],
                                      **kw)
        records = db.Query(sql, values)
            
        # prepare field renderer and names
        fldList = self._RenameFieldAlias(fldList)
        converter = self._PrepareRenderer(kw, fldList)
        items, cnt = self._ConvertRecords(records, converter, fields, fldList, kw)

        # total records
        total = len(items) + start
        if (total==max or start>0) and kw.get("skipCount") != 1:
            if "sort" in kw:
                del kw["sort"]
            if not kw.get("groupby"):
                cntflds = ["-count(*) as cnt"]
            else:
                cntflds = ["-count(DISTINCT %s) as cnt" % (kw.get("groupby"))]
            sql2, values = db.FmtSQLSelect(cntflds, 
                                           parameter=parameter,  
                                           operators=operators,
                                           dataTable=typeInf["dbparam"],
                                           **kw)
            val = db.Query(sql2, values)
            if not kw.get("groupby"):
                total = val[0][0] if val else 0
            else:
                total = len(val) if val else 0

        items = self._HandleRelations(kw.get("relations"), items, kw)
        result = self._PrepareResult(items, parameter, cnt, total, start, max, t, sql)
        return result


    def SearchData(self, pool_type, parameter, fields=None, operators=None, **kw):
        """
        Extended data layer search function. Supports all keyword options and search result. 
        
        Example ::
        
            root.()SearchData("image", 
                              parameter={"text": "new"}, 
                              fields=["id", "text", "title"], 
                              start=0, max=50, 
                              operators={"text":"LIKE"})
        
        returns search result (See above)
        """
        t = time.time()
        fields = fields or []
        operators = operators or {}
        start, max, kw = self._SearchKWs(kw)
        # lookup field definitions
        fields, fldList, groupcol = self._PrepareFields(fields, pool_type)
        removeID = self._HandleGroupByQueries(fields, fldList, groupcol, kw)

        typeInf = self.app.configurationQuery.GetObjectConf(pool_type)
        if not typeInf:
            raise ConfigurationError("Type not found (%s)" % (pool_type))

        db = self.db
        if not db:
            raise ConnectionError("No database connection")

        sql, values = db.FmtSQLSelect(fldList, 
                                      parameter=parameter,  
                                      operators=operators,
                                      start=start, 
                                      max=max, 
                                      dataTable=typeInf["dbparam"],
                                      singleTable=1,
                                      **kw)
        records = db.Query(sql, values)
            
        # prepare field renderer and names
        fldList = self._RenameFieldAlias(fldList)
        converter = self._PrepareRenderer(kw, fldList)
        items, cnt = self._ConvertRecords(records, converter, fields, fldList, kw)

        # total records
        total = len(items) + start
        if (total==max or start>0) and kw.get("skipCount") != 1:
            if "sort" in kw:
                del kw["sort"]
            if not kw.get("groupby"):
                cntflds = ["-count(*) as cnt"]
            else:
                cntflds = ["-count(DISTINCT %s) as cnt" % (kw.get("groupby"))]
            sql2, values = db.FmtSQLSelect(cntflds, 
                                           parameter=parameter,  
                                           operators=operators,
                                           start=start, 
                                           max=max, 
                                           dataTable=typeInf["dbparam"],
                                           singleTable=1,
                                           **kw)
            val = db.Query(sql2, values)
            if not kw.get("groupby"):
                total = val[0][0] if val else 0
            else:
                total = len(val) if val else 0
                
        items = self._HandleRelations(kw.get("relations"), items, kw)
        result = self._PrepareResult(items, parameter, cnt, total, start, max, t, sql)
        return result


    def SearchFulltext(self, phrase, parameter=None, fields=None, operators=None, **kw):
        """
        Fulltext search function. Searches all text fields marked for fulltext search. Uses *searchPhrase* 
        as parameter for text search. Supports all keyword options and search result. 
        
        Example ::
        
            root.SearchFulltext("new", parameter={},
                              fields=["id", "title"], 
                              start=0, max=50, 
                              operators={"text":"LIKE"})
        
        returns search result (See above)
        """
        t = time.time()

        fields = fields or ("id","title","pool_type","-pool_fulltext.text as fulltext")
        operators = operators or {}
        parameter = parameter or {}
        if phrase==None:
            phrase = ""
        searchFor = phrase
        start, max, kw = self._SearchKWs(kw)
        # lookup field definitions
        fields, fldList, groupcol = self._PrepareFields(fields)
        removeID = self._HandleGroupByQueries(fields, fldList, groupcol, kw)

        if phrase.find("*") == -1:
            phrase = "%%%s%%" % phrase
        else:
            phrase = phrase.replace("*", "%")

        db = self.db
        if not db:
            raise ConnectionError("No database connection")

        sql, values = db.GetFulltextSQL(phrase, 
                                        fldList, 
                                        parameter=parameter,  
                                        operators=operators, 
                                        start=start, 
                                        max=max,
                                        **kw)
        records = db.Query(sql, values)
            
        # prepare field renderer and names
        fldList = self._RenameFieldAlias(fldList)
        converter = self._PrepareRenderer(kw, fldList)
        items, cnt = self._ConvertRecords(records, converter, fields, fldList, kw)
        
        # total records
        total = len(items) + start
        if (total==max or start>0) and kw.get("skipCount") != 1:
            if "sort" in kw:
                del kw["sort"]
            if not kw.get("groupby"):
                cntflds = ["-count(*) as cnt"]
            else:
                cntflds = ["-count(DISTINCT %s) as cnt" % (kw.get("groupby"))]
            sql2, values = db.FmtSQLSelect(cntflds, 
                                           parameter=parameter,  
                                           operators=operators,
                                           start=start, 
                                           max=max, 
                                           skipRang=1, 
                                           **kw)
            val = db.Query(sql2, values)
            if not kw.get("groupby"):
                total = val[0][0] if val else 0
            else:
                total = len(val) if val else 0

        items = self._HandleRelations(kw.get("relations"), items, kw)
        result = self._PrepareResult(items, parameter, cnt, total, start, max, t, sql)
        result["phrase"] = searchFor
        return result


    def SearchFulltextType(self, pool_type, phrase, parameter=None, fields=None, operators=None, **kw):
        """
        Fulltext search function. Searches all text fields marked for fulltext search of the given type. Uses *searchPhrase* 
        as parameter for text search. Supports all keyword options and search result. 
        
        Example ::
        
            root.()SearchFulltextType("text",
                              parameter={"searchPhrase": "new"}, 
                              fields=["id", "text", "title"], 
                              start=0, max=50, 
                              operators={"text":"LIKE"})
        
        returns search result (See above)
        """
        t = time.time()

        fields = fields or ("id","title","-pool_fulltext.text as fulltext")
        operators = operators or {}
        parameter = parameter or {}
        if phrase is None:
            phrase = ""
        searchFor = phrase
        start, max, kw = self._SearchKWs(kw)
        # lookup field definitions
        fields, fldList, groupcol = self._PrepareFields(fields, pool_type)
        removeID = self._HandleGroupByQueries(fields, fldList, groupcol, kw)
        self._HandleTypeJoins(pool_type, parameter, operators, kw)

        # fulltext wildcard
        if phrase.find("*") == -1:
            phrase = "%%%s%%" % phrase
        else:
            phrase = phrase.replace("*", "%")

        typeInf = self.app.configurationQuery.GetObjectConf(pool_type)
        if not typeInf:
            raise ConfigurationError("Type not found (%s)" % (pool_type))

        db = self.db
        if not db:
            raise ConnectionError("No database connection")

        sql, values = db.GetFulltextSQL(phrase, 
                                        fldList, 
                                        parameter=parameter, 
                                        operators=operators,
                                        start=start, 
                                        max=max,
                                        dataTable=typeInf["dbparam"],
                                        **kw)
        records = db.Query(sql, values)
            
        # prepare field renderer and names
        fldList = self._RenameFieldAlias(fldList)
        converter = self._PrepareRenderer(kw, fldList)
        items, cnt = self._ConvertRecords(records, converter, fields, fldList, kw)

        # total records
        total = len(items) + start
        if (total==max or start>0) and kw.get("skipCount") != 1:
            if "sort" in kw:
                del kw["sort"]
            if not kw.get("groupby"):
                cntflds = ["-count(*) as cnt"]
            else:
                cntflds = ["-count(DISTINCT %s) as cnt" % (kw.get("groupby"))]
            sql2, values = db.FmtSQLSelect(cntflds, 
                                           parameter=parameter,  
                                           operators=operators,
                                           start=start, 
                                           max=max, 
                                           dataTable=typeInf["dbparam"],
                                           skipRang=1, 
                                           **kw)
            val = db.Query(sql2, values)
            if not kw.get("groupby"):
                total = val[0][0] if val else 0
            else:
                total = len(val) if val else 0

        items = self._HandleRelations(kw.get("relations"), items, kw)
        result = self._PrepareResult(items, parameter, cnt, total, start, max, t, sql)
        result["phrase"] = searchFor
        return result


    def SearchFilename(self, filename, parameter, fields=None, operators=None, **kw):
        """
        Filename search function. Searches all physical file filenames (not url path names). Supports all 
        keyword options and search result. 
        
        Includes matchinng files as "result_files" in each record.
        
        Example ::
        
            root.()SearchFulltextType("text",
                              parameter={"searchPhrase": "new"}, 
                              fields=["id", "text", "title"], 
                              start=0, max=50, 
                              operators={"text":"LIKE"})
        
        returns search result (See above)
        """
        fields = fields or ()
        operators = operators or {}

        db = self.db
        if not db:
            raise ConnectionError("No database connection")
        files = db.SearchFilename(filename)

        ids = []
        filesMapped = {}
        for f in files:
            if not f["id"] in ids:
                ids.append(f["id"])
            if str(f["id"]) not in filesMapped:
                filesMapped[str(f["id"])] = []
            filesMapped[str(f["id"])].append(f)
        if len(ids)==0:
            ids.append(0)
        
        parameter["id"] = ids
        operators["id"] = "IN"
        result = self.Search(parameter=parameter, fields=fields, operators=operators, **kw)

        # merge result and files
        for rec in result["items"]:
            if str(rec["id"]) not in filesMapped:
                continue
            rec["result_files"] = filesMapped[rec["id"]]
            # copy first file in list
            file = filesMapped[str(rec["id"])][0]
            rec["+size"] = file["size"]
            rec["+extension"] = file["extension"]
            rec["+filename"] = file["filename"]
            rec["+fileid"] = file["fileid"]
            rec["+key"] = file["filekey"]

        # update result
        del result["criteria"]["id"]
        result["criteria"]["filename"] = filename
        return result


    def _SearchKWs(self, kws):
        default = {"ascending":1, "start":0, "max":100}
        # parse incoming kws
        
        try:       start = int(kws["start"])
        except:    start = default["start"]
        if "start" in kws:
            del kws["start"]

        try:       max = int(kws["max"])
        except:    max = default["max"]
        if "max" in kws:
            del kws["max"]

        try:       kws["ascending"] = int(kws["ascending"])
        except:    kws["ascending"] = default["ascending"]
        
        """
        groupby=kw.get("groupby"), 
        logicalOperator=kw.get("logicalOperator"), 
        condition=kw.get("condition"), 
        join=kw.get("join"))
        """
        return start, max, kws
         
    def _PrepareFields(self, fields, pool_type=None):
        # lookup field definitions
        fields = self._GetFieldDefinitions(fields, pool_type)
        fldList = []
        groupcol = 0
        for f in fields:
            if f["id"][0] == "-":
                groupcol += 1
            fldList.append(f["id"])
        return fields, fldList, groupcol
    
    def _GetFieldDefinitions(self, fields, pool_type = None):
        f = []
        for fld in fields:
            if IFieldConf.providedBy(fld):
                f.append(fld)
                continue
            if not isinstance(fld, str):
                continue
            if fld in ("__preview__",):
                continue
            # skip custom flds
            if fld[0] == "+":
                continue
            # Aggregate functions, custom flds
            if fld[0] == "-":
                f.append(FieldConf(**{"id": fld, "name": fld, "datatype": "string"}))
                continue

            fl = self.app.configurationQuery.GetFld(fld, pool_type)
            if fl:
                f.append(fl)
        return f

    def _HandleGroupByQueries(self, fields, fldList, groupcol, kws):
        # add id. required for group by  queries
        removeID = False
        if (not "id" in fldList and groupcol == 0 and kws.get("groupby") == None) or kws.get("addID")==1:
            fldList.append("id")
            fields.append(self.app.configurationQuery.GetFld("id"))
            removeID = True
        return removeID
    
    def _HandleTypeJoins(self, pool_type, parameter, operators, kws):
        # set join type
        default_join = 0
        if "jointype" not in kws or kws.get("jointype")=="inner":
            default_join = 1
            if not kws.get("skiptype"):
                parameter["pool_type"] = pool_type
        #operators
        if not operators:
            operators = {}
        if "pool_type" not in operators:
            operators["pool_type"] = "="
        if not default_join:
            operators["jointype"] = kws.get("jointype")
        return default_join

    
    def _PrepareRenderer(self, kws, fldList):
        # prepare field renderer
        skipRender = kws.get("skipRender", False)
        if skipRender == True:
            skipRender = fldList
        elif not skipRender:
            skipRender = ("pool_type", "pool_wfa", "pool_wfp")
        converter = FieldRenderer(self, skip=skipRender)
        return converter
    
    def _RenameFieldAlias(self, fldList):
        # parse alias field names used in sql query
        p = 0
        for f in fldList:
            if f[0] == "-" and f.find(" as ") != -1:
                a = f.split(" as ")[-1]
                a = a.replace(" ", "")
                a = a.replace(")", "")
                fldList[p] = a
            p += 1
        return fldList

    def _ConvertRecords(self, records, converter, fields, fldList, kws):
        # convert result
        db = self.db
        items = []
        for rec in records:
            rec2 = []
            for p in range(len(fields)):
                value = db.structure._de(rec[p], fields[p]["datatype"], fields[p])
                rec2.append(converter.Render(fields[p], value, False, **kws))
            items.append(dict(list(zip(fldList, rec2))))
        return items, len(items)
    
    def _HandleRelations(self, relations, items, kws):
        if not relations:
            return items
        if isinstance(relations, str):
            relations = (relations,)
        cache = {}
        for r in relations:
            # special cases: user lookup pool_createdby, pool_changedby
            if r in ("pool_createdby", "pool_changedby"):
                GetUser = self.app.portal.userdb.root.GetUser
                for i in items:
                    ref = "user:"+i[r]
                    if ref in cache:
                        user = cache[ref]
                    else:
                        user = GetUser(i[r])
                        cache[ref] = user
                    i[r] = user
            # todo load obj by id
        return items

    def _PrepareResult(self, items, parameter, cnt, total, start, max, t, sql):
        # prepare result dictionary and paging information
        result = {}
        result["items"] = items
        result["criteria"] = parameter
        result["count"] = cnt
        result["total"] = total
        result["start"] = start
        result["max"] = max
        result["time"] = time.time() - t
        result["sql"] = sql
        
        next = start + max
        if next >= total:
            next = 0
        result["next"] = next
        nextend = next + max
        if nextend > total:
            nextend = total
        result["nextend"] = nextend

        prev = start - max
        if prev < 1:
            prev = 0
        result["prev"] = prev
        prevend = prev + max
        result["prevend"] = prevend
        return result


    # Tree structure -----------------------------------------------------------

    def GetTree(self, flds=None, sort="id", base=0, parameter=""):
        """
        Select list of all folders from db.
        
        returns the subtree
        {'items': [{'id': 354956L, 'ref1': 354954L, 'ref2': 354952L, ..., 'ref10': None, 'items': [...]}]
        """
        if not flds:
            # lookup meta list default fields
            flds = self.app.configuration.listDefault
        db = self.db
        return db.GetTree(flds=flds, sort=sort, base=base, parameter=parameter)


    def TreeParentIDs(self, id):
        """
        returns the parent ids for the object with id as list
        """
        db = self.db
        return db.GetParentPath(id)


    def TreeParentTitles(self, id):
        """
        returns the parent titles for the object with id as list
        """
        db = self.db
        return db.GetParentTitles(id)


    # Codelists representation for entries -----------------------------------------------------------------------------------------

    def GetEntriesAsCodeList(self, pool_type, name_field, parameter=None, operators=None, sort=None):
        """
        Search the database for entries of type *pool_type* and return matches as codelist ::
        
            [{"name": name_field, "id": object.id}, ... ]
        
        If the name_field is stored as data field, insert *data.* at the beginning of name_field 
        (e.g. ``data.header``)
        
        returns list
        """
        operators = operators or {}
        parameter = parameter or {}
        if not sort:
            sort = name_field
        if "pool_type" not in parameter:
            parameter["pool_type"] = pool_type
        recs = self.SelectDict(pool_type=pool_type, parameter=parameter, 
                               fields=["id", "pool_unitref", name_field+" as name"], 
                               operators=operators, sort=sort)
        return recs


    def GetEntriesAsCodeList2(self, name_field, parameter=None, operators=None, sort=None):
        """
        Search the database and return matches as codelist ::
        
            [{"name": name_field, "id": object.id}, ... ]
        
        returns list
        """
        operators = operators or {}
        parameter = parameter or {}
        if not sort:
            sort = name_field
        recs = self.SelectDict(parameter=parameter, fields=["id", "pool_unitref", name_field+" as name"], 
                               operators=operators, sort=sort)
        return recs


    def GetGroupAsCodeList(self, pool_type, name_field, parameter=None, operators=None, sort=None):
        """
        Search the database for entries of type *pool_type* and return matches grouped by unique
        *name_field* values as codelist ::
        
            [{"name": name_field, "id": object.id}, ... ]
        
        If the name_field is stored as data field, insert *data.* at the beginning of name_field 
        (e.g. ``data.header``)
        
        returns list
        """
        operators = operators or {}
        parameter = parameter or {}
        if not sort:
            sort = name_field
        if "pool_type" not in parameter:
            parameter["pool_type"] = pool_type
        recs = self.SelectDict(pool_type=pool_type, 
                               parameter=parameter, 
                               fields=["id", "pool_unitref", name_field+" as name"], 
                               operators=operators, 
                               #groupby=name_field, 
                               sort=sort)
        return recs


    def GetGroupAsCodeList2(self, name_field, parameter=None, operators=None, sort=None):
        """
        Search the database and return matches grouped by unique *name_field* values as codelist ::
        
            [{"name": name_field, "id": object.id}, ... ]
        
        returns list
        """
        operators = operators or {}
        parameter = parameter or {}
        if not sort:
            sort = name_field
        recs = self.SelectDict(parameter=parameter, 
                               fields=["id", "pool_unitref", name_field+" as name"], 
                               operators=operators, 
                               #groupby=name_field, 
                               sort=sort)
        return recs


    # Name / ID lookup -----------------------------------------------------------

    def FilenameToID(self, filename, unitref=None, parameter=None, firstResultOnly=True, operators=None):
        """
        Convert url path filename (meta.pool_filename) to id. This function does not lookup
        physical files and their filenames.

        returns id
        """
        operators = operators or {}
        parameter = parameter or {}
        if unitref is not None:
            parameter["pool_unitref"] = unitref
        parameter["pool_filename"] = filename
        operators["pool_filename"] = "="
        # lookup meta list default fields
        flds = self.app.configuration.listDefault
        recs = self.Select(parameter=parameter, fields=flds, operators=operators)
        #print recs
        if firstResultOnly:
            if len(recs) == 0:
                return 0
            return recs[0][0]
        return recs


    def IDToFilename(self, id):
        """
        Convert id to url path filename (meta.pool_filename). This function does not lookup
        physical files and their filenames.
        
        returns string
        """
        parameter={"id": id}
        recs = self.Select(parameter=parameter, fields=["pool_filename"])
        if len(recs) == 0:
            return ""
        return recs[0][0]


    def ConvertDatarefToID(self, pool_type, dataref):
        """
        Search for object id based on dataref and pool_type.

        returns id
        """
        parameter={"pool_type": pool_type, "pool_dataref": dataref}
        recs = self.Select(parameter=parameter, fields=["id"])
        if len(recs) == 0:
            return 0
        return recs[0][0]


    def GetMaxID(self):
        """
        Lookup id of the last created object.

        returns id
        """
        recs = self.Select(fields=["-max(id)"])
        if len(recs) == 0:
            return 0
        return recs[0][0]


    # References --------------------------------------------------------------------

    def GetReferences(self, unitID, types=None, sort="id"):
        """
        Search for references in unit or unitlist fields of all objects.
        
        returns id list
        """
        if not types:
            types = self.app.configurationQuery.GetAllObjectConfs()
        else:
            l = []
            for t in types:
                l.append(self.app.configurationQuery.GetObjectConf(t))
            types = l
        references = []
        ids = [unitID]

        db = self.db

        # lookup meta list default fields
        flds = self.app.configuration.listDefault
        flds = list(flds)
        # search unit flds
        for t in types:
            for f in t["data"]:
                if f["datatype"] != "unit":
                    continue
                l = self.Select(pool_type=t["id"], parameter={f["id"]:unitID}, fields=flds, sort=sort)
                for r in l:
                    if not r[0] in ids:
                        ids.append(r[0])
                        references.append(r)

        # search unitlist flds
        for t in types:
            for f in t["data"]:
                if f["datatype"] != "unitlist":
                    continue
                l = self.Select(pool_type=t["id"], parameter={f["id"]:str(unitID)}, fields=flds+[f["id"]], sort=sort, 
                                operators={f["id"]:"LIKE"})
                for r in l:
                    if not r[2] == t["id"]:
                        continue
                    unitRefs = ConvertToNumberList(r[3])
                    if not unitID in unitRefs:
                        continue
                    if not r[0] in ids:
                        ids.append(r[0])
                        references.append(r)

        return references


