
from . import base, files, connection


class TestConnection(connection.Connection):
    """
    Non functional database connection class. For testing.
    """

    placeholder = "%s"

    def __init__(self, config=None, connectNow=True):
        self.configuration = config
        self.db = None

    # dbapi like functions --------------------------------------------------------------

    def cursor(self):
        return None

    def rollback(self):
        """ Calls rollback on the current transaction, if supported """
        return

    def commit(self):
        """ Calls commit on the current transaction, if supported """
        return

    def connect(self):
        """ Close and connect to server """
        return

    def close(self):
        """ Close database connection """
        return

    def ping(self):
        """ ping database server """
        return 1

    def IsConnected(self):
        """ Check if database is connected """
        return True

    def VerifyConnection(self):
        """
        reconnects if not connected. If revalidate is larger than 0 IsConnected() will only be called
        after `revalidate` time
        """
        return True

    @property
    def dbapi(self):
        """ returns the dbapi database connection """
        return None

    def PrivateConnection(self):
        """ """
        return None

    def FmtParam(self, param):
        """
        Format a parameter for sql queries like literal for db. This function is not
        secure for any values.
        """
        if isinstance(param, (int, float)):
            return str(param)
        d = str(param)
        if d.find('"') != -1:
            d = d.replace('"', '\\"')
        return '"%s"' % d

    def GetDBManager(self):
        """ returns the database manager obj """
        return None



class TestingPool(files.FileManager, base.Base):
    """
    Data Pool Sqlite3 implementation
    """
    _DefaultConnection = TestConnection
    _EmptyValues = []

    # types/classes -------------------------------------------------------------------

    def _GetPoolEntry(self, id, **kw):
        return None
