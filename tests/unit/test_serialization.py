import importlib
import os
import unittest

import cattleman
from cattleman.types import Cluster, IPAddressType, IPAddress, Node
from cattleman.persistency import Persistency
from cattleman.types.application import Application

os.environ.update({
    f"CATTLEMAN_RESOURCES_DB": ":memory:"
})


class TestSerialization(unittest.TestCase):

    def setUp(self):
        print()
        # noinspection PyTypeChecker
        importlib.reload(cattleman.persistency)

    def test_serialize_cluster(self):
        cluster = Cluster.make("test", description="My test cluster")
        db = Persistency.database("resources")
        row = db.get("clusters", cluster.id)
        # print(row['value'])
        cluster2 = Cluster.deserialize(row['value'])

        print(cluster)
        print(cluster2)

    @unittest.skip
    def test_serialize_ip(self):
        IPAddress("test4", IPAddressType.IPv4, "8.8.8.8", description="My test ip v4")
        IPAddress("test6", IPAddressType.IPv6, "1.1.1.1", description="My test ip v6")

    @unittest.skip
    def test_serialize_node(self):
        cluster = Cluster("test", description="My test cluster")
        ipaddress = IPAddress("test", IPAddressType.IPv4, "8.8.8.8", description="My test ip")
        Node("test", [ipaddress], cluster, description="My test node")

    @unittest.skip
    def test_serialize_application(self):
        Application("test", description="My test application")

    # def test_serialize_cluster(self):
    #     Cluster("test", description="My test cluster")
    #
    # def test_serialize_cluster(self):
    #     Cluster("test", description="My test cluster")
    #
    # def test_serialize_cluster(self):
    #     Cluster("test", description="My test cluster")


if __name__ == '__main__':
    unittest.main()
