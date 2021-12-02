import sqlite3
from typing import Iterable

import semantic_version

UPSERT_SUPPORTED_SINCE = semantic_version.Version("3.24.0")


def upsert_query(table: str, columns: Iterable[str], conflict: Iterable[str], update: str) -> str:
    placeholders = ", ".join(["?"] * len(columns))
    columns = ", ".join(columns)
    conflict = ", ".join(conflict or [])
    # ---
    sqlite_version = semantic_version.Version(sqlite3.sqlite_version)
    if sqlite_version >= UPSERT_SUPPORTED_SINCE:
        query = f"INSERT INTO {table}({columns}) VALUES ({placeholders}) " \
                f"ON CONFLICT ({conflict}) " \
                f"DO UPDATE SET {update} = excluded.{update};"
    else:
        # TODO: prepare a more complex query for older sqlite and switch based on sqlite version
        # query = f"INSERT INTO relations({RELATIONS_ROW_K}) VALUES ({RELATIONS_ROW_V})"
        query = None
    return query
