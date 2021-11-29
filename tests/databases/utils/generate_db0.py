#!/usr/bin/env python3

import os
import sys

# noinspection PyUnresolvedReferences
from utils import INCLUDE, get_path, make_empty, DB

DB_NAME = "db0"
DB_PATH = get_path(DB_NAME)
os.environ.update({
    f"CATTLEMAN_RESOURCES_DB": DB_PATH
})
# clear DB
os.remove(DB_PATH)


# include lib
sys.path.insert(0, INCLUDE)


def main():
    # this is an empty database
    make_empty(DB_NAME)


if __name__ == '__main__':
    main()
