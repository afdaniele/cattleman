import os
import sqlite3
from threading import Semaphore
from typing import Dict, Iterable

from cattleman.constants import DATABASES_DIR, DATABASE_SCHEMA_VERSION
from cattleman.exceptions import DatabaseNotFoundException

ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)))


class Database:

    def __init__(self, name: str):
        os.makedirs(DATABASES_DIR, exist_ok=True)
        os.chmod(DATABASES_DIR, mode=0o700)
        # ---
        self._db_fpath = os.path.join(DATABASES_DIR, f"{name}.db")
        self._db_fpath = os.environ.get(f"CATTLEMAN_{name.upper()}_DB", self._db_fpath)
        self._db = sqlite3.connect(self._db_fpath)
        self._db.row_factory = sqlite3.Row
        self._lock = Semaphore()
        self._ensure_structure()

    def execute(self, sql: str, *args):
        with self._lock:
            return self._db.execute(sql, args)

    def executemany(self, sql: str, seq_of_parameters: Iterable[Iterable]):
        with self._lock:
            return self._db.executemany(sql, seq_of_parameters)

    def executescript(self, sql_script: str):
        with self._lock:
            return self._db.executescript(sql_script)

    def commit(self):
        with self._lock:
            return self._db.commit()

    def _ensure_structure(self):
        schema = os.path.join(ROOT, "schemas", "database", DATABASE_SCHEMA_VERSION, "schema.sql")
        # create structure
        with open(schema, "rt") as fin:
            self.executescript(fin.read())


class DatabaseSession:

    def __init__(self, database: Database):
        self._database: Database = database
        self._counter: int = 0
        self._lock: Semaphore = Semaphore()

    def __enter__(self) -> Database:
        with self._lock:
            self._counter += 1
        return self._database

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            self._counter -= 1
            commit = self._counter == 0 and exc_type is None
        if commit:
            self._database.commit()


class Persistency:

    __databases: Dict[str, Database] = {
        "resources": Database("resources")
    }
    __sessions: Dict[str, DatabaseSession] = {
        name: DatabaseSession(db) for name, db in __databases.items()
    }

    @staticmethod
    def database(name: str) -> Database:
        try:
            return Persistency.__databases[name]
        except KeyError:
            raise DatabaseNotFoundException(name)

    @staticmethod
    def session(database: str) -> DatabaseSession:
        try:
            return Persistency.__sessions[database]
        except KeyError:
            raise DatabaseNotFoundException(database)





