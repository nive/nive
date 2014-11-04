# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import string, time

from nive.utils.dataPool2.dbManager import DatabaseManager
from nive.definitions import ConfigurationError

SQLITE3 = 0

try:    
    import sqlite3
    SQLITE3 = 1
except:
    pass

    
    
    
class Sqlite3Manager(DatabaseManager):
    """
    """
    modifyColumns = True #False

    def __init__(self):
        # might not be imported on startup
        import sqlite3
        self.db = None
        self.dbConn = None
        self.useUtf8 = True


    def Connect(self, databaseName = ""):
        self.dbConn = sqlite3.connect(databaseName)
        self.db = self.dbConn.cursor()
        return self.db != None


    # Options ----------------------------------------------------------------

    def ConvertConfToColumnOptions(self, conf):
        """
        field representation:
        {"id": "type", "datatype": "list", "size"/"maxLen": 0, "default": ""}

        datatypes:
        list -> list || listn

        string -> VARCHAR(size) NOT NULL DEFAULT default
        number -> INT NOT NULL DEFAULT default
        float -> FLOAT NOT NULL DEFAULT default
        bool -> TINYINT(4) NOT NULL DEFAULT default
        percent -> TINYINT(4) NOT NULL DEFAULT default
        text -> TEXT NOT NULL DEFAULT default
        htext -> TEXT NOT NULL DEFAULT default
        lines -> TEXT NOT NULL DEFAULT default
        xml -> TEXT NOT NULL DEFAULT default
        unit -> INT NOT NULL DEFAULT default
        unitlist -> VARCHAR(2048) NOT NULL DEFAULT default
        date -> TIMESTAMP NULL DEFAULT default
        datetime -> TIMESTAMP NULL DEFAULT default
        time -> TIMESTAMP NULL DEFAULT default
        timestamp -> TIMESTAMP
        listt -> VARCHAR(30) NOT NULL DEFAULT default
        listn -> SMALLINT NOT NULL DEFAULT default
        multilist, checkbox -> VARCHAR(2048) NOT NULL DEFAULT default
        [file] -> BLOB
        [bytesize] -> BIGINT(20) NOT NULL DEFAULT default
        url -> TEXT NOT NULL DEFAULT default
        """
        datatype = conf["datatype"]
        aStr = u""

        # convert datatype list
        if(datatype == "list"):
            if isinstance(conf["default"], basestring):
                datatype = "listt"
            else:
                datatype = "listn"

        if datatype in ("string", "email", "password"):
            if conf.get("size", conf.get("maxLen",0)) <= 3:
                aStr = u"CHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])
            else:
                aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype in ("number", "long", "int"):
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = long(aN)
            if conf.get("size", conf.get("maxLen",0)) == 4:
                aStr = u"TINYINT NOT NULL DEFAULT %d" % (aN)
            elif conf.get("size", conf.get("maxLen",0)) in (11,12):
                aStr = u"INTEGER NOT NULL DEFAULT %d" % (aN)
            else:
                aStr = u"INTEGER NOT NULL DEFAULT %d" % (aN)

        elif datatype == "float":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = float(aN)
            aStr = u"FLOAT NOT NULL DEFAULT %d" % (aN)

        elif datatype == "bool":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None or aN == "False":
                aN = 0
            if aN == "True":
                aN = 1
            if isinstance(aN, basestring):
                aN = int(aN)
            aStr = u"TINYINT NOT NULL DEFAULT %d" % (aN)

        elif datatype in ("text", "htext", "url", "urllist", "json", "code"):
            aStr = u"TEXT NOT NULL DEFAULT '%s'" % (conf["default"])

        elif datatype == "unit":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = long(aN)
            aStr = u"INTEGER NOT NULL DEFAULT %d" % (aN)

        elif datatype == "unitlist":
            aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype == "date":
            aD = conf["default"]
            if aD == () or aD == "()":
                aD = "NULL"
            if aD in ("now", "nowdate", "nowtime"):
                aD = ""
            if isinstance(aD, basestring) and not aD in ("NOW","NULL"):
                aD = self.ConvertDate(aD)
            if aD == "":
                aStr = u"TIMESTAMP NULL"
            else:
                aStr = u"TIMESTAMP NULL DEFAULT '%s'" % (aD)

        elif datatype == "datetime":
            aD = conf["default"]
            if aD == () or aD == "()":
                aD = "NULL"
            if aD in ("now", "nowdate", "nowtime"):
                aD = ""
            if isinstance(aD, basestring) and not aD in ("NOW","NULL"):
                aD = self.ConvertDate(aD)
            if aD == "":
                aStr = u"TIMESTAMP NULL"
            else:
                aStr = u"TIMESTAMP NULL DEFAULT '%s'" % (aD)

        elif datatype == "time":
            aD = conf["default"]
            if aD == () or aD == "()":
                aD = "NULL"
            if aD in ("now", "nowtime"):
                aD = ""
            if isinstance(aD, basestring) and not aD in ("NOW","NULL"):
                aD = self.ConvertDate(aD)
            if aD == "":
                aStr = u"TIMESTAMP NULL"
            else:
                aStr = u"TIMESTAMP NULL DEFAULT '%s'" % (aD)

        elif datatype == "timestamp":
            aStr = u"TIMESTAMP DEFAULT (datetime('now','localtime'))"

        elif datatype == "listt":
            aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype in ("listn", "codelist"):
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = int(aN)
            aStr = "SMALLINT NOT NULL DEFAULT %d" % (aN)

        elif datatype in ("multilist", "checkbox", "mselection", "mcheckboxes", "radio"):
            aStr = u"VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype == "file":
            aStr = u"BLOB"

        elif datatype == "bytesize":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, basestring):
                aN = long(aN)
            aStr = u"INTEGER NOT NULL DEFAULT %d" % (aN)

        if conf.get("unique"):
            aStr += " UNIQUE"
        return aStr



    # physical database structure ----------------------------------------------------------------

    def GetDatabases(self):
        return []


    def GetTables(self):
        if not self.IsDB():
            return []
        sql = u"""SELECT name FROM 
                   (SELECT * FROM sqlite_master UNION ALL
                    SELECT * FROM sqlite_temp_master)
                WHERE type='table'
                ORDER BY name"""
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
        self.db.execute(u"PRAGMA table_info(%s)" % (tableName))
        table = {}
        for c in self.db.fetchall():
            table[c[1]] = {"db": {"id": c[1], "type": c[2], "identity": c[5], "default": c[4], "null": c[3]}, 
                           "conf": None} 
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
        for aD in self.GetTables():
            if string.lower(aD[0]) == string.lower(tableName):
                return True
        return False


    def CreateTable(self, tableName, columns=None, createIdentity=True, primaryKeyName=u"id"):
        if not self.IsDB():
            return False
        if not tableName or tableName == u"":
            return False
        assert(tableName != u"user")
        if createIdentity:
            aSql = u"CREATE TABLE %s(%s INTEGER PRIMARY KEY AUTOINCREMENT" % (tableName, primaryKeyName)
            if columns:
                for c in columns:
                    if c.id == primaryKeyName:
                        continue
                    aSql += ","
                    aSql += c.id + u" " + self.ConvertConfToColumnOptions(c)
            aSql += u")"
        else:
            aSql = u"CREATE TABLE %s" % (tableName)
            if not columns:
                raise ConfigurationError, "No database fields defined."
            aCnt = 0
            aSql += u"("
            for c in columns:
                if aCnt:
                    aSql += u","
                aCnt = 1
                aSql += c.id + u" " + self.ConvertConfToColumnOptions(c)
            aSql += u")"
        self.db.execute(aSql)
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
        self.db.execute(u"alter table %s rename to %s" % (inTableName, inNewTableName))
        return True



    # Columns --------------------------------------------------------------
    """
    inColumnData --> "ColumnName ColumnDatdatatype ColumnOptions"
        Column Options --> [Not] [NULL] [DEFAULT 'default']
    SetPrimaryKey&SetUnique --> can also get a ColumnList
        ColumnList --> ColumnName1,ColumName2,...
    """

    def CreateColumn(self, tableName, columnName, columnOptions=u""):
        if not self.IsDB():
            return False
        if columnName == u"" or tableName == u"":
            return False
        if columnOptions == u"identity":
            return self.CreateIdentityColumn(tableName, columnName)
        self.db.execute(u"alter table %s add column %s %s" % (tableName, columnName, columnOptions))
        return True


    def CreateIdentityColumn(self, tableName, columnName):
        if not self.IsDB():
            return False
        return self.CreateColumn(tableName, columnName, u"INTEGER PRIMARY KEY AUTOINCREMENT")


    # Database Options ------------------------------------------------------------

    def IsDatabase(self, databaseName):
        try:
            db = sqlite3.connect(databaseName)
            db.close()
            return True
        except:
            return False

    def CreateDatabase(self, databaseName):
        return False

    def UseDatabase(self, databaseName):
        return False

