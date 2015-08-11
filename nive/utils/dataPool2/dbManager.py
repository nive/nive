# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

import string, time
from datetime import datetime

from nive.utils.utils import ConvertToDateTime
from nive.definitions import ConfigurationError, OperationalError




class DatabaseManager(object):
    """
    Base class for specific database servers
    
    SQL and administration calls are bases on MySql
    """

    modifyColumns = True

    def __init__(self):
        self.db = None
        self.dbConn = None
        self.useUtf8 = True

    # Database Options ---------------------------------------------------------------------

    def Connect(self, databaseName = "", inIP = "", inUser = "", inPW = ""):
        return self.db != None


    def SetDB(self, inDB):
        self.dbConn = inDB
        self.db = self.dbConn.cursor()
        return self.db != None


    def Close(self):
        if self.db:
            self.db.close()
        if self.dbConn:
            self.dbConn.close()
        self.db = None


    def IsDB(self):
        return self.db is not None


    # Options ----------------------------------------------------------------

    def ConvertDate(self, date):
        if not isinstance(date, datetime):
            date = ConvertToDateTime(date)
        if not date:
            return u""
        return date.strftime(u"%Y-%m-%d %H:%M:%S")


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
                    raise OperationalError, "timeout create table"
            return True

        columns = self.GetColumns(tableName, structure)

        for col in structure:
            name = col["id"]
            options = self.ConvertConfToColumnOptions(col)

            # skip id column
            if createIdentity and name == u"id":
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
                if not self.ModifyColumn(tableName, name, u"", options):
                    return False
            else:
                if not self.CreateColumn(tableName, name, options):
                    return False

        if createIdentity:
            if not self.IsColumn(tableName, u"id"):
                if not self.CreateIdentityColumn(tableName, u"id"):
                    return False
            
        return True


    def ConvertConfToColumnOptions(self, conf):
        """
        field representation:
        {"id": "type", "datatype": "list", "size"/"maxLen": 0, "default": ""}

        datatypes:
        list -> list || listn
        
        Example:

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
        self.db.execute(u"create database " + databaseName)
        self.dbConn.commit()
        return True


    def UseDatabase(self, databaseName):
        if not self.IsDB():
            return False
        #self.db.execute(u"use " + databaseName)
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
            if string.lower(aD[0]) == string.lower(tableName):
                return True
        return False


    def CreateTable(self, tableName, columns = None, createIdentity = True, primaryKeyName="id"):
        if not self.IsDB():
            return False
        if not tableName or tableName == "":
            return False
        assert(tableName != "user")
        aSql = u""
        if createIdentity:
            aSql = u"CREATE TABLE %s(%s INT UNSIGNED AUTO_INCREMENT UNIQUE NOT NULL PRIMARY KEY" % (tableName, primaryKeyName)
            if columns:
                for c in columns:
                    if c.id == primaryKeyName:
                        continue
                    aSql += ","
                    aSql += c.id + u" " + self.ConvertConfToColumnOptions(c)
            aSql += u")"
            aSql += u" AUTO_INCREMENT = 1 "
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
        aSql += u" ENGINE = %s" %(self.engine)
        if self.useUtf8:
            aSql += u" CHARACTER SET utf8 COLLATE utf8_general_ci"

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
        self.db.execute(u"alter table %s rename as %s" % (inTableName, inNewTableName))
        return True


    def DeleteTable(self, inTableName):
        if not self.IsDB():
            return False
        self.db.execute(u"drop table %s" % (inTableName))
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
        self.db.execute(u"alter table %s add column %s %s" % (tableName, columnName, columnOptions))
        return True


    def CreateIdentityColumn(self, tableName, columnName):
        if not self.IsDB():
            return False
        return self.CreateColumn(tableName, columnName, u"INT UNSIGNED AUTO_INCREMENT UNIQUE NOT NULL PRIMARY KEY")


    def ModifyColumn(self, tableName, columnName, inNewColumnName, columnOptions):
        if not self.IsDB():
            return False
        #print("alter table %s change %s %s %s" % (tableName, columnName, inNewColumnName, columnOptions))
        if columnOptions == "" or columnName == "" or tableName == "":
            return False
        aN = inNewColumnName
        if aN == "":
            aN = columnName
        self.db.execute(u"alter table %s change %s %s %s" % (tableName, columnName, aN, columnOptions))
        return True


    # physical database structure ----------------------------------------------------------------

    def GetDatabases(self):
        if not self.IsDB():
            return ""
        self.db.execute(u"show databases")
        return self.db.fetchall()


    def GetTables(self):
        if not self.IsDB():
            return ""
        self.db.execute(u"show tables")
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
        self.db.execute(u"show columns from %s" % (tableName))
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


