#!/usr/bin/env python3

import os
import sys

# noinspection PyUnresolvedReferences
from utils import INCLUDE, get_path, make_empty, DB

DB_NAME = "db1"
DB_PATH = get_path(DB_NAME)
os.environ.update({
    f"CATTLEMAN_RESOURCES_DB": DB_PATH
})
# clear DB
make_empty(DB_NAME)


# include lib
sys.path.insert(0, INCLUDE)
from cattleman.types import Cluster, IPAddressType, IPAddress, Node
from cattleman.persistency import Persistency


def main():
    # create 1x cluster, 1x IP address and 1x Node
    with Persistency.session("resources"):
        cluster = Cluster("local", description="My local cluster")
        # create node
        ip = IPAddress("ip0", IPAddressType.IPv4, "8.8.8.8")
        node = Node("node0", ip, cluster, description="My local node")


if __name__ == '__main__':
    main()
