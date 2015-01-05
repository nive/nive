# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#
import string, time

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
        self.dbConn = None
        self.engine = ""
        self.useUtf8 = True

    # Database Options ---------------------------------------------------------------------

    def Connect(self, databaseName = "", inIP = "", inUser = "", inPW = ""):
        self.dbConn = psycopg2.connect(database = databaseName, host = inIP, user = inUser, passwd = inPW)
        self.db = self.dbConn.cursor()
        return self.db != None

    # Options ----------------------------------------------------------------

    def ModifyColumn(self, tableName, columnName, inNewColumnName, columnOptions):
        if not self.IsDB():
            return False
        #print("alter table %s change %s %s %s" % (tableName, columnName, inNewColumnName, columnOptions))
        if columnOptions == u"" or columnName == u"" or tableName == u"":
            return False
        if inNewColumnName:
            self.db.execute(u"alter table %s rename column %s to %s" % (tableName, columnName, inNewColumnName))
        opt = columnOptions.split(u" ")
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
        date -> TIMESTAMP NULL DEFAULT default
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
                aStr = u"SMALLINT NOT NULL DEFAULT %d" % (aN)
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
            aStr = u"SMALLINT NOT NULL DEFAULT %d" % (aN)

        elif datatype in ("text", "htext", "url", "urllist", "json", "code", "lines"):
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
            aStr = u"TIMESTAMP DEFAULT NOW()"

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

        elif datatype in ("binary", "file"):
            aStr = u"BYTEA"

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
            table[c[0]] = {"db": {"id": c[0], "type": c[1]+size, "identity": c[4], "default": default, "null": c[3]}, 
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
        if not tableName:
            return False
        assert(tableName != "user")
        if createIdentity:
            aSql = u"CREATE TABLE %s(%s SERIAL PRIMARY KEY" % (tableName, primaryKeyName)
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
        try:
            self.db.execute(aSql)
        except:
            breakpoint=1
            raise
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

    def IsColumn(self, tableName, columnName):
        columns = self.GetColumns(tableName)
        cn = columnName.lower()
        if cn in columns and columns[cn].get("db"):
            return True
        return False


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
        return self.CreateColumn(tableName, columnName, u"SERIAL PRIMARY KEY")


