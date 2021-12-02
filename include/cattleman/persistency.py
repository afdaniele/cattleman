import os
import logging
import sqlite3
from sqlite3 import Row, Connection
from threading import Semaphore
from typing import Dict, Iterable, Any, List, Type, Optional

from cattleman.logger import cmlogger
from cattleman.constants import DATABASES_DIR, DATABASE_SCHEMA_VERSION
from cattleman.exceptions import DatabaseNotFoundException
from cattleman.utils.atomic import AtomicSession
from cattleman import cmlogger

ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)))

logging.basicConfig()


class Database:

    def __init__(self, name: str):
        os.makedirs(DATABASES_DIR, exist_ok=True)
        os.chmod(DATABASES_DIR, mode=0o700)
        # prepare logger
        self._logger = logging.getLogger(f"DB:{name}")
        self._logger.setLevel(logging.INFO)
        # get path to storage
        self._db_fpath = os.path.join(DATABASES_DIR, f"{name}.db")
        self._db_fpath = os.environ.get(f"CATTLEMAN_{name.upper()}_DB", self._db_fpath)
        self._db: Optional[Connection] = None
        self._lock = Semaphore()

    @property
    def opened(self) -> bool:
        return self._db is not None

    def open(self):
        self._logger.info(f"Opened on {self._db_fpath}")
        self._db = sqlite3.connect(self._db_fpath)
        self._db.row_factory = sqlite3.Row
        self._ensure_structure()

    def get(self, table: str, id: str) -> Row:
        return self.execute(f"SELECT * FROM {table} WHERE id=?;", id).fetchone()

    def all(self, table: str) -> List[Row]:
        return self.execute(f"SELECT * FROM {table};").fetchall()

    def set(self, table: str, id: Any, data: bytes):
        # TODO: implement this
        pass

    def fetchall(self, sql: str, *args) -> List[Row]:
        return self.execute(sql, *args).fetchall()

    def execute(self, sql: str, *args):
        with AtomicSession():
            with self._lock:
                return self._db.execute(sql, args)

    def executemany(self, sql: str, seq_of_parameters: Iterable[Iterable]):
        with AtomicSession():
            with self._lock:
                return self._db.executemany(sql, seq_of_parameters)

    def executescript(self, sql_script: str):
        with AtomicSession():
            with self._lock:
                return self._db.executescript(sql_script)

    def commit(self):
        with AtomicSession():
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
        if not self._database.opened:
            self._database.open()
        # ---
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
        "resources": Database("resources"),
        "events": Database("events"),
    }
    __sessions: Dict[str, DatabaseSession] = {
        name: DatabaseSession(db) for name, db in __databases.items()
    }

    @staticmethod
    def database(name: str) -> Database:
        try:
            database = Persistency.__databases[name]
            if not database.opened:
                database.open()
            return database
        except KeyError:
            raise DatabaseNotFoundException(name)

    @staticmethod
    def session(database: str) -> DatabaseSession:
        try:
            return Persistency.__sessions[database]
        except KeyError:
            raise DatabaseNotFoundException(database)

    @staticmethod
    def load_from_disk():
        Persistency._load_resources_from_disk()

    @staticmethod
    def _load_resources_from_disk():
        from cattleman.types import KnowledgeBase, PersistentResource
        from cattleman.types import Cluster
        from cattleman.types import Node
        from cattleman.types import IPAddress
        from cattleman.types import DNSRecord
        from cattleman.types import Application
        from cattleman.types import Pod
        from cattleman.types import Port
        from cattleman.types import Service
        from cattleman.types import Request
        # ---
        resources: Dict[str, Type[PersistentResource]] = {
            "clusters": Cluster,
            "nodes": Node,
            "ip_addresses": IPAddress,
            "dns_records": DNSRecord,
            "applications": Application,
            "pods": Pod,
            "ports": Port,
            "services": Service,
            "requests": Request,
        }
        database = Persistency.database("resources")
        # load resources
        total = 0
        cmlogger.info("Loading resources from disk...")
        for table, klass in resources.items():
            per_table = 0
            for res in database.all(table):
                id = res["id"]
                value = res["value"]
                resource = klass.deserialize(value)
                KnowledgeBase.set(id, resource)
                # collect stats
                per_table += 1
                total += 1
            cmlogger.debug(f" > Loaded {per_table} resources of type {table} from disk.")
        cmlogger.info(f"< Loaded {total} resources in total from disk.")
