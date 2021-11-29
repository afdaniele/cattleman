import os
import sqlite3

ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "..")
INCLUDE = os.path.join(ROOT, "include")
LIB = os.path.join(INCLUDE, "cattleman")
TESTS = os.path.join(ROOT, "tests")


class DB:

    def __init__(self, fpath: str):
        self.fpath = fpath
        self.connection = sqlite3.connect(fpath)

    def execute(self, query: str):
        return self.connection.execute(query)

    def executescript(self, query: str):
        return self.connection.executescript(query)

    def commit(self):
        return self.connection.commit()

    def __del__(self):
        self.connection.close()


def get_path(db_name: str):
    # path to database
    db_fpath = os.path.join(TESTS, "databases", f"{db_name}.sqlite")
    return os.path.abspath(db_fpath)


def make_empty(db_name: str):
    # path to database
    db_fpath = get_path(db_name)
    print("Producing: ", db_fpath)
    # remove if exists
    if os.path.isfile(db_fpath):
        os.remove(db_fpath)
    # open database object
    db = DB(db_fpath)
    # create structure
    schema = os.path.join(LIB, "schemas", "database", "1.0", "schema.sql")
    with open(schema, "rt") as fin:
        db.executescript(fin.read())
    # return database
    return db