import os
import sqlite3
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..")
INCLUDE = os.path.join(ROOT, "include")
LIB = os.path.join(INCLUDE, "cattleman")
TESTS = os.path.join(ROOT, "tests")

sys.path.insert(0, INCLUDE)

from cattleman.configuration import load_configuration_from_database


class DB:

    def __init__(self, fpath: str = ":memory:"):
        self.connection = sqlite3.connect(fpath)

    def execute(self, query: str):
        return self.connection.execute(query)

    def executescript(self, query: str):
        return self.connection.executescript(query)

    def __del__(self):
        self.connection.close()


class TestDB(unittest.TestCase):

    @staticmethod
    def _make_empty() -> DB:
        script = os.path.join(LIB, "schemas", "database", "1.0", "schema.sql")
        db = DB()
        with open(script, "rt") as fin:
            db.executescript(fin.read())
        return db

    @staticmethod
    def _get_db_path(num: int):
        return os.path.join(TESTS, "databases", f"db{num}.sqlite")

    @staticmethod
    def _load_db(num: int):
        return DB(TestDB._get_db_path(num))

    def test_make_empty(self):
        TestDB._make_empty()

    def test_load_empty(self):
        db_path = TestDB._get_db_path(0)
        load_configuration_from_database(db_path)







if __name__ == '__main__':
    unittest.main()
