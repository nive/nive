
import unittest

from nive.tests import db_app
from nive.tests import __local

from nive.search import Search

# -----------------------------------------------------------------

class SearchTest_db:

    def setUp(self):
        self._loadApp()
        db_app.populate(self)


    def tearDown(self):
        self._closeApp(True)

    
    def test_search(self):
        r = Search(self.app.root)
        #test_tree
        self.assertTrue(len(r.TreeParentIDs(self.lastid))==2)
        self.assertTrue(len(r.TreeParentTitles(self.lastid))==2)
        self.assertTrue(len(r.TreeParentIDs(self.ids[3]))==0)
        self.assertTrue(len(r.TreeParentTitles(self.ids[3]))==0)

        #test_select
        self.assertTrue(r.Select())
        self.assertTrue(r.SelectDict())
        self.assertTrue(r.Select(pool_type="type1"))
        self.assertTrue(r.SelectDict(pool_type="type1"))
        self.assertFalse(r.Select(parameter={"pool_type": "type"}, operators={"pool_type": "="}, sort="id", ascending = 0))
        self.assertFalse(r.SelectDict(parameter={"pool_type": "type"}, operators={"pool_type": "="}, sort="id", ascending = 0))
        self.assertTrue(r.Select(parameter={"pool_type": "type"}, operators={"pool_type": "LIKE"}, sort="id", ascending = 0))
        self.assertTrue(r.SelectDict(parameter={"pool_type": "type"}, operators={"pool_type": "LIKE"}, sort="id", ascending = 0))
        self.assertTrue(r.Select(pool_type="type1", parameter={}, fields=["id","pool_filename","ftext","fnumber","fdate"], start=10, max=1))
        self.assertTrue(r.SelectDict(pool_type="type1", parameter={}, fields=["id","pool_filename","ftext","fnumber","fdate"], start=10, max=1))
        self.assertTrue(r.Select(parameter={"pool_type": "notype", "pool_filename": "others"}, logicalOperator="or", operators={"pool_type":"LIKE", "pool_filename":"LIKE"}))
        self.assertTrue(r.SelectDict(parameter={"pool_type": "notype", "pool_filename": "others"}, logicalOperator="or", operators={"pool_type":"LIKE", "pool_filename":"LIKE"}))
        self.assertFalse(r.Select(parameter={"pool_type": "notype", "pool_filename": "notitle"}, logicalOperator="or", operators={"pool_type":"LIKE", "pool_filename":"LIKE"}))
        self.assertFalse(r.SelectDict(parameter={"pool_type": "notype", "pool_filename": "notitle"}, logicalOperator="or", operators={"pool_type":"LIKE", "pool_filename":"LIKE"}))
        self.assertTrue(r.Select(fields=["pool_filename"], groupby="pool_filename"))
        self.assertTrue(r.SelectDict(fields=["pool_filename"], groupby="pool_filename"))
        self.assertTrue(r.Select(condition="id > 23"))
        self.assertTrue(r.SelectDict(condition="id > 23"))

        #test_codelists
        pool_type="type1"
        name_field="pool_filename"
        self.assertTrue(r.GetEntriesAsCodeList(pool_type, name_field))
        self.assertTrue(r.GetEntriesAsCodeList2(name_field))
        self.assertTrue(r.GetGroupAsCodeList(pool_type, name_field))
        self.assertTrue(r.GetGroupAsCodeList2(name_field))
        parameter = {"pool_state":1}
        operators = {"pool_state":"<="}
        self.assertTrue(r.GetEntriesAsCodeList(pool_type, name_field, parameter= parameter, operators = operators))
        self.assertTrue(r.GetEntriesAsCodeList2(name_field, parameter= parameter, operators = operators))
        self.assertTrue(r.GetGroupAsCodeList(pool_type, name_field, parameter= parameter, operators = operators))
        self.assertTrue(r.GetGroupAsCodeList2(name_field, parameter= parameter, operators = operators))

        #test_conversion
        pool_type="type1"
        r.FilenameToID("number1")
        r.IDToFilename(self.lastid)
        dataref = r.Select(parameter={"pool_type": pool_type}, fields=["id","pool_dataref"], max=1)[0]
        self.assertTrue(r.ConvertDatarefToID(pool_type, dataref[1])==dataref[0])
        self.assertTrue(r.GetMaxID())

        #test_refs
        # todo [3] fix GetReferences
        #self.assertTrue(r.GetReferences(self.ids[0]))
        #self.assertTrue(r.GetReferences(self.ids[0], types=["type1"]))

        #test_search
        r = Search(self.app.root)
        parameter = {"pool_state":1}
        operators = {"pool_state":"<="}
        pool_type = "type1"
        fields1 = ["id","pool_filename","pool_state","pool_unitref"]
        fields2 = ["id","pool_filename","pool_state","pool_unitref","ftext"]
        fields3 = ["id","ftext"]

        d=r.Select(fields=["-count(*)"])
        self.assertTrue(r.Select(parameter=parameter, fields=fields1, start=0, max=100))
        self.assertTrue(r.Select(pool_type=pool_type, parameter=parameter, fields=fields2, start = 0, max=100, operators=operators))
        self.assertTrue(r.SelectDict(parameter=parameter, fields=fields1, start=0, max=100))
        self.assertTrue(r.SelectDict(pool_type=pool_type, parameter=parameter, fields=fields2, start = 0, max=100, operators=operators))

        self.assertTrue(r.Search(parameter, fields = fields1, sort = "pool_filename", ascending = 1, start = 0, max = 100)["count"])
        self.assertTrue(r.SearchType(pool_type, parameter, fields = fields2, sort = "pool_filename", ascending = 1, start = 0, max = 100, operators=operators)["count"])
        self.assertTrue(r.SearchData(pool_type, {}, fields = fields3, sort = "id", ascending = 1, start = 0, max = 100, operators={})["count"])
        self.assertTrue(r.SearchFulltext("text", fields = fields1, sort = "pool_filename", ascending = 1, start = 0, max = 300)) #["count"]
        self.assertTrue(r.SearchFulltextType(pool_type, "text", fields = fields2, sort = "pool_filename", ascending = 1, start = 0, max = 300))   #["count"]
        r.SearchFilename("file1.txt", parameter, fields = [], sort = "pool_filename", ascending = 1, start = 0, max = 100, operators=operators)
        
class SearchTest_db_sqlite(SearchTest_db, __local.SqliteTestCase):
    """
    see tests.__local
    """

class SearchTest_db_mysql(SearchTest_db, __local.MySqlTestCase):
    """
    see tests.__local
    """

class SearchTest_db_pg(SearchTest_db, __local.PostgreSqlTestCase):
    """
    see tests.__local
    """
