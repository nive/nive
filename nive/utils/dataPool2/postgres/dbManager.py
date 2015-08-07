# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#
import string, time
import logging

from nive.utils.dataPool2.dbManager import DatabaseManager
from nive.definitions import ConfigurationError


try:    
    import psycopg2
except:
    # ignore to make tests imports pass
    # __init__() will raise an import error
    pass


class PostgresManager(DatabaseManager):
    """
    """
    modifyColumns = True

    def __init__(self):
        # might not be imported on startup
        import psycopg2
        self.db = None
        self.dbname = ""
        self.dbConn = None
        self.engine = ""
        self.useUtf8 = True
        self.log = logging.getLogger("dbManager")

    # Database Options ---------------------------------------------------------------------

    def Connect(self, databaseName = "", ip = "", user = "", pw = ""):
        self.dbname = databaseName
        self.dbConn = psycopg2.connect(database = databaseName, host = ip, user = user, passwd = pw)
        self.db = self.dbConn.cursor()
        return self.db is not None

    # Options ----------------------------------------------------------------

    def ModifyColumn(self, tableName, columnName, newColumnName, columnOptions):
        if not self.IsDB():
            return False
        #print("alter table %s change %s %s %s" % (tableName, columnName, newColumnName, columnOptions))
        if not columnOptions or not columnName or not tableName:
            return False
        if newColumnName:
            self.log.debug(u"alter table %s rename column %s to %s" % (tableName, columnName, newColumnName))
            self.db.execute(u"alter table %s rename column %s to %s" % (tableName, columnName, newColumnName))
        opt = columnOptions.split(u" ")
        self.log.debug(u"alter table %s alter column %s type %s" % (tableName, columnName, opt[0]))
        self.db.execute(u"alter table %s alter column %s type %s" % (tableName, columnName, opt[0]))
        return True



    def ConvertConfToColumnOptions(self, conf):
        """
        field representation:
        {"id": "type", "datatype": "list", "size"/"maxLen": 0, "default": ""}

        datatypes:
        list -> list || listn

        string -> VARCHAR(size) NOT NULL DEFAULT default
        number -> INT NOT NULL DEFAULT default
        float -> FLOAT NOT NULL DEFAULT default
        bool -> SMALLINT(4) NOT NULL DEFAULT default
        percent -> SMALLINT(4) NOT NULL DEFAULT default
        text -> TEXT NOT NULL DEFAULT default
        htext -> TEXT NOT NULL DEFAULT default
        lines -> TEXT NOT NULL DEFAULT default
        xml -> TEXT NOT NULL DEFAULT default
        unit -> INT NOT NULL DEFAULT default
        unitlist -> VARCHAR(2048) NOT NULL DEFAULT default
        date -> DATE NULL DEFAULT default
        datetime -> TIMESTAMP NULL DEFAULT default
        time -> TIME NULL DEFAULT default
        timestamp -> TIMESTAMP
        listt -> VARCHAR(30) NOT NULL DEFAULT default
        listn -> SMALLINT NOT NULL DEFAULT default
        multilist, checkbox -> VARCHAR(2048) NOT NULL DEFAULT default
        binary, [file] -> BYTEA
        [bytesize] -> BIGINT(20) NOT NULL DEFAULT default
        url -> TEXT NOT NULL DEFAULT default
        """
        datatype = conf["datatype"]
        col = u""

        # convert datatype list
        if datatype == "list":
            if isinstance(conf["default"], basestring):
                datatype = "listt"
            else:
                datatype = "listn"

        if datatype in ("string", "email", "password"):
            if conf.get("size", 150) <= 3:
                col = u"CHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])
            else:
                col = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype in ("number", "long", "int"):
            cval = conf["default"]
            if cval in ("", " ", None):
                cval = 0
            if isinstance(cval, basestring):
                cval = long(cval)
            size = conf.get("size", 4)
            if size == 2:
                col = u"SMALLINT NOT NULL DEFAULT %d" % (cval)
            elif size == 8:
                col = u"BIGINT NOT NULL DEFAULT %d" % (cval)
            else:
                col = u"INTEGER NOT NULL DEFAULT %d" % (cval)

        elif datatype == "float":
            cval = conf["default"]
            if cval in ("", " ", None):
                cval = 0
            if isinstance(cval, basestring):
                cval = float(cval)
            col = u"FLOAT NOT NULL DEFAULT %d" % (cval)

        elif datatype == "bool":
            cval = conf["default"]
            if cval in ("", " ", None, "False", "0"):
                cval = 0
            if cval in ("True", "1"):
                cval = 1
            if isinstance(cval, basestring):
                cval = int(cval)
            col = u"SMALLINT NOT NULL DEFAULT %d" % (cval)

        elif datatype in ("text", "htext", "url", "urllist", "json", "code", "lines"):
            col = u"TEXT NOT NULL DEFAULT '%s'" % (conf["default"])

        elif datatype == "unit":
            cval = conf["default"]
            if cval in ("", " ", None):
                cval = 0
            if isinstance(cval, basestring):
                cval = long(cval)
            col = u"INTEGER NOT NULL DEFAULT %d" % (cval)

        elif datatype == "unitlist":
            col = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype == "date":
            cval = conf["default"]
            if cval == () or cval == "()":
                cval = "NULL"
            if cval in ("now", "nowdate", "nowtime"):
                cval = ""
            if isinstance(cval, basestring) and not cval in ("NOW","NULL"):
                cval = self.ConvertDate(cval)
            if not cval:
                col = u"DATE NULL"
            else:
                col = u"DATE NULL DEFAULT '%s'" % (cval)

        elif datatype == "datetime":
            cval = conf["default"]
            if cval == () or cval == "()":
                cval = "NULL"
            if cval in ("now", "nowdate", "nowtime"):
                cval = ""
            if isinstance(cval, basestring) and not cval in ("NOW","NULL"):
                cval = self.ConvertDate(cval)
            if not cval:
                col = u"TIMESTAMP NULL"
            else:
                col = u"TIMESTAMP NULL DEFAULT '%s'" % (cval)

        elif datatype == "time":
            cval = conf["default"]
            if cval == () or cval == "()":
                cval = "NULL"
            if cval in ("now", "nowtime"):
                cval = ""
            if isinstance(cval, basestring) and not cval in ("NOW","NULL"):
                cval = self.ConvertDate(cval)
            if cval == "":
                col = u"TIME NULL"
            else:
                col = u"TIME NULL DEFAULT '%s'" % (cval)

        elif datatype == "timestamp":
            col = u"TIMESTAMP DEFAULT NOW()"

        elif datatype == "listt":
            col = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype in ("listn", "codelist"):
            cval = conf["default"]
            if cval in ("", " ", None):
                cval = 0
            if isinstance(cval, basestring):
                cval = int(cval)
            col = "SMALLINT NOT NULL DEFAULT %d" % (cval)

        elif datatype in ("multilist", "checkbox", "mselection", "mcheckboxes", "radio"):
            col = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype in ("binary", "file"):
            col = u"BYTEA"

        elif datatype == "bytesize":
            cval = conf["default"]
            if cval in ("", " ", None):
                cval = 0
            if isinstance(cval, basestring):
                cval = long(cval)
            col = u"INTEGER NOT NULL DEFAULT %d" % (cval)

        if conf.get("unique"):
            col += " UNIQUE"
        return col



    # physical database structure ----------------------------------------------------------------

    def GetDatabases(self):
        if not self.IsDB():
            return []
        sql = u"""SELECT datname FROM pg_database;"""
        self.db.execute(sql)
        return self.db.fetchall()


    def GetTables(self):
        if not self.IsDB():
            return []
        sql = u"""SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"""
        self.db.execute(sql)
        return self.db.fetchall()


    def GetColumns(self, tableName, structure=None):
        """
        returns a dict of columns. each column is represented by and stored und column id:
        {db: {id, type, identity, default, null}, conf: FieldConf()}
        """
        if not self.IsDB():
            return []
        if not self.IsTable(tableName):
            return []
        self.db.execute(u"SELECT column_name, data_type, column_default, is_nullable, is_identity, character_maximum_length FROM information_schema.columns WHERE table_name ='%s';" % (tableName))
        table = {}
        for c in self.db.fetchall():
            if c[2]:
                default = c[2].replace(u"::character varying","")
            else:
                default = ""
            if c[5]:
                size = " (%s)"%str(c[5])
            else:
                size = ""
            table[c[0]] = {"db": {"id": c[0], "type": c[1]+size, "identity": c[4], "default": default, "null": c[3]}, "conf": None} 
        if structure:
            for conf in structure:
                if conf.id in table:
                    table[conf.id]["conf"] = conf
                else:
                    table[conf.id] = {"db": None, "conf": conf} 
        return table


    # Tables --------------------------------------------------------------
    """
    inTableEntrys --> ColumnName ColumnDataTyp ColumnOptions
    ColumnOptions --> [NOT][NULL][DEFAULT = ""][PRIMARY KEY][UNIQUE]
    """

    def IsTable(self, tableName):
        for cval in self.GetTables():
            if string.lower(cval[0]) == string.lower(tableName):
                return True
        return False


    def CreateTable(self, tableName, columns=None, createIdentity=True, primaryKeyName=u"id"):
        if not self.IsDB():
            return False
        if not tableName:
            return False
        assert(tableName != "user")
        if createIdentity:
            sql = u"CREATE TABLE %s(%s SERIAL PRIMARY KEY" % (tableName, primaryKeyName)
            if columns:
                for c in columns:
                    if c.id == primaryKeyName:
                        continue
                    sql += ","
                    sql += c.id + u" " + self.ConvertConfToColumnOptions(c)
            sql += u")"
        else:
            sql = u"CREATE TABLE %s" % (tableName)
            if not columns:
                raise ConfigurationError, "No database fields defined."
            aCnt = 0
            sql += u"("
            for c in columns:
                if aCnt:
                    sql += u","
                aCnt = 1
                sql += c.id + u" " + self.ConvertConfToColumnOptions(c)
            sql += u")"
        self.log.debug(sql)
        self.db.execute(sql)

        # delay until table is created
        time.sleep(0.3)
        aCnt = 1
        while not self.IsTable(tableName):
            time.sleep(0.5)
            aCnt += 1
            if aCnt == 30:
                return False
        return True

    def RenameTable(self, inTableName, inNewTableName):
        if not self.IsDB():
            return False
        self.log.debug(u"alter table %s rename to %s" % (inTableName, inNewTableName))
        self.db.execute(u"alter table %s rename to %s" % (inTableName, inNewTableName))
        return True



    # Columns --------------------------------------------------------------
    """
    inColumnData --> "ColumnName ColumnDatdatatype ColumnOptions"
        Column Options --> [Not] [NULL] [DEFAULT 'default']
    SetPrimaryKey&SetUnique --> can also get a ColumnList
        ColumnList --> ColumnName1,ColumName2,...
    """

    def IsColumn(self, tableName, columnName):
        columns = self.GetColumns(tableName)
        cn = columnName.lower()
        if cn in columns and columns[cn].get("db"):
            return True
        return False


    def CreateColumn(self, tableName, columnName, columnOptions=u""):
        if not self.IsDB():
            return False
        if not columnName or not tableName:
            return False
        if columnOptions == u"identity":
            columnOptions = u"SERIAL PRIMARY KEY"
        self.log.debug(u"alter table %s add column %s %s" % (tableName, columnName, columnOptions))
        self.db.execute(u"alter table %s add column %s %s" % (tableName, columnName, columnOptions))
        return True


    def CreateIdentityColumn(self, tableName, columnName):
        if not self.IsDB():
            return False
        return self.CreateColumn(tableName, columnName, u"SERIAL PRIMARY KEY")


