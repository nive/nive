# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Data Pool Postgres Module
----------------------
*Requires psycopg2*. Use 'pip install python-psycopg2' to install the package.
"""


import string, re, os
import threading
from time import time, localtime

try:
    import psycopg2
except ImportError:
    # define fake psycopg class here to avoid test import errors if psycopg is not installed
    class psycopg2(object):
        OperationalError = None
        ProgrammingError = None
        Warning = None

from nive.utils.utils import STACKF

from nive.utils.dataPool2.base import Base, Entry
from nive.utils.dataPool2.base import NotFound
from nive.utils.dataPool2.connection import Connection, ConnectionThreadLocal, ConnectionRequest

from nive.utils.dataPool2.postgres.dbManager import PostgresManager
from nive.utils.dataPool2.files import FileManager, FileEntry





class PostgresConnection(Connection):
    """
    postgres connection handling class

    config parameter in dictionary:
    user = database user
    password = password user
    host = host postgres server
    port = port postgres server
    db = initial database name

    timeout is set to 3.
    """

    def connect(self):
        """ Close and connect to server """
        #t = time()
        conf = self.configuration
        db = psycopg2.connect(host=conf.host, 
                              port=conf.port or None,
                              database=conf.dbName, 
                              user=conf.user, 
                              password=str(conf.password), 
                              connect_timeout=conf.timeout)
        if not db:
            raise OperationalError, "Cannot connect to database '%s.%s'" % (conf.host, conf.dbName)
        self._set(db)
        #print "connect:", time() - t
        return db
        

    def IsConnected(self):
        """ Check if database is connected """
        try:
            db = self._get()
            return db.cursor()!=None
        except:
            return False


    def GetDBManager(self):
        """ returns the database manager obj """
        self.VerifyConnection()
        aDB = PostgresManager()
        aDB.SetDB(self.PrivateConnection())
        return aDB


    def PrivateConnection(self):
        """ This function will return a new and raw connection. It is up to the caller to close this connection. """
        conf = self.configuration
        return psycopg2.connect(host=conf.host, 
                                port=conf.port or None,
                                database=conf.dbName, 
                                user=conf.user, 
                                password=str(conf.password), 
                                connect_timeout=conf.timeout)


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
            

    # types/classes -------------------------------------------------------------------

    def _GetPoolEntry(self, id, **kw):
        try:
            return PostgreSqlEntry(self, id, **kw)
        except NotFound:
            return None






class PostgreSqlEntry(FileEntry, Entry):
    """
    Data Pool Entry Postgres implementation
    """

    def _FmtLimit(self, start, max):
        if start != None:
            return u"OFFSET %s LIMIT %s" % (unicode(start), unicode(max))
        return u"LIMIT %s" % (unicode(max))
    
