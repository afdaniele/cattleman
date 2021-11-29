import os
import json

import cpk

_SCHEMAS_DIR = os.path.join(os.path.dirname(cpk.__file__), 'schemas')


def _get_schema(schema_fpath: str) -> dict:
    if not os.path.isfile(schema_fpath):
        raise FileNotFoundError(schema_fpath)
    with open(schema_fpath, 'r') as fin:
        return json.load(fin)


def load_schema(name: str, version: str) -> dict:
    schema_fpath = os.path.join(_SCHEMAS_DIR, name, f"v{version.lstrip('v')}.json")
    return _get_schema(schema_fpath)


__all__ = [
    "load_schema"
]
