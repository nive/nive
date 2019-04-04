# -*- coding: latin-1 -*-

import unittest

from nive.definitions import DatabaseConf
from nive.utils.dataPool2.connection import *

from nive.tests import __local

# configuration ---------------------------------------------------------------------------
conn = DatabaseConf(
    dbName = __local.ROOT+"dummy.db"
)


class ConnectionTest(unittest.TestCase):
    """
    """
    def test_conn(self):
        self.assertTrue(Connection(conn))
        
    def test_conntl(self):
        self.assertTrue(ConnectionThreadLocal(conn))
    
    def test_connreq(self):
        self.assertTrue(ConnectionRequest(conn))



