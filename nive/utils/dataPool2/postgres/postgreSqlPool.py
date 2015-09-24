# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Data Pool Postgres Module
----------------------
*Requires psycopg2*. Use 'pip install python-psycopg2' to install the package.
"""


import threading

from nive.definitions import ConfigurationError
try:
    import psycopg2
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
except ImportError:
    # define fake psycopg class here to avoid test import errors if psycopg is not installed
    class psycopg2(object):
        OperationalError = None
        ProgrammingError = None
        Warning = None
        @staticmethod
        def connect(*args,**kw):
            raise ImportError, "Python postgres binding not available. Try 'pip install psycopg2' to install the package."
            
            
from nive.utils.utils import STACKF

from nive.utils.dataPool2.base import Base, Entry
from nive.utils.dataPool2.base import NotFound
from nive.utils.dataPool2.connection import Connection, ConnectionThreadLocal, ConnectionRequest

from nive.utils.dataPool2.postgres.dbManager import PostgresManager
from nive.utils.dataPool2.files import FileManager, FileEntry

from nive.definitions import OperationalError



class PostgresConnection(Connection):
    """
    postgres connection handling class

    config parameter in dictionary:
    dbName = initial database name
    user = database user

    password = password user
    host = host postgres server
    port = port postgres server

    user/host/port/password not mandatory if unix socket connection
    """
    #TODO add all psycopg2 connect options

    def connect(self):
        """ Close and connect to server """

        db = self.PrivateConnection()
        if not db:
            conf = self.configuration
            raise OperationalError, "Cannot connect to database '%s.%s'" % (conf.host, conf.dbName)
        self._set(db)
        return db

    def IsConnected(self):
        """ Check if database is connected """
        db = self._get()
        return db and not db.closed

    def GetDBManager(self):
        """ returns the database manager obj """
        self.VerifyConnection()
        manager = PostgresManager()
        manager.SetDB(self.PrivateConnection())
        return manager

    def PrivateConnection(self):
        """ This function will return a new and raw connection. It is up to the caller to close this connection. """
        conf = self.configuration
        kargs = {'database': conf.dbName,
                'connect_timeout': conf.timeout}

        if conf.host:
            kargs['host'] = conf.host
        if conf.port:
            kargs['port'] = conf.port
        if conf.user:
            kargs['user'] = conf.user

        return psycopg2.connect(**kargs)

    def FmtParam(self, param):
        """ 
        Format a parameter for sql queries like literal for db. This function is not
        secure for any values. 
        """
        if isinstance(param, (int, long, float)):
            return unicode(param)
        d = unicode(param)
        if d.find(u"'")!=-1:
            d = d.replace(u"'",u"\\'")
        return u"'%s'"%d


class PgConnThreadLocal(PostgresConnection, ConnectionThreadLocal):
    """
    Caches database connections as thread local values.
    """

    def __init__(self, config = None, connectNow = False):
        PostgresConnection.__init__(self, config, connectNow)


class PgConnRequest(PostgresConnection, ConnectionRequest):
    """
    Caches database connections as request values. Uses thread local stack as fallback (e.g testing).
    """

    def __init__(self, config = None, connectNow = False):
        self.local = threading.local()
        PostgresConnection.__init__(self, config, connectNow)

class PostgreSql(FileManager, Base):
    """
    Data Pool Postgres implementation
    """
    _OperationalError = psycopg2.OperationalError
    _ProgrammingError = psycopg2.ProgrammingError
    _Warning = psycopg2.Warning
    _DefaultConnection = PgConnRequest#PgConnThreadLocal
            

    def GetContainedIDs(self, base=0, sort=u"title", parameter=u""):
        """
        select list of all entries
        id needs to be first field, pool_unitref second
        """
        def _SelectIDs(base, ids, sql, cursor):
            cursor.execute(sql%(base))
            entries = cursor.fetchall()
            for e in entries:
                ids.append(e[0])
                ids = _SelectIDs(e[0], ids, sql, cursor)
            return ids
        if parameter != u"":
            parameter = u"AND " + parameter
        parameter = (u"WHERE pool_unitref=%d", parameter)
        sql = u"""SELECT id FROM %s %s ORDER BY %s""" % (self.MetaTable, u" ".join(parameter), sort)
        cursor = self.connection.cursor()
        ids = _SelectIDs(base, [], sql, cursor)
        cursor.close()
        return ids
    
    
    def _GetInsertIDValue(self, cursor):
        cursor.execute(u"SELECT LASTVAL()")
        return cursor.fetchone()[0]

    def _CreateNewID(self, table = u"", dataTbl = None):
        aC = self.connection.cursor()
        if table == u"":
            table = self.MetaTable
        if table == self.MetaTable:
            if not dataTbl:
                raise ConfigurationError("Missing data table - Entry not created")

            # sql insert empty rec in meta table
            if self._debug:
                STACKF(0,u"INSERT INTO %s DEFAULT VALUES" % (dataTbl)+"\r\n",self._debug, self._log,name=self.name)
            try:
                aC.execute(u"INSERT INTO %s DEFAULT VALUES" % (dataTbl))
            except self._Warning:
                pass
            # sql get id of created rec
            if self._debug:
                STACKF(0,u"SELECT LASTVAL()\r\n",0, self._log,name=self.name)
            aC.execute(u"SELECT LASTVAL()")
            dataref = aC.fetchone()[0]
            # sql insert empty rec in meta table
            if self._debug:
                STACKF(0,u"INSERT INTO %s (pool_datatbl, pool_dataref) VALUES ('%s', %s)"% (self.MetaTable, dataTbl, dataref),0, self._log,name=self.name)
            aC.execute(u"INSERT INTO %s (pool_datatbl, pool_dataref) VALUES ('%s', %s)"% (self.MetaTable, dataTbl, dataref))
            if self._debug:
                STACKF(0,u"SELECT LAST_INSERT_ID()\r\n",0, self._log,name=self.name)
            aC.execute(u"SELECT LASTVAL()")
            aID = aC.fetchone()[0]
            aC.close()
            return aID, dataref

        # sql insert empty rec in meta table
        if self._debug:
            STACKF(0,u"INSERT INTO %s () VALUES ()" % (table)+"\r\n",self._debug, self._log,name=self.name)
        aC.execute(u"INSERT INTO %s () VALUES ()" % (table))
        # sql get id of created rec
        if self._debug:
            STACKF(0,u"SELECT LAST_INSERT_ID()\r\n",0, self._log,name=self.name)
        aC.execute(u"SELECT LAST_INSERT_ID()")
        aID = aC.fetchone()[0]
        aC.close()
        return aID, 0

    # types/classes -------------------------------------------------------------------


    def _GetPoolEntry(self, id, **kw):
        try:
            return PostgreSqlEntry(self, id, **kw)
        except NotFound:
            return None


    def _FmtLimit(self, start, max):
        if start != None:
            return u"LIMIT %s OFFSET %s" % (unicode(max), unicode(start))
        return u"LIMIT %s" % (unicode(max))


class PostgreSqlEntry(FileEntry, Entry):
    """
    Data Pool Entry Postgres implementation
    """
