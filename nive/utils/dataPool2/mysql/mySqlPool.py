# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Data Pool MySql Module
----------------------
*Requires MySQL-python*. Use 'pip install MySQL-python' to install the package.
"""


import threading
from nive.definitions import OperationalError, ConfigurationError

try:
    import MySQLdb
except ImportError:
    # make tests pass without mysql package
    class MySQLdb(object):
        """ """
        OperationalError = None
        ProgrammingError = None
        Warning = None
        @staticmethod
        def connect(*args,**kw):
            raise ImportError("Python MySQLdb binding not available. Try 'pip install MySQL-python' to install the package.")
    
from nive.utils.utils import STACKF

from nive.utils.dataPool2.base import Base, Entry
from nive.utils.dataPool2.base import NotFound
from nive.utils.dataPool2.connection import Connection, ConnectionThreadLocal, ConnectionRequest

from nive.utils.dataPool2.mysql.dbManager import MySQLManager
from nive.utils.dataPool2.files import FileManager, FileEntry



class MySqlConnection(Connection):
    """
    MySql connection handling class

    config parameter in dictionary:
    user = database user
    password = password user
    host = host mysql server
    port = port mysql server
    db = initial database name

    timeout is set to 3.
    """
    # todo [3] unicode ?

    def connect(self):
        """ Close and connect to server """
        #t = time()
        conf = self.configuration
        use_unicode = conf.unicode
        charset = None
        if use_unicode:
            charset = "utf8"
        db = MySQLdb.connect(conf.host,
                             conf.user,
                             str(conf.password), 
                             port=conf.port or 3306,
                             db=conf.dbName, 
                             connect_timeout=conf.timeout, 
                             use_unicode=use_unicode, 
                             charset=charset)
        if not db:
            raise OperationalError("Cannot connect to database '%s.%s'" % (conf.host, conf.dbName))
        self._set(db)
        #print "connect:", time() - t
        return db
        

    def IsConnected(self):
        """ Check if database is connected """
        try:
            db = self._get()
            db.ping()
            return db.cursor()!=None
        except:
            return False


    def GetDBManager(self):
        """ returns the database manager obj """
        self.VerifyConnection()
        aDB = MySQLManager()
        aDB.SetDB(self.PrivateConnection())
        return aDB


    def FmtParam(self, param):
        """format a parameter for sql queries like literal for mysql db"""
        db = self._get()
        if not db:
            self.connect()
            db = self._get()
        return db.literal(param)


    def PrivateConnection(self):
        """ This function will return a new and raw connection. It is up to the caller to close this connection. """
        conf = self.configuration
        use_unicode = conf.unicode
        charset = None
        if use_unicode:
            charset = "utf8"
        db = MySQLdb.connect(conf.host,
                             conf.user,
                             str(conf.password), 
                             port=conf.port or 3306,
                             db=conf.dbName, 
                             connect_timeout=conf.timeout, 
                             use_unicode=use_unicode, 
                             charset=charset)
        return db



class MySqlConnThreadLocal(MySqlConnection, ConnectionThreadLocal):
    """
    Caches database connections as thread local values.
    """

    def __init__(self, config = None, connectNow = True):
        self.local = threading.local()
        MySqlConnection.__init__(self, config, connectNow)


class MySqlConnRequest(MySqlConnection, ConnectionRequest):
    """
    Caches database connections as request values. Uses thread local stack as fallback (e.g testing).
    """

    def __init__(self, config = None, connectNow = True):
        self.local = threading.local()
        MySqlConnection.__init__(self, config, connectNow)



class MySql(FileManager, Base):
    """
    Data Pool MySql 5 implementation
    """
    _OperationalError = MySQLdb.OperationalError
    _ProgrammingError = MySQLdb.ProgrammingError
    _Warning = MySQLdb.Warning
    _DefaultConnection = MySqlConnRequest


    def _GetInsertIDValue(self, cursor):
        cursor.execute("SELECT LAST_INSERT_ID()")
        return cursor.fetchone()[0]

               
    def _CreateNewID(self, table = "", dataTbl = None):
        #
        aC = self.connection.cursor()
        if table == "":
            table = self.MetaTable
        if table == self.MetaTable:
            if not dataTbl:
                raise ConfigurationError("Missing data table - Entry not created")

            # sql insert empty rec in meta table
            if self._debug:
                STACKF(0,"INSERT INTO %s () VALUES ()" % (dataTbl)+"\r\n",self._debug, self._log,name=self.name)
            try:
                aC.execute("INSERT INTO %s () VALUES ()" % (dataTbl))
            except self._Warning:
                pass
            # sql get id of created rec
            if self._debug:
                STACKF(0,"SELECT LAST_INSERT_ID()\r\n",0, self._log,name=self.name)
            aC.execute("SELECT LAST_INSERT_ID()")
            dataref = aC.fetchone()[0]
            # sql insert empty rec in meta table
            if self._debug:
                STACKF(0,"INSERT INTO %s (pool_datatbl, pool_dataref) VALUES ('%s', %s)"% (self.MetaTable, dataTbl, dataref),0, self._log,name=self.name)
            aC.execute("INSERT INTO %s (pool_datatbl, pool_dataref) VALUES ('%s', %s)"% (self.MetaTable, dataTbl, dataref))
            if self._debug:
                STACKF(0,"SELECT LAST_INSERT_ID()\r\n",0, self._log,name=self.name)
            aC.execute("SELECT LAST_INSERT_ID()")
            aID = aC.fetchone()[0]
            aC.close()
            return aID, dataref

        # sql insert empty rec in meta table
        if self._debug:
            STACKF(0,"INSERT INTO %s () VALUES ()" % (table)+"\r\n",self._debug, self._log,name=self.name)
        aC.execute("INSERT INTO %s () VALUES ()" % (table))
        # sql get id of created rec
        if self._debug:
            STACKF(0,"SELECT LAST_INSERT_ID()\r\n",0, self._log,name=self.name)
        aC.execute("SELECT LAST_INSERT_ID()")
        aID = aC.fetchone()[0]
        aC.close()
        return aID, 0


    # types/classes -------------------------------------------------------------------

    def _GetPoolEntry(self, id, **kw):
        try:
            return MySqlEntry(self, id, **kw)
        except NotFound:
            return None



    # MySql 4 tree structure --------------------------------------------------------------

    def GetParentPath4(self, id):
        """
        MySql 4 version
        returns id references of parents for id.
        """
        sql = """
        SELECT p0.pool_unitref as ref1,p1.pool_unitref as ref2,p2.pool_unitref as ref3,p3.pool_unitref as ref4,p4.pool_unitref as ref5,p5.pool_unitref as ref6,p6.pool_unitref as ref7
        FROM %(meta)s p0, %(meta)s p1, %(meta)s p2, %(meta)s p3, %(meta)s p4, %(meta)s p5, %(meta)s p6
        WHERE  p0.id = %(id)d
        and    p1.id = p0.pool_unitref
        and IF(p1.pool_unitref > 0, p2.id = p1.pool_unitref, p2.id = p0.pool_unitref)
        and IF(p2.pool_unitref > 0, p3.id = p2.pool_unitref, p3.id = p0.pool_unitref)
        and IF(p3.pool_unitref > 0, p4.id = p3.pool_unitref, p4.id = p0.pool_unitref)
        and IF(p4.pool_unitref > 0, p5.id = p4.pool_unitref, p5.id = p0.pool_unitref)
        and IF(p5.pool_unitref > 0, p6.id = p5.pool_unitref, p6.id = p0.pool_unitref)
        Group by ref1""" % {"meta":self.MetaTable, "id":int(id)}
        t = self.Query(sql)
        parents = []
        if len(t) == 0:
            return parents
        cnt = 7
        for i in range(0, cnt-1):
            id = t[0]
            if id == 0:
                break
            parents.insert(0, id)
        return parents


    def GetParentTitles4(self, id):
        """
        MySql 4 version
        returns titles of parents for id.
        """
        sql = """
        SELECT p0.pool_unitref as ref1,p0.title as t1,p1.pool_unitref as ref2,p1.title as t2,p2.pool_unitref as ref3,p2.title as t3,p3.pool_unitref as ref4,p3.title as t4,p4.pool_unitref as ref5,p4.title as t5,p5.pool_unitref as ref6,p5.title as t6,p6.pool_unitref as ref7,p6.title as t7
        FROM %(meta)s p0, %(meta)s p1, %(meta)s p2, %(meta)s p3, %(meta)s p4, %(meta)s p5, %(meta)s p6
        WHERE  p0.id = %(id)d
        and    p1.id = p0.pool_unitref
        and IF(p1.pool_unitref > 0, p2.id = p1.pool_unitref, p2.id = p0.pool_unitref)
        and IF(p2.pool_unitref > 0, p3.id = p2.pool_unitref, p3.id = p0.pool_unitref)
        and IF(p3.pool_unitref > 0, p4.id = p3.pool_unitref, p4.id = p0.pool_unitref)
        and IF(p4.pool_unitref > 0, p5.id = p4.pool_unitref, p5.id = p0.pool_unitref)
        and IF(p5.pool_unitref > 0, p6.id = p5.pool_unitref, p6.id = p0.pool_unitref)
        Group by ref1""" % {"meta":self.MetaTable, "id":int(id)}
        t = self.Query(sql)
        parents = []
        if len(t) == 0:
            return parents
        cnt = 4
        for i in range(1, cnt-1):
            title = t[0][i*2+1]
            parents.insert(0, self.EncodeText(title))
            if t[0][i*2] == 0:
                break
        return parents


    def _FmtListForQuery(self, values):
        return values
        #FmtParam = self.connection.FmtParam
        #return ",".join([FmtParam(v) for v in values])


class MySqlEntry(FileEntry, Entry):
    """
    Data Pool Entry MySql 5 implementation
    """


