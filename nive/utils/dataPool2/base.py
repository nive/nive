# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = "Data Pool 2 SQL Base Module"

import weakref
import logging

from datetime import datetime, date

from nive.utils.utils import ConvertToDateTime
from nive.utils.utils import ConvertListToStr
from nive.utils.utils import STACKF
from nive.utils.path import DvPath

from nive.definitions import ConfigurationError, OperationalError, ProgrammingError, ConnectionError, Warning

from nive.utils.dataPool2.structure import PoolStructure, DataWrapper, MetaWrapper, FileWrapper



class Base(object):
    """
    Data Pool 2 SQL Base implementation

    Manage typed data units consisting of meta layer, data layer and files.
    Meta layer is the same for all units, data layer is based on types and files
    are stored by key.
    Meta and data is mapped to database, files are stored in filesystem.

    Pool structure is required and must contain the used database fields as list
    (table names and column names).

    Entries are referenced by pool_meta.id as unique ID.

    All basic SQL is handled internally.

    Configuration Parameter
    -----------------------
    root:          string. filesystem root path
    codePage:      string. the codepage used on output
    dbCodePage:    string. database codepage
    structure:     PoolStructure object defining the database structure and field types.
    version:       string. the default version
    useBackups:    bool.     store backup versions of files on replace
    useTrashcan:   bool.     moves files to trashcan rather than delete physically
    debug:         number. turn debugging on. 0 = off, 1=on (no traceback), 2...20=on (traceback lines) 
    log:           string. log file path for debugging

    Standard Meta
    -------------
    A list consisting of meta layer fields which are used in preloading

    "meta_flds": (
    ("pool_dataref", "integer not null default 0"),
    ("pool_datatbl", "ENUM() not null"),
    )
    """
    # map db system exceptions to one type
    _OperationalError=OperationalError
    _ProgrammingError=ProgrammingError
    _Warning=Warning
    _DefaultConnection = None
    _EmptyValues = None

    MetaTable = "pool_meta"
    FulltextTable = "pool_fulltext"
    GroupsTable = "pool_groups"
    

    def __init__(self, connection = None, structure = None, root = "",
                 useTrashcan = False, useBackups = False, 
                 codePage = "utf-8", dbCodePage = "utf-8",
                 connParam = None,
                 debug = 0, log = "sql.log",
                 timezone = None, **kw):

        self.codePage = codePage
        self.dbCodePage = dbCodePage
        self.useBackups = useBackups
        self.useTrashcan = useTrashcan
        self.pytimezone = timezone

        self._debug = debug
        self._log = log
        self.name = root        # used for logging
        
        self._conn = None
        if not structure:
            self.structure = self._GetDefaultPoolStructure()(pool=self)
        else:
            self.structure = structure
        
        # create directories, if not available
        self.InitFileStorage(root, connParam)
        if connection:
            self._conn = connection
            self.name = self._conn.configuration.dbName
        elif connParam:
            self._conn = self.CreateConnection(connParam)
            self.name = connParam.get("dbName","")
        

    def Close(self):
        if self._conn is not None:
            self._conn.close()

    def __del__(self):
         self.Close()


    # Database api ---------------------------------------------------------------------

    @property
    def connection(self):
        """
        Returns the database connection and attempts a reconnect or verifies the connection
        depending on configuration settings.
        """
        self._conn.VerifyConnection()
        return self._conn

    @property
    def usedconnection(self):
        """
        Returns the previously used connection without verifying the connection. The returned
        connection may be none or not connected. Can be used in cases if the connection will
        only be used to finish previous actions e.g. Commit(). Lookup is faster and will not 
        waste unnecessary resources.
        """
        return self._conn

    @property
    def dbapi(self):
        if not self._conn:
            raise ConnectionError("No Connection")
        return self._conn.dbapi


    def Begin(self):
        """
        Start a database transaction, if supported
        """
        self.connection.begin()

    def Undo(self):
        """
        Rollback the changes made to the database, if supported
        """
        if self.usedconnection:
            self.usedconnection.rollback()

    def Commit(self, user=""):
        """
        Commit the changes made to the database, if supported
        """
        self.usedconnection.commit()

    def GetDBDate(self, date=None):
        if not date:
            date = datetime.now(tz=self.pytimezone)
        elif not isinstance(date, datetime):
            date = ConvertToDateTime(date)
        return date.strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def placeholder(self):
        """
        SQL statement format string to be used as placeholder for values. 
        e.g. mysql=%s, sqlite=?
        """
        return self._conn.placeholder
    

    # SQL queries ---------------------------------------------------------------------

    def FmtSQLSelect(self, flds, parameter=None, dataTable="", start=0, max=0, **kw):
        """
        Create a select statement based on pool_structure and given parameters.
        
        Aggregate functions can be included in flds but must be marked with
        the prefix `-` e.g. `-count(*)`
        
        Tables in the generated statement get an alias prefix:
        meta__ for meta table
        data__ for data table
        
        flds: select fields
        parameter: where clause parameter
        dataTable: add join statement for the table
        start: start number of record to be returned
        max: maximum nubers of records in result

        **kw:
        singleTable: 1/0 skip join. only use datatable for select
        version: version key. select content from specific version
        operators: operators used for fields in where clause: =,LIKE,<,>,...
        jointype: type of join. default = INNER
        logicalOperator = link between conditions. default = and. and, or, not
        condition = custom condition statement. default = empty
        join = custom join statement. default = empty
        groupby: add GROUP BY statement
        sort: result sort order. sort prefix ! to skip auto table lookup
        ascending: result sort order ascending or descending
        """
        operators = kw.get("operators",{})
        jointype = operators.get("jointype", "INNER")
        singleTable = kw.get("singleTable",0)
        version = kw.get("version")
        metaStructure = self.structure.get(self.MetaTable, version=version)
        mapJoinFld = kw.get("mapJoinFld")
        plist = []   # sorted list of query parameters for execute()
        ph = self.placeholder   # placeholder to be used instead plist values
        fields = []
        for field in flds:
            if singleTable:
                table = ""
                if field[0] == "-":
                    field = field[1:]
            else:
                table = "meta__."
                # aggregate functions marked with - e.g. "-count(*)"
                if field[0] == "-":
                    table = ""
                    field = field[1:]
                asName = field.find(" as ")!=-1
                f2=field
                if asName:
                    f2 = field.split(" as ")[0]
                elif f2 in metaStructure:   # ?? or f2 == "pool_stag":
                    table = "meta__."
                elif table != "":
                    if jointype.lower() != "inner":
                        if field == mapJoinFld:
                            fields.append("IF(meta__.pool_datatbl='%s', %s, meta__.title)" % (dataTable, field))
                        else:
                            fields.append("IF(meta__.pool_datatbl='%s', %s, '')" % (dataTable, field))
                        continue
                    table = "data__."
            #if len(fields) > 0:
            #    fields.append(", ")
            fields.append(table + field)
        fields = ",".join(fields)

        aCombi = kw.get("logicalOperator")
        if not aCombi:
            aCombi = "AND"
        else:
            aCombi = aCombi.upper()
            if not aCombi in ("AND","OR","NOT"):
                aCombi = "AND"
        addCombi = False
        
        where = []
        if parameter is None:
            parameter={}
        for key in list(parameter.keys()):
            value = parameter[key]
            paramname = key

            operator = "="
            if operators and key in operators:
                operator = operators[key]

            if singleTable:
                table = ""
            else:
                table = "meta__."
                # aggregate functions marked with - e.g. "-count(*)"
                if key[0] == "-":
                    table = ""
                    paramname = key[1:]
                elif key in metaStructure:
                    table = "meta__."
                elif dataTable != "":
                    table = "data__."
            
            # fmt string values
            if isinstance(value, str):
                if operator == "LIKE":
                    if value == "":
                        continue
                    value = "%%%s%%" % value.replace("*", "%")
                    if addCombi:
                        where.append(" %s " % aCombi)
                    where.append("%s%s %s %s " % (table, paramname, operator, ph))
                    plist.append(value)
                elif operator == "BETWEEN":
                    if value == "":
                        continue
                    if addCombi:
                        where.append(" %s " % aCombi)
                    where.append("%s%s %s %s " % (table, paramname, operator, ph))
                    plist.append(value)
                elif operator == "IN":
                    operator = "="
                    if addCombi:
                        where.append(" %s " % aCombi)
                    where.append("%s%s %s %s " % (table, paramname, operator, ph))
                    plist.append(value)
                else:
                    if addCombi:
                        where.append(" %s " % aCombi)
                    where.append("%s%s %s %s " % (table, paramname, operator, ph))
                    plist.append(value)
                addCombi = True

            # fmt list values
            elif isinstance(value, (tuple, list)):
                if not value:
                    continue
                if addCombi:
                    where.append(" %s " % aCombi)
                if operator == "BETWEEN":
                    if len(value) < 2:
                        continue
                    where.append("%s%s %s %s AND %s" % (table, paramname, operator, ph, ph))
                    plist.append(value[0])
                    plist.append(value[1])
                elif operator.startswith("LIKE:"):
                    if value == "":
                        continue
                    if operator.endswith("OR"):
                        logicalOp = "OR"
                    elif operator.endswith("NOT"):
                        logicalOp = "NOT"
                    else:
                        logicalOp = "AND"
                    where.append(" (")
                    statement = False
                    for v in value:
                        # handle multiple like values
                        if statement:
                            where.append(" %s " % logicalOp)
                        statement=True
                        # exception empty value
                        if not v:
                            where.append("%s%s %s %s " % (table, paramname, "=", ph))
                        else:
                            v = "%%%s%%" % v.replace("*", "%")
                            where.append("%s%s %s %s " % (table, paramname, "LIKE", ph))
                        plist.append(v)
                    where.append(") ")
                elif len(value)==1:
                    if operator == "IN":
                        operator = "="
                    elif operator == "NOT IN":
                        operator = "<>"
                    where.append("%s%s %s %s " % (table, paramname, operator, ph))
                    plist.append(value[0])
                else:
                    v = self._FmtListForQuery(value)
                    if isinstance(v, str):
                        # sqlite error: cannot use placeholder with lists
                        where.append("%s%s %s (%s) " % (table, paramname, operator, v))
                    else:
                        where.append("%s%s %s %s " % (table, paramname, operator, ph))
                        plist.append(value)
                addCombi = True

            # fmt number values
            elif isinstance(value, (int, float)):
                if addCombi:
                    where.append(" %s " % aCombi)
                if operator == "LIKE":
                    operator = "="
                where.append("%s%s %s %s" % (table, paramname, operator, ph))
                plist.append(value)
                addCombi = True

            # fmt datetime values
            elif isinstance(value, datetime):
                if addCombi:
                    where.append(" %s " % aCombi)
                if operator == "LIKE":
                    operator = "="
                where.append("%s%s %s %s" % (table, paramname, operator, ph))
                plist.append(value)
                addCombi = True

            # fmt datetime values
            elif isinstance(value, date):
                if addCombi:
                    where.append(" %s " % aCombi)
                if operator == "LIKE":
                    operator = "="
                where.append("DATE(%s%s) %s %s" % (table, paramname, operator, ph))
                plist.append(value)
                addCombi = True

        condition = kw.get("condition")
        if condition != None and condition != "":
            if len(where):
                where.append(" %s %s" %(aCombi, condition))
            else:
                where = [condition]
        where = self._FmtWhereClause(where, singleTable)

        order = "ASC"
        if kw.get("ascending", 1) == 0:
            order = "DESC"

        # map sort fields
        sort = kw.get("sort", "")
        if sort is None:
            sort = ""
        if sort and sort[0] == "!":
            sort = sort[1:]
        elif sort and not singleTable:
            table = "meta__."
            s = sort.split(",")
            sort = []
            for sortfld in s:
                sortfld = sortfld.strip(" ")
                sortfldvalue = sortfld.split(" ")[0]
                if len(sortfld) > 0 and sortfld[0] == "-":
                    table = ""
                    sortfld = sortfld[1:]
                elif sortfldvalue in metaStructure or sortfldvalue == "pool_stag":
                    table = "meta__."
                elif dataTable != "":
                    table = "data__."
                if len(sort):
                    sort.append(", ")
                sort.append(table)
                sort.append(sortfld)
            sort = "".join(sort)

        customJoin = kw.get("join", "")
        if customJoin is None:
            customJoin = ""

        join = ""
        joindata = ""
        if not singleTable:
            # joins
            if dataTable != "":
                joindata = "%s JOIN %s AS data__ ON (meta__.pool_dataref = data__.id) " % (jointype, dataTable)

        limit = ""
        if max:
            limit = self._FmtLimit(start, max)

        groupby = ""
        if kw.get("groupby"):
            groupby = "GROUP BY %s" % kw.get("groupby")

        table = self.MetaTable + " AS meta__"
        if singleTable:
            table = dataTable

        if sort != "":
            sort = "ORDER BY %s %s" % (sort, order)

        sql = """
        SELECT %s
        FROM %s
        %s
        %s
        %s
        %s
        %s
        %s
        %s
        """ % (fields, table, join, joindata, customJoin, where, groupby, sort, limit)
        return sql, plist


    def _FmtListForQuery(self, values):
        return values

    def _FmtWhereClause(self, where, singleTable):
        if len(where):
            where = "WHERE %s" % "".join(where)
        else:
            where = ""
        return where

    def _FmtLimit(self, start, max):
        if start != None:
            return "LIMIT %s, %s" % (str(start), str(max))
        return "LIMIT %s" % (str(max))


    def GetFulltextSQL(self, searchPhrase, flds, parameter, dataTable = "", **kw):
        """
        generate sql statement for fulltext query

        searchPhrase: text to be searched

        For further options see -> FmtSQLSelect
        """
        sql, values = self.FmtSQLSelect(flds, parameter, dataTable=dataTable, **kw)
        searchPhrase = self.DecodeText(searchPhrase)
        values.insert(0, searchPhrase)
        ph = self.placeholder
        phrase = """%s.text LIKE %s""" % (self.FulltextTable, ph)

        if not searchPhrase in ("", "'%%'", None):
            if sql.find("WHERE ") == -1:
                if sql.find("ORDER BY ") != -1:
                    sql = sql.replace("ORDER BY ", "WHERE %s \r\n        ORDER BY " % (phrase))
                elif sql.find("LIMIT ") != -1:
                    sql = sql.replace("LIMIT ", "WHERE %s \r\n        LIMIT " % (phrase))
                else:
                    sql += "WHERE %s " % (phrase)
            else:
                sql = sql.replace("WHERE ", "WHERE %s AND " % (phrase))

        sql = sql.replace("FROM %s AS meta__"%(self.MetaTable), "FROM %s AS meta__\r\n        LEFT JOIN %s ON (meta__.id = %s.id)"%(self.MetaTable, self.FulltextTable, self.FulltextTable))
        return sql, values
    
    
    # database query execution -----------------------------------------------------------------------

    def Execute(self, sql, values = None, cursor = None):
        """
        Execute a query on the database. Returns the dbapi cursor. Use `cursor.fetchall()` or
        `cursor.fetchone()` to retrieve results. The cursor should be closed after usage.
        """
        if cursor is None:
            cursor = self.connection.cursor()
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        # adjust different accepted empty values sets
        if not values:
            values = self._EmptyValues
        try:
            cursor.execute(sql, values)
        except self._OperationalError as e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError(e)
        except self._ProgrammingError as e:
            # map to nive.utils.dataPool2.base.OperationalError
            self.Undo()
            raise ProgrammingError(e)
        return cursor

    
    def Query(self, sql, values = None, getResult = True):
        """
        execute a query on the database. non unicode texts are converted according to codepage settings.
        """
        c = self.connection.cursor()
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        sql = self.DecodeText(sql)
        if values:
            # check for list and strings
            found = [isinstance(v, list) or isinstance(v, bytes) for v in values]
            if True in found:
                # shouldnt happen
                v1 = []
                for v in values:
                    if isinstance(v, list):
                        v1.append(tuple(v))
                    elif isinstance(v, bytes):
                        v1.append(self.DecodeText(v))
                    else:
                        v1.append(v)
                values = v1
        # adjust different accepted empty values sets
        if not values:
            values = self._EmptyValues
        try:
            c.execute(sql, values)
        except self._OperationalError as e:
            # map to nive.utils.dataPool2.base.OperationalError
            self.Undo()
            logging.getLogger(self.name).error(str(e) + "  " + sql)
            raise OperationalError(e)
        except self._ProgrammingError as e:
            # map to nive.utils.dataPool2.base.OperationalError
            self.Undo()
            logging.getLogger(self.name).error(str(e) + "  " + sql)
            raise ProgrammingError(e)
        if not getResult:
            c.close()
            return
        result = c.fetchall()
        c.close()
        return result


    def SelectFields(self, table, fields, idValues, idColumn = None):
        """
        Select row with multiple fields in the table.
        Set `idColumn` to the column name of the unique id column
        
        table: table name
        fields: list of field names to be returned
        idValues: list of matching id values to be returned
        idColumn: default 'id'. id column name

        returns matching records 
        """
        dataList = []
        phdata = []
        ph = self.placeholder
        key = idColumn or "id"
        for value in idValues:
            phdata.append(ph)
            dataList.append(value)

        sql = "SELECT %s FROM %s WHERE %s IN (%s)" % (",".join(fields), table, key, ",".join(phdata))

        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)

        cursor = self.connection.cursor()
        result = ()
        try:
            cursor.execute(sql, dataList)
            result = cursor.fetchall()
        except self._Warning:
            pass
        except self._OperationalError as e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError(e)
        #finally:
        #    cursor.close()
        return result

    
    def InsertFields(self, table, data, idColumn = None):
        """
        Insert row with multiple fields in the table.
        Codepage and dates are converted automatically
        Set `idColumn` to the column name of the auto increment unique id column
        to get it returned.
        
        returns the converted data 
        """
        dataList = []
        flds = []
        phdata = []
        ph = self.placeholder
        data = self.structure.serialize(table, None, data)
        for key, value in list(data.items()):
            flds.append(key)
            phdata.append(ph)
            dataList.append(value)

        sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, ",".join(flds), ",".join(phdata))

        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)

        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, dataList)
        except self._Warning:
            pass
        except self._OperationalError as e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError(e)
        except:
            self.Undo()
            raise
        #finally:
        #    cursor.close()

        id = 0
        if idColumn:
            id = self._GetInsertIDValue(cursor)
        cursor.close()
        return data, id


    def UpdateFields(self, table, id, data, idColumn = "id", autoinsert=False):
        """
        Updates multiple fields in the table.
        If `autoinsert` is True the a new record is automatically inserted if it does not exist. Also
        the function returns the converted data *and* id (non zero if a new record was inserted)
        
        If `autoinsert` is False the function returns the converted data.
        """
        ph = self.placeholder
        if autoinsert:
            # if record does not exist, insert it
            sql = """select id from %s where %s=%s""" %(table, idColumn, ph)
            cursor = self.Execute(sql, (id,))
            r = cursor.fetchone()
            cursor.close()
            if not r:
                data, id = self.InsertFields(table, data, idColumn = idColumn)
                return data, id
            
        dataList = []
        data = self.structure.serialize(table, None, data)
        sql = ["UPDATE %s SET " % (table)]
        for key, value in list(data.items()):
            dataList.append(value)
            if len(sql)>1:
                sql.append(",%s=%s"%(key, ph))
            else:
                sql.append("%s=%s"%(key, ph))

        sql.append(" WHERE %s=%s" % (idColumn, ph))
        dataList.append(id)
        sql = "".join(sql)
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)

        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, dataList)
        except self._Warning:
            pass
        except self._OperationalError as e:
            # map to nive.utils.dataPool2.base.OperationalError
            raise OperationalError(e)
        except:
            self.Undo()
            raise
        finally:
            cursor.close()

        if autoinsert:
            return data, 0
        return data


    def DeleteRecords(self, table, parameter):
        """
        Delete records referenced by parameters
        """
        if not parameter:
            return False
        p = []
        v = []
        ph = self.placeholder
        for field, value in list(parameter.items()):
            p.append("%s=%s"%(field, ph))
            v.append(value)
        sql = "DELETE FROM %s WHERE %s" % (table, " AND ".join(p))
        if self._debug:
            STACKF(0,sql+"\r\n\r\n",self._debug, self._log,name=self.name)
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, v)
        except:
            self.Undo()
            raise
        finally:
            cursor.close()


    # Text conversion -----------------------------------------------------------------------

    def EncodeText(self, text):
        """
        Used for text read from the database. 
        Converts the text to unicode based on self.dbCodePage.
        """
        if text is None:
            return text
        if isinstance(text, bytes):
            return str(text, self.dbCodePage, "replace")
        return text


    def DecodeText(self, text):
        """
        Used for text stored in database.
        Convert the text to unicode based on self.codePage.
        """
        if text is None:
            return text
        if isinstance(text, bytes):
            return str(text, self.codePage, "replace")
        return text


    def ConvertRecToDict(self, rec, flds):
        """
        Convert a database record tuple to dictionary based on flds list
        """
        return dict(list(zip(flds, rec)))


    # Entries -------------------------------------------------------------------------------------------

    def CreateEntry(self, pool_datatbl, id = 0, user = "", **kw):
        """
        Create new entry.
        Requires pool_datatbl as parameter
        """
        if id:
            id, dataref = self._CreateFixID(id, dataTbl=pool_datatbl)
        else:
            id, dataref = self._CreateNewID(table=self.MetaTable, dataTbl=pool_datatbl)
        if not id:
            return None
        kw["preload"] = "skip"
        kw["pool_dataref"] = dataref
        entry = self._GetPoolEntry(id, **kw)
        entry._InitNew(pool_datatbl, user)
        return entry


    def GetEntry(self, id, **kw):
        """
        Get entry from db by ID
        """
        return self._GetPoolEntry(id, **kw)


    def DeleteEntry(self, id, version=None):
        """
        Delete the entry and files
        """
        cursor = self.connection.cursor()

        # base record
        sql, values = self.FmtSQLSelect(["pool_dataref", "pool_datatbl"], parameter={"id":id}, dataTable=self.MetaTable, singleTable=1)
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        try:
            cursor.execute(sql, values)
        except:
            self.Undo()
            raise
        r = cursor.fetchone()
        if not r:
            return 0
        dataref = r[0]
        datatbl = r[1]
        cursor.close()

        self.DeleteFiles(id, version=version)
        tables = (self.MetaTable, self.FulltextTable, self.GroupsTable)
        for table in tables:
            self.DeleteRecords(table, parameter={"id":id})
        self.DeleteRecords(datatbl, parameter={"id":dataref})

        return 1


    def IsIDUsed(self, id):
        """
        Query database if id exists
        """
        sql, values = self.FmtSQLSelect(["id"], parameter={"id":id}, dataTable = self.MetaTable, singleTable=1)
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        c = self.connection.cursor()
        c.execute(sql, values)
        n = c.fetchone()
        c.close()
        return n is not None


    def GetBatch(self, ids, **kw):
        """
        Get all entries as objects at once. returns a list.
        supports preload: all, skip, meta
        
        kw: 
        - meta: list of meta pool_datatbl for faster lookup
        """
        preload = kw.get("preload", "all")
        entries = []
        version = kw.get("version")
        sort = kw.get("sort")
        if len(ids) == 0:
            return entries

        if preload == "skip":
            for id in ids:
                e = self._GetPoolEntry(id, preload="skip", version=version)
                entries.append(e)
            return entries

        if preload == "meta":
            flds = self.structure.get(self.MetaTable, version=version)
            if not flds:
                raise ConfigurationError("Meta layer is empty.")
            parameter = {"id": ids}
            operators = {"id": "IN"}
            sql, values = self.FmtSQLSelect(flds, parameter=parameter, dataTable=self.MetaTable, max=len(ids), sort=sort, operators=operators, singleTable=1)
            recs = self.Query(sql, values)
            for r in recs:
                meta = self.ConvertRecToDict(r, flds)
                e = self._GetPoolEntry(meta["id"], pool_dataref=meta["pool_dataref"], pool_datatbl=meta["pool_datatbl"], preload="skip")
                e._UpdateCache(meta = meta, data = None)
                entries.append(e)
            return entries

        if "meta" in kw and kw["meta"] and "pool_datatbl" in kw["meta"][0]:
            # use meta pool_datatbl passed in kw[meta]
            tables = []
            for r in kw["meta"]:
                if not r["pool_datatbl"] in tables:
                    tables.append(r["pool_datatbl"])
        else:
            # select data tables for ids
            flds = ["pool_datatbl"]
            parameter = {"id": ids}
            operators = {"id": "IN"}
            # select list of datatbls
            sql, values = self.FmtSQLSelect(flds, parameter=parameter, dataTable=self.MetaTable, sort=sort, groupby="pool_datatbl", operators=operators, singleTable=1)
            tables = []
            for r in self.Query(sql, values):
                if not r["pool_datatbl"] in tables:
                    tables.append(r[0])
        t = ""
        fldsm = self.structure.get(self.MetaTable, version=version)
        if not fldsm:
            raise ConfigurationError("Meta layer is empty.")
        unsorted = []
        for table in tables:
            structure = self.structure.get(table, version=version)
            if not structure:
                continue
            fldsd = list(structure)
            flds = list(fldsm) + fldsd
            parameter = {"id": ids, "pool_datatbl": table}
            operators = {"id": "IN", "pool_datatbl": "="}
            # select type data
            sql, values = self.FmtSQLSelect(flds, parameter=parameter, dataTable=table, sort=sort, operators=operators)
            typeData = self.Query(sql, values)
            for r2 in typeData:
                meta = self.ConvertRecToDict(r2[:len(fldsm)], fldsm)
                data = self.ConvertRecToDict(r2[len(fldsm):], fldsd)
                e = self._GetPoolEntry(meta["id"], pool_dataref=meta["pool_dataref"], pool_datatbl=meta["pool_datatbl"], preload="skip")
                meta = self.structure.deserialize(self.MetaTable, None, meta)
                data = self.structure.deserialize(table, None, data)
                e._UpdateCache(meta = meta, data = data)
                unsorted.append(e)
        # sort entries
        for id in ids:
            for o in unsorted:
                if o.id==id:
                    entries.append(o)
                    break
        return entries

    def _GetInsertIDValue(self, cursor):
        #("assert", "subclass")
        return 0

    def _CreateNewID(self, table="", dataTbl=None):
        #("assert", "subclass")
        return 0

    def _CreateFixID(self, id, dataTbl):
        #("assert", "subclass")
        return 0

    def _GetPoolEntry(self, id, **kw):
        #("assert", "subclass")
        return 0


    # Tree structure --------------------------------------------------------------

    def GetContainedIDs(self, base=0, sort="title", parameter=""):
        """
        Search subtree and returns a list of all contained ids.
        id needs to be first field, pool_unitref second
        """
        refs = """
        pool_unitref as ref1,
        (select pool_unitref from %(meta)s where id = ref1) as ref2,
        (select pool_unitref from %(meta)s where id = ref2) as ref3,
        (select pool_unitref from %(meta)s where id = ref3) as ref4,
        (select pool_unitref from %(meta)s where id = ref4) as ref5,
        (select pool_unitref from %(meta)s where id = ref5) as ref6,
        (select pool_unitref from %(meta)s where id = ref6) as ref7,
        (select pool_unitref from %(meta)s where id = ref7) as ref8,
        (select pool_unitref from %(meta)s where id = ref8) as ref9,
        (select pool_unitref from %(meta)s where id = ref9) as ref10,
        """ % {"meta": self.MetaTable}

        if parameter:
            parameter = "where " + parameter
        sql = """
        select %s id
        from %s %s
        order by pool_unitref, %s
        """ % (refs, self.MetaTable, parameter, sort)
        aC = self.connection.cursor()
        aC.execute(sql)
        l = aC.fetchall()
        aC.close()
        if len(l) == 0:
            return []

        ids = []
        for rec in l:
            #ignore outside tree
            if not base in rec or rec[10] == base:
                continue
            #data
            ids.append(rec[10])

        return ids


    def GetTree(self, flds=None, sort="title", base=0, parameter=""):
        """
        Loads a subtree as dictionary. 
        The returned dictionary has the following format:
        {"id": 123, "items": [{"id": 124, "items": [], "data": "q", ....}, ...], "data": "q", ....}
        
        id needs to be first field, pool_unitref second
        """
        if flds is None:
            flds = ["id"]
        refs = """
        pool_unitref as ref1,
        (select pool_unitref from %(meta)s where id = ref1) as ref2,
        (select pool_unitref from %(meta)s where id = ref2) as ref3,
        (select pool_unitref from %(meta)s where id = ref3) as ref4,
        (select pool_unitref from %(meta)s where id = ref4) as ref5,
        (select pool_unitref from %(meta)s where id = ref5) as ref6,
        (select pool_unitref from %(meta)s where id = ref6) as ref7,
        (select pool_unitref from %(meta)s where id = ref7) as ref8,
        (select pool_unitref from %(meta)s where id = ref8) as ref9,
        (select pool_unitref from %(meta)s where id = ref9) as ref10,
        """ % {"meta":self.MetaTable}

        if parameter:
            parameter = "where " + parameter
        sql = """
        select 
        %s 
        %s
        from %s %s
        order by pool_unitref, %s
        """ % (refs, ConvertListToStr(flds), self.MetaTable, parameter, sort)
        aC = self.connection.cursor()
        aC.execute(sql)
        l = aC.fetchall()
        tree = {"items":[]}
        aC.close()
        if len(l) == 0:
            return tree

        flds2 = ["ref1", "ref2", "ref3", "ref4", "ref5", "ref6", "ref7", "ref8", "ref9", "ref10"] + flds
        rtree = ["ref10", "ref9", "ref8", "ref7", "ref6", "ref5", "ref4", "ref3", "ref2", "ref1"]
        for rec in l:
            #ignore outside tree
            if not base in rec:  # or rec[10] == base:
                continue
            #data
            data = self.ConvertRecToDict(rec, flds2)
            #parent and path, lookup base in parents 
            add = 0
            current = tree
            for ref in rtree:
                if data[ref] is None:
                    continue
                if data[ref] == base:
                    add = 1
                if not add:
                    continue
                # add item to tree list
                if "items" not in current:
                    current["items"] = []
                refentry = self._InList(current["items"], data[ref])
                if not refentry:
                    refentry = {"id":data[ref], "items": []}
                    current["items"].append(refentry)
                current = refentry
            # add data 
            if "items" not in current:
                current["items"] = []
            entry = self._InList(current["items"], data["id"])
            if not entry:
                entry = data
                current["items"].append(entry)
            else:
                entry.update(data)

        return tree

    def _InList(self, l, id):
        for i in l:
            if i["id"] == id:
                return i
        return None
    
    
    def GetParentPath(self, id):
        """
        Returns id references of parents for the given id.
        Maximum 10 parents
        """
        if id <= 0:
            return []
        sql = """
        SELECT t1.pool_unitref AS ref1, 
         t2.pool_unitref as ref2, 
         t3.pool_unitref as ref3, 
         t4.pool_unitref as ref4,
         t5.pool_unitref as ref5,
         t6.pool_unitref as ref6,
         t7.pool_unitref as ref7,
         t8.pool_unitref as ref8,
         t9.pool_unitref as ref9,
         t10.pool_unitref as ref10
        FROM %(meta)s AS t1
        LEFT JOIN %(meta)s AS t2 ON t2.id = t1.pool_unitref
        LEFT JOIN %(meta)s AS t3 ON t3.id = t2.pool_unitref
        LEFT JOIN %(meta)s AS t4 ON t4.id = t3.pool_unitref
        LEFT JOIN %(meta)s AS t5 ON t5.id = t4.pool_unitref
        LEFT JOIN %(meta)s AS t6 ON t6.id = t5.pool_unitref
        LEFT JOIN %(meta)s AS t7 ON t7.id = t6.pool_unitref
        LEFT JOIN %(meta)s AS t8 ON t8.id = t7.pool_unitref
        LEFT JOIN %(meta)s AS t9 ON t9.id = t8.pool_unitref
        LEFT JOIN %(meta)s AS t10 ON t10.id = t9.pool_unitref
        WHERE t1.id = %(id)d;""" % {"id":id, "meta": self.MetaTable}
        
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        aC = self.connection.cursor()
        aC.execute(sql)
        aL = aC.fetchall()
        parents = []
        if len(aL) == 0:
            return parents
        cnt = 10
        for i in range(0, cnt-1):
            id = aL[0][i]
            if id == None:
                continue
            if id <= 0:
                break
            parents.insert(0, id)
        aC.close()
        return parents


    def GetParentTitles(self, id):
        """
        Returns titles of parents for the given id.
        maximum 10 parents
        """
        if id <= 0:
            return []
        aC = self.connection.cursor()
        sql = """
        SELECT t1.pool_unitref AS ref1, t1.title AS title1, 
         t2.pool_unitref as ref2, t2.title AS title2,
         t3.pool_unitref as ref3, t3.title AS title3,
         t4.pool_unitref as ref4, t4.title AS title4,
         t5.pool_unitref as ref5, t5.title AS title5,
         t6.pool_unitref as ref6, t6.title AS title6,
         t7.pool_unitref as ref7, t7.title AS title7,
         t8.pool_unitref as ref8, t8.title AS title8,
         t9.pool_unitref as ref9, t9.title AS title9,
         t10.pool_unitref as ref10, t10.title AS title10 
        FROM %(meta)s AS t1
        LEFT JOIN %(meta)s AS t2 ON t2.id = t1.pool_unitref
        LEFT JOIN %(meta)s AS t3 ON t3.id = t2.pool_unitref
        LEFT JOIN %(meta)s AS t4 ON t4.id = t3.pool_unitref
        LEFT JOIN %(meta)s AS t5 ON t5.id = t4.pool_unitref
        LEFT JOIN %(meta)s AS t6 ON t6.id = t5.pool_unitref
        LEFT JOIN %(meta)s AS t7 ON t7.id = t6.pool_unitref
        LEFT JOIN %(meta)s AS t8 ON t8.id = t7.pool_unitref
        LEFT JOIN %(meta)s AS t9 ON t9.id = t8.pool_unitref
        LEFT JOIN %(meta)s AS t10 ON t10.id = t9.pool_unitref
        WHERE t1.id = %(id)d;""" % {"id": id, "meta": self.MetaTable}        
        
        if self._debug:
            STACKF(0,sql+"\r\n",self._debug, self._log,name=self.name)
        aC.execute(sql)
        aL = aC.fetchall()
        parents = []
        if len(aL) == 0:
            return parents
        cnt = 10
        for i in range(1, cnt-1):
            title = aL[0][i*2+1]
            if title is None:
                break
            parents.insert(0, self.EncodeText(title))
        aC.close()
        return parents


    # Files and directories ---------------------------------------------------------------------

    def InitFileStorage(self, root, connectionParam):
        """
        Set the local root path for files
        """
        self.root = DvPath()
        self.root.SetStr(root)

    def GetRoot(self):
        return str(self.root)

    def DeleteFiles(self, id, version):
        # subclassed
        pass


    # groups - userid assignment storage ------------------------------------------------------------------------------------

    def GetGroups(self, id, userid=None, group=None):
        """
        Get local group assignment for userid.

        `id` can be a single value or a tuple. If its a tuple the groups for
        all matching ids are returned.

        returns a group assignment list [["userid", "groupid", "id"], ...]
        """
        # check if exists
        parameter = {}
        
        if id is not None:
            parameter["id"] = id
        else:
            raise TypeError("id must not be none")
        if userid:
            parameter["userid"] = userid
        if group:
            parameter["groupid"] = group
        operators = {}
        if isinstance(id, (list, tuple)):
            operators["id"] = "IN"
        sql, values = self.FmtSQLSelect(["userid", "groupid", "id"],
                                        parameter=parameter,
                                        operators=operators,
                                        dataTable=self.GroupsTable,
                                        singleTable=1)
        r = self.Query(sql, values)
        return r


    def AddGroup(self, id, userid, group):
        """
        Add a local group assignment for userid.
        """
        data = {"userid": userid, "groupid": group}
        if id is not None:
            data["id"] = id
        else:
            raise TypeError("id must not be none")
        self.InsertFields(self.GroupsTable, data)


    def RemoveGroups(self, id, userid=None, group=None):
        """
        Remove a local group assignment for userid or all for the id/ref.
        """
        p = {}
        if id is not None:
            p["id"] = id
        else:
            raise TypeError("id must not be none")
        if userid:
            p["userid"] = userid
        if group:
            p["groupid"] = group
        self.DeleteRecords(self.GroupsTable, p)


    def GetAllUserGroups(self, userid):
        """
        Get all local group assignment for userid.
        
        returns a group assignment list [["userid", "groupid", "id"], ...]
        """
        # check if exists
        p = {"userid": userid}
        o = {"userid": "="}
        sql, values = self.FmtSQLSelect(["userid", "groupid", "id"], parameter=p, operators=o, dataTable=self.GroupsTable, singleTable=1)
        r = self.Query(sql, values)
        return r


    # Pool status ---------------------------------------------------------------------

    def GetCountEntries(self, table = None):
        """
        Returns the total number of entries in the pool
        """
        if not table:
            table = self.MetaTable
        aC = self.connection.cursor()
        aC.execute("SELECT COUNT(*) FROM %s" % (table))
        aN = aC.fetchone()[0]
        aC.close()
        return aN


    def SetConnection(self, conn):
        self._conn = conn

    def CreateConnection(self, connParam):
        return self._DefaultConnection(connParam)

    
    # internal subclassing -------------------------------------------
    
    def _GetDefaultPoolStructure(self):
        return PoolStructure

    def _GetDataWrapper(self):
        return DataWrapper

    def _GetMetaWrapper(self):
        return MetaWrapper

    def _GetFileWrapper(self):
        return FileWrapper
    
    # to be removed --------------------------------------------------
    
    def GetConnection(self):
        return self._conn




class Entry(object):
    """
    Entry object of data pool
    """

    def __init__(self, dataPool, id, **kw):
        """[a]
        version: version of this entry
        dataTbl: data table name of this entry type
        preload: meta/data flds to preload on init. "all" (default), "skip", "stdmetadata", "stdmeta", "meta"
        kw virtual = 1 to disable preload() and exists() 
        """
        # key values
        self.id = id
        self.version = kw.get("version", None)
        self.dataTbl = kw.get("pool_datatbl", None)
        self.dataRef = kw.get("pool_dataref", 0)

        # basic properties
        self.pool = dataPool
        selfref = weakref.ref(self)
        self.meta = dataPool._GetMetaWrapper()(selfref)
        self.data = dataPool._GetDataWrapper()(selfref)
        self.files = dataPool._GetFileWrapper()(selfref)
        self.cacheRec = True
        self._localRoles = None
        self._permissions = None
        self.virtual = kw.get("virtual")==1
        
        #self._debug = 0#dataPool._debug

        if self.virtual:
            return
        preload = kw.get("preload", "all")
        if self.id and self.cacheRec and preload != "skip":
            self.Load(preload)
            if self.data.IsEmpty() and self.meta.IsEmpty() and self.files.IsEmpty():
                if not self.Exists():
                    raise NotFound("%s not found" % str(id))
        #else:
        #    if not self.Exists():
        #        raise NotFound, "%s not found" % str(id)


    def __del__(self):
        self.Close()


    def Close(self):
        self.meta.close()
        self.data.close()
        self.files.close()
        self.pool = None

    def Exists(self):
        """
        Check if the entry physically exists in the database
        """
        if self.virtual:
            return True
        if not self.IsValid():
            return False
        return self.pool.IsIDUsed(self.id)

    def IsValid(self):
        """
        Check if the id is valid
        """
        return self.id > 0


    def SerializeValue(self, fieldname, value, meta=False):
        if meta:
            tbl = self.pool.MetaTable
        else:
            tbl = self.GetDataTbl()
        return self.pool.structure.serialize(tbl, fieldname, value)

    def DeserializeValue(self, fieldname, value, meta=False):
        if meta:
            tbl = self.pool.MetaTable
        else:
            tbl = self.GetDataTbl()
        return self.pool.structure.deserialize(tbl, fieldname, value)

    # Transactions ------------------------------------------------------------------------

    def Commit(self, user="", dbCommit=True):
        """
        Commit temporary changes (meta, data, files) to database
        """
        self.Touch(user)
        try:
            # meta
            if self.meta.HasTemp():
                self.pool.UpdateFields(self.pool.MetaTable, self.id, self.meta.GetTemp())
            # data
            if self.data.HasTemp():
                self.pool.UpdateFields(self.GetDataTbl(), self.GetDataRef(), self.data.GetTemp())
            # files
            if self.files.HasTemp():
                self.CommitFiles(self.files.GetTemp())
            if dbCommit:
                self.pool.Commit()
            # remove previous files
            self.Cleanup(self.files.GetTemp())
            self.data.SetContent(self.data.GetTemp())
            self.data.clear()
            self.meta.SetContent(self.meta.GetTemp())
            self.meta.clear()
            self.files.SetContent(self.files.GetTemp())
            self.files.clear()
        except Exception as e:
            try:
                self.Undo()
            except:
                pass
            raise 
        return True


    def Undo(self):
        """
        Undo changes in database
        """
        self.meta.EmptyTemp()
        self.data.EmptyTemp()
        self.files.EmptyTemp()
        self.pool.Undo()


    # Reading Values ------------------------------------------------------------------------

    def GetMetaField(self, fld, fromDB=False):
        """
        Read a single field from meta layer
        if fromDB data is loaded from db, not cache
        """
        if fld == "id":
            return self.id
        elif fld == "pool_size":
            return self.GetDataSize()

        if not fromDB and self.cacheRec and fld in self.meta:
            return self.meta[fld]

        sql, values = self.pool.FmtSQLSelect([fld], parameter={"id":self.id}, dataTable=self.pool.MetaTable, singleTable=1)
        data = self._GetFld(sql, values)
        data = self.pool.structure.deserialize(self.pool.MetaTable, fld, data)
        self._UpdateCache({fld: data})
        return data


    def GetDataField(self, fld, fromDB=False):
        """
        Read a single field from data layer
        if fromDB data is loaded from db, not cache
        """
        if not fromDB and self.cacheRec and fld in self.data:
            return self.data[fld]

        tbl = self.GetDataTbl()
        sql, values = self.pool.FmtSQLSelect([fld], parameter={"id":self.GetDataRef()}, dataTable=tbl, singleTable=1)
        data = self._GetFld(sql, values)
        data = self.pool.structure.deserialize(tbl, fld, data)
        self._UpdateCache(None, {fld: data})
        return data


    def GetMeta(self):
        """
        Read meta layer and return as dictionary
        """
        if self.cacheRec and not self.meta.IsEmpty():
            return self.meta.copy()

        data =  self._SQLSelect(self.pool.structure.get(self.pool.MetaTable, version=self.version))
        data = self.pool.structure.deserialize(self.pool.MetaTable, None, data)
        self._UpdateCache(data)
        data["id"] = self.id
        return data


    def GetData(self):
        """
        Read data layer and return as dictionary
        """
        if self.cacheRec and not self.data.IsEmpty():
            return self.data

        tbl = self.GetDataTbl()
        try:
            flds = self.pool.structure.get(tbl, version=self.version)
        except:
            return None

        data = self._SQLSelect(flds, table=tbl)
        data = self.pool.structure.deserialize(tbl, None, data)
        self._UpdateCache(None, data)
        return data


    # Writing Values ------------------------------------------------------------------------

    def SetMetaField(self, fld, data, cache=True):
        """
        Update single field to meta layer.
        Commits changes immediately to database without calling touch.
        """
        temp = self.pool.UpdateFields(self.pool.MetaTable, self.id, {fld:data})
        self.pool.Commit()
        if cache:
            self._UpdateCache(temp)
        return True


    def SetDataField(self, fld, data, cache=True):
        """
        Update single field to data layer
        Commits changes immediately to database without calling touch.
        """
        if fld == "id":
            return False

        # check if data record already exists
        id = self.GetDataRef()
        if id <= 0:
            return False

        temp = self.pool.UpdateFields(self.GetDataTbl(), id, {fld:data})
        self.pool.Commit()

        if cache:
            self._UpdateCache(None, temp)
        return True


    def Touch(self, user=""):
        """
        Tets change date and changed by to now
        """
        temp = {}
        temp["pool_change"] = self.pool.GetDBDate()
        if user is None:
            user=""
        else:
            user=str(user)
        temp["pool_changedby"] = user
        self.meta.update(temp)
        return True


    # Files -------------------------------------------------------------------------------------------

    def DuplicateFiles(self, newEntry):
        """
        """
        #BREAK("subclass")
        pass


    def CommitFile(self, key, file):
        """
        """
        #BREAK("subclass")
        pass


    # Actions ---------------------------------------------------------------------------

    def Duplicate(self, duplicateFiles = True):
        """
        Create a copy of the entry with a new id.
        """
        if self.cacheRec:
            self.Load("all")

        newEntry = self.pool.CreateEntry(pool_datatbl=self.GetDataTbl())
        if not newEntry:
            return None
        id = newEntry.GetID()

        # copy data
        newEntry.meta.update(self.GetMeta())
        newEntry.data.update(self.GetData())

        # check if entry contains file and file exists
        if duplicateFiles:
            if not self.DuplicateFiles(newEntry):
                self.pool.DeleteEntry(id)
                del newEntry
                return None

        return newEntry


    # Preloading -------------------------------------------------------------------------------------------

    def Load(self, option = "all", reload = False):
        """
        Loads different sets of fields in single sql statement

        options:
        skip
        all: all meta and data fields
        stdmeta: fields configured in stdMeta list
        stdmetadata: fields configured in stdMeta list and all data fields
        meta: all meta fields
        """
        if self.virtual:
            return True
        if option == "skip":
            return True

        # check data already in memory
        if not reload:
            if option == "all" and not self.data.IsEmpty() and not self.meta.IsEmpty():
                return True

            elif option == "stdmetadata" and not self.data.IsEmpty() and not self.meta.IsEmpty():
                return True

            elif option == "stdmeta" and not self.meta.IsEmpty():
                return True

            elif option == "meta" and not self.meta.IsEmpty():
                return True

        # shortcut sql load functions based on pool structure
        if option == "all":
            return self._PreloadAll()
        elif option == "stdmetadata":
            return self._PreloadStdMetaData()
        elif option == "stdmeta":
            return self._PreloadStdMeta()
        elif option == "meta":
            return self._PreloadMeta()

        return True


    # System Values ------------------------------------------------------------------------

    def GetID(self):
        return self.id

    def GetDataTbl(self):
        if self.dataTbl:
            return self.dataTbl
        self.dataTbl = self.GetMetaField("pool_datatbl")
        return self.dataTbl

    def GetDataRef(self):
        if self.dataRef:
            return self.dataRef
        self.dataRef = self.GetMetaField("pool_dataref")
        return self.dataRef

    def GetSize(self):
        return 0

    def GetVersion(self):
        return self.version


    # Caching --------------------------------------------------------------------

    def Clear(self):
        """
        empty cache
        """
        self.meta.clear()
        self.data.clear()
        self.files.clear()


    # Fulltext ---------------------------------------------------------------------------------------

    def WriteFulltext(self, text):
        """
        Update or create fulltext for entry
        """
        if text is None:
            text=""
        sql, values = self.pool.FmtSQLSelect(["id"], parameter={"id":self.id}, dataTable=self.pool.FulltextTable, singleTable=1)
        cursor = self.pool.connection.cursor()
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n", self.pool._debug, self.pool._log, name=self.pool.name)
        try:
            cursor.execute(sql, values)
        except:
            self.pool.Undo()
            raise
        r = cursor.fetchone()
        text = self.pool.DecodeText(text)
        if not r:
            self.pool.InsertFields(self.pool.FulltextTable, {"text": text, "id": self.id})
        else:
            self.pool.UpdateFields(self.pool.FulltextTable, self.id, {"text": text})
        cursor.close()


    def GetFulltext(self):
        """
        read fulltext from entry
        """
        sql, values = self.pool.FmtSQLSelect(["text"], parameter={"id":self.id}, dataTable=self.pool.FulltextTable, singleTable=1)
        cursor = self.pool.connection.cursor()
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n", self.pool._debug, self.pool._log, name=self.pool.name)
        try:
            cursor.execute(sql, values)
        except:
            self.pool.Undo()
            raise
        r = cursor.fetchone()
        cursor.close()
        if not r:
            return ""
        return self.pool.DecodeText(r[0])


    def DeleteFulltext(self):
        """
        Delete fulltext for entry
        """
        ph = self.pool.placeholder
        sql = "DELETE FROM %s WHERE id = %s"%(self.pool.FulltextTable, ph)
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
        aCursor = self.pool.connection.cursor()
        aCursor.execute(sql, (self.id,))
        aCursor.close()


    # Locking ---------------------------------------------------------------------

    def Lock(self, owner):
        return False

    def UnLock(self, owner, forceUnlock = False):
        return False

    def IsLocked(self, owner):
        return False


    # SQL functions -------------------------------------------------------------------------------------------

    def _GetFld(self, sql, values):
        """
        select single field from sql
        """
        try:
            cursor = self.pool.connection.cursor()
            if self.pool._debug:
                STACKF(0,sql+"\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
            cursor.execute(sql, values)
            r = cursor.fetchone()
            cursor.close()
            return r[0]
        except self.pool._Warning as e:
            try:    cursor.close()
            except: pass
            if self.pool._debug:
                STACKF(0,str(e)+"\r\n",self.pool._debug, self.pool._log,name=self.pool.name)
            return None
        except:
            self.pool.Undo()
            raise
    
    
    def _SQLSelect(self, flds, cursor=None, table=None):
        """
        select one entry and convert to dictionary
        """
        pool = self.pool
        if not table:
            table = pool.MetaTable
            param = {"id": self.id}
        else:
            param = {"id": self.GetDataRef()}
        sql, values = pool.FmtSQLSelect(flds, param, dataTable = table, version=self.version, singleTable=1)
        c = 0
        if cursor is None:
            c = 1
            cursor = pool.connection.cursor()
        if pool._debug:
            STACKF(0,sql+"\r\n\r\n",pool._debug, pool._log,name=pool.name)
        try:
            cursor.execute(sql, values)
        except:
            pool.Undo()
            raise
        r = cursor.fetchone()
        if c:
            cursor.close()
        if not r:
            return None
        return pool.ConvertRecToDict(r, flds)


    def _SQLSelectAll(self, metaFlds, dataFlds, cursor=None):
        """
        select meta and data of one entry and convert to dictionary
        """
        pool = self.pool
        flds2 = list(metaFlds) + list(dataFlds)
        param = {"id": self.id}
        sql, values = pool.FmtSQLSelect(flds2, param, dataTable = self.GetDataTbl(), version=self.version)

        c = 0
        if cursor is None:
            c = 1
            cursor = pool.connection.cursor()
        if self.pool._debug:
            STACKF(0,sql+"\r\n\r\n",pool._debug, pool._log,name=pool.name)
        try:
            cursor.execute(sql, values)
        except:
            pool.Undo()
            raise
        r = cursor.fetchone()
        if c:
            cursor.close()
        if not r:
            raise TypeError(sql)
        # split data and meta
        meta = pool.ConvertRecToDict(r[:len(metaFlds)], metaFlds)
        data = pool.ConvertRecToDict(r[len(metaFlds):], dataFlds)
        return meta, data


    def _PreloadAll(self, cursor=None):
        if self.virtual:
            return True
        if not self.dataTbl or not self.dataRef:
            if not self._PreloadMeta(cursor):
                return False
            self._PreloadData(cursor)
            return True
        dataTbl = self.GetDataTbl()
        meta, data = self._SQLSelectAll(self.pool.structure.get(self.pool.MetaTable, version=self.version),
                                        self.pool.structure.get(dataTbl, version=self.version), cursor=cursor)
        if not meta:
            return False
        meta = self.pool.structure.deserialize(self.pool.MetaTable, None, meta)
        data = self.pool.structure.deserialize(dataTbl, None, data)
        self._UpdateCache(meta, data)
        return True


    def _PreloadMeta(self, cursor=None):
        if self.virtual:
            return True
        meta = self._SQLSelect(self.pool.structure.get(self.pool.MetaTable, self.version), cursor=cursor)
        if not meta:
            return False
        meta = self.pool.structure.deserialize(self.pool.MetaTable, None, meta)
        self._UpdateCache(meta)
        return True


    def _PreloadData(self, cursor=None):
        if self.virtual:
            return True
        dataTbl = self.GetDataTbl()
        data = self._SQLSelect(self.pool.structure.get(dataTbl, version=self.version), cursor=cursor, table=dataTbl)
        if not data:
            return False
        data = self.pool.structure.deserialize(dataTbl, None, data)
        self._UpdateCache(None, data)
        return True


    def _PreloadStdMeta(self, cursor=None):
        if self.virtual:
            return True
        meta = self._SQLSelect(self.pool.structure.stdMeta, cursor=cursor)
        if not meta:
            return False
        meta = self.pool.structure.deserialize(self.pool.MetaTable, None, meta)
        self._UpdateCache(meta)
        return True


    def _PreloadStdMetaData(self, cursor=None):
        if self.virtual:
            return True
        dataTbl = self.GetDataTbl()
        meta, data = self._SQLSelectAll(self.pool.structure.stdMeta, self.pool.structure.get(dataTbl, version=self.version), cursor=cursor)
        if not meta:
            return False
        meta = self.pool.structure.deserialize(self.pool.MetaTable, None, meta)
        data = self.pool.structure.deserialize(dataTbl, None, data)
        self._UpdateCache(meta, data)
        return True


    # Internal -------------------------------------------------------------------------------------------

    def _InitNew(self, dataTable = None, user = ""):
        """
        sets create date and created by to now
        """
        aC = self.pool.connection.cursor()
        self.dataTbl = dataTable
        aMeta = {}
        date = self.pool.GetDBDate()
        aMeta["pool_create"] = date
        aMeta["pool_change"] = date
        if user is None:
            user=""
        else:
            user=str(user)
        aMeta["pool_createdby"] = user
        aMeta["pool_changedby"] = user
        if self.dataTbl and self.dataTbl != "":
            aMeta["pool_datatbl"] = self.dataTbl
        self.meta.update(aMeta, force=True)


    def _UpdateCache(self, meta = None, data = None, files = None):
        if meta:
            self.meta.SetContent(meta)
        if data:
            self.data.SetContent(data)
        if files:
            self.files.SetContent(files)



class NotFound(Exception):
    """ raised if entry not found """

class FileNotFound(Exception):
    """ raised if physical file not found """

