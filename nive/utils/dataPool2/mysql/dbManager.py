# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import string, time
from datetime import datetime

from nive.definitions import OperationalError, ConfigurationError
from nive.utils.utils import ConvertToDateTime
from nive.utils.dataPool2.dbManager import DatabaseManager

try:    
    import MySQLdb
except:    
    # ignore to make tests imports pass
    # __init__() will raise an import error
    pass



class MySQLManager(DatabaseManager):
    """
    """

    modifyColumns = True

    def __init__(self):
        # might not be imported on startup
        import MySQLdb
        self.db = None
        self.dbConn = None
        self.engine = "MyISAM"
        self.useUtf8 = True

    # Database Options ---------------------------------------------------------------------

    def Connect(self, databaseName = "", inIP = "", inUser = "", inPW = ""):
        self.dbConn = MySQLdb.connect(db = databaseName, host = inIP, user = inUser, passwd = inPW)
        self.db = self.dbConn.cursor()
        return self.db != None


    def SetDB(self, inDB):
        self.dbConn = inDB
        self.db = self.dbConn.cursor()
        return self.db != None


    def Close(self):
        try:
            self.dbConn.close()
            self.db.close()
        except:
            pass
        self.db = None


    def IsDB(self):
        return self.db != None


    # Options ----------------------------------------------------------------

    def ConvertDate(self, date):
        if not isinstance(date, datetime):
            date = ConvertToDateTime(date)
        if not date:
            return ""
        return date.strftime("%Y-%m-%d %H:%M:%S")


    def UpdateStructure(self, tableName, structure, modify = None, createIdentity = True):
        """
        modify = None to skip changing existing columns, list of column ids to modify if changed
        """
        # check table exists
        if not self.IsTable(tableName):
            if not self.CreateTable(tableName, columns=structure, createIdentity=createIdentity):
                return False
            # delay until table is created
            time.sleep(0.3)
            aCnt = 1
            while not self.IsTable(tableName):
                time.sleep(0.5)
                aCnt += 1
                if aCnt == 10:
                    raise OperationalError("timeout create table")
            return True

        columns = self.GetColumns(tableName, structure)

        for col in structure:
            name = col["id"]
            options = self.ConvertConfToColumnOptions(col)

            # skip id column
            if createIdentity and name == "id":
                continue

            if not self.IsColumn(tableName, name):
                if not self.CreateColumn(tableName, name, options):
                    return False
                continue

            if not modify:
                continue

            if not name in modify:
                continue

            # modify column settings
            if name in columns and columns[name].get("db"):
                if not self.ModifyColumn(tableName, name, "", options):
                    return False
            else:
                if not self.CreateColumn(tableName, name, options):
                    return False

        if createIdentity:
            if not self.IsColumn(tableName, "id"):
                if not self.CreateIdentityColumn(tableName, "id"):
                    return False
            
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
        bool -> TINYINT(4) NOT NULL DEFAULT default
        percent -> TINYINT(4) NOT NULL DEFAULT default
        text -> TEXT NOT NULL DEFAULT default
        htext -> TEXT NOT NULL DEFAULT default
        lines -> TEXT NOT NULL DEFAULT default
        xml -> TEXT NOT NULL DEFAULT default
        unit -> INT NOT NULL DEFAULT default
        unitlist -> VARCHAR(2048) NOT NULL DEFAULT default
        date -> DATE NULL DEFAULT default
        datetime -> DATETIME NULL DEFAULT default
        time -> TIME NULL DEFAULT default
        timestamp -> TIMESTAMP
        listt -> VARCHAR(30) NOT NULL DEFAULT default
        listn -> SMALLINT NOT NULL DEFAULT default
        multilist, checkbox -> VARCHAR(2048) NOT NULL DEFAULT default
        json -> TEXT
        [file] -> BLOB
        [bytesize] -> BIGINT(20) NOT NULL DEFAULT default
        url -> TEXT NOT NULL DEFAULT default
        """
        datatype = conf["datatype"]
        aStr = ""

        # convert datatype list
        if datatype == "list":
            if isinstance(conf["default"], str):
                datatype = "listt"
            else:
                datatype = "listn"

        if datatype in ("string", "email", "password"):
            if conf.get("size", conf.get("maxLen",0)) <= 3:
                aStr = "CHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])
            else:
                aStr = "VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype in ("number", "long", "int"):
            aN = conf["default"]
            if aN in ("", " ", None):
                aN = 0
            if isinstance(aN, str):
                aN = int(aN)
            if conf.get("size", conf.get("maxLen",0)) == 4:
                aStr = "TINYINT(4) NOT NULL DEFAULT %d" % (aN)
            elif conf.get("size", conf.get("maxLen",0)) >16:
                aStr = "BIGINT(20) NOT NULL DEFAULT %d" % (aN)
            else:
                aStr = "INT NOT NULL DEFAULT %d" % (aN)

        elif datatype == "float":
            aN = conf["default"]
            if aN in ("", " ", None):
                aN = 0
            if isinstance(aN, str):
                aN = float(aN)
            aStr = "FLOAT NOT NULL DEFAULT %d" % (aN)

        elif datatype == "bool":
            aN = conf["default"]
            if aN in ("", " ", None, "False"):
                aN = 0
            elif aN == "True":
                aN = 1
            elif isinstance(aN, str):
                aN = int(aN)
            aStr = "TINYINT(4) NOT NULL DEFAULT %d" % (aN)

        elif datatype in ("text", "htext", "url", "urllist", "json", "code"):
            aStr = "TEXT NOT NULL" # DEFAULT '%s'" % (conf["default"])

        elif datatype == "unit":
            aN = conf["default"]
            if aN == "" or aN == " " or aN == None:
                aN = 0
            if isinstance(aN, str):
                aN = int(aN)
            aStr = "INT UNSIGNED NOT NULL DEFAULT %d" % (aN)

        elif datatype == "unitlist":
            aStr = "VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype == "date":
            aD = conf["default"]
            if aD == () or aD == "()":
                aD = "NULL"
            elif aD in ("now", "nowdate", "nowtime"):
                aD = ""
            if isinstance(aD, str) and not aD in ("NOW","NULL"):
                aD = self.ConvertDate(aD)
            if aD == "":
                aStr = "DATE NULL"
            else:
                aStr = "DATE NULL DEFAULT '%s'" % (aD)

        elif datatype == "datetime":
            aD = conf["default"]
            if aD == () or aD == "()":
                aD = "NULL"
            elif aD in ("now", "nowdate", "nowtime"):
                aD = ""
            if isinstance(aD, str) and not aD in ("NOW","NULL"):
                aD = self.ConvertDate(aD)
            if aD == "":
                aStr = "DATETIME NULL"
            else:
                aStr = "DATETIME NULL DEFAULT '%s'" % (aD)

        elif datatype == "time":
            aD = conf["default"]
            if aD == () or aD == "()":
                aD = "NULL"
            elif aD in ("now", "nowtime"):
                aD = ""
            if isinstance(aD, str) and not aD in ("NOW","NULL"):
                aD = self.ConvertDate(aD)
            if aD == "":
                aStr = "TIME NULL"
            else:
                aStr = "TIME NULL DEFAULT '%s'" % (aD)

        elif datatype == "timestamp":
            aStr = "TIMESTAMP"

        elif datatype == "listt":
            aStr = "VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype == "listn" or datatype == "codelist":
            aN = conf["default"]
            if aN in ("", " ", None):
                aN = 0
            elif isinstance(aN, str):
                aN = int(aN)
            aStr = "SMALLINT(6) NOT NULL DEFAULT %d" % (aN)

        elif datatype in ("multilist", "mselection", "checkbox", "mcheckboxes", "radio"):
            aStr = "VARCHAR(%d) NOT NULL DEFAULT '%s'" % (conf.get("size", conf.get("maxLen",0)), conf["default"])

        elif datatype == "file":
            aStr = "BLOB"

        elif datatype == "bytesize":
            aN = conf["default"]
            if aN in ("", " ", None):
                aN = 0
            if isinstance(aN, str):
                aN = int(aN)
            aStr = "BIGINT(20) NOT NULL DEFAULT %d" % (aN)

        if conf.get("unique"):
            aStr += " UNIQUE"
        return aStr


    # Database ------------------------------------------------------------

    def IsDatabase(self, databaseName):
        for aD in self.GetDatabases():
            if aD[0] == databaseName:
                return True
        return False

    def CreateDatabase(self, databaseName):
        if not self.IsDB():
            return False
        self.db.execute("create database " + databaseName)
        self.dbConn.commit()
        return True


    def UseDatabase(self, databaseName):
        if not self.IsDB():
            return False
        #self.db.execute("use " + databaseName)
        return True


    # Table --------------------------------------------------------------
    """
    inTableEntrys --> ColumnName ColumnDataTyp ColumnOptions
    ColumnOptions --> [NOT][NULL][DEFAULT = ""][PRIMARY KEY][UNIQUE]

    ENGINE = MyISAM
    CHARACTER SET utf8 COLLATE utf8_general_ci;

    ENGINE = InnoDB
    CHARACTER SET utf8 COLLATE utf8_general_ci;
    """

    def IsTable(self, tableName):
        for aD in self.GetTables():
            if aD[0].lower() == tableName.lower():
                return True
        return False


    def CreateTable(self, tableName, columns = None, createIdentity = True, primaryKeyName="id"):
        if not self.IsDB():
            return False
        if not tableName or tableName == "":
            return False
        assert(tableName != "user")
        aSql = ""
        if createIdentity:
            aSql = "CREATE TABLE %s(%s INT UNSIGNED AUTO_INCREMENT UNIQUE NOT NULL PRIMARY KEY" % (tableName, primaryKeyName)
            if columns:
                for c in columns:
                    if c.id == primaryKeyName:
                        continue
                    aSql += ","
                    aSql += c.id + " " + self.ConvertConfToColumnOptions(c)
            aSql += ")"
            aSql += " AUTO_INCREMENT = 1 "
        else:
            aSql = "CREATE TABLE %s" % (tableName)
            if not columns:
                raise ConfigurationError("No database fields defined.")
            aCnt = 0
            aSql += "("
            for c in columns:
                if aCnt:
                    aSql += ","
                aCnt = 1
                aSql += c.id + " " + self.ConvertConfToColumnOptions(c)
            aSql += ")"
        aSql += " ENGINE = %s" %(self.engine)
        if self.useUtf8:
            aSql += " CHARACTER SET utf8 COLLATE utf8_general_ci"

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
        self.db.execute("alter table %s rename as %s" % (inTableName, inNewTableName))
        return True


    def DeleteTable(self, inTableName):
        if not self.IsDB():
            return False
        self.db.execute("drop table %s" % (inTableName))
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
        cn = columnName
        if cn in columns and columns[cn].get("db"):
            return True
        return False


    def CreateColumn(self, tableName, columnName, columnOptions):
        if not self.IsDB():
            return False
        #print("alter table %s add column %s %s" % (tableName, columnName, columnOptions))
        if columnOptions == "" or columnName == "" or tableName == "":
            return False
        if columnOptions == "identity":
            return self.CreateIdentityColumn(tableName, columnName)
        self.db.execute("alter table %s add column %s %s" % (tableName, columnName, columnOptions))
        return True


    def CreateIdentityColumn(self, tableName, columnName):
        if not self.IsDB():
            return False
        return self.CreateColumn(tableName, columnName, "INT UNSIGNED AUTO_INCREMENT UNIQUE NOT NULL PRIMARY KEY")


    def ModifyColumn(self, tableName, columnName, inNewColumnName, columnOptions):
        if not self.IsDB():
            return False
        #print("alter table %s change %s %s %s" % (tableName, columnName, inNewColumnName, columnOptions))
        if columnOptions == "" or columnName == "" or tableName == "":
            return False
        aN = inNewColumnName
        if aN == "":
            aN = columnName
        self.db.execute("alter table %s change %s %s %s" % (tableName, columnName, aN, columnOptions))
        return True


    # physical database structure ----------------------------------------------------------------

    def GetDatabases(self):
        if not self.IsDB():
            return ""
        self.db.execute("show databases")
        return self.db.fetchall()


    def GetTables(self):
        if not self.IsDB():
            return ""
        self.db.execute("show tables")
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
        self.db.execute("show columns from %s" % (tableName))
        table = {}
        for c in self.db.fetchall():
            table[c[0]] = {"db": {"id": c[0], "type": c[1], "identity": c[3]!="", "default": c[4], "null": ""}, 
                           "conf": None} 
        if structure:
            for conf in structure:
                if conf.id in table:
                    table[conf.id]["conf"] = conf
                else:
                    table[conf.id] = {"db": None, "conf": conf} 
        return table


