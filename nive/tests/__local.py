

import sys
from nive.definitions import DatabaseConf


# real database test configuration
# change these to fit your system
ENABLE_MYSQL_TESTS = True
try:
    import MySQLdb
except ImportError:
    ENABLE_MYSQL_TESTS = False


WIN = sys.platform == "win32"

# sqlite and mysql
if WIN:
    ROOT = "c:\\Temp\\nive\\"
else:
    ROOT = "/var/tmp/nive/"



MYSQL_CONF = DatabaseConf(
    context = "MySql",
    dbName = "ut_nive",
    host = "localhost",
    user = "root",
    password = "",
    port = "",
    fileRoot = ROOT
)

