import importlib
import os
import unittest

import cattleman
from cattleman.persistency import Persistency
from cattleman.relations import RelationsManager
from cattleman.resources import Application, IPAddress, Node, Pod, Cluster, Service, Port, \
    DNSRecord
from cattleman.types import IPAddressType, RelationType, TransportProtocol, DNSRecordType

os.environ.update({
    f"CATTLEMAN_RESOURCES_DB": ":memory:"
})


# noinspection DuplicatedCode
class TestSerialization(unittest.TestCase):

    def setUp(self):
        print()
        # noinspection PyTypeChecker
        importlib.reload(cattleman.persistency)

    def test_serialize_application(self):
        # make sure the database is clean
        relations = RelationsManager.get()
        self.assertEqual(len(relations), 0)
        # application
        Application.make("test", description="My test application")
        # make sure no relations ended up inside the database
        relations = RelationsManager.get()
        self.assertEqual(len(relations), 0)

    def test_serialize_pod(self):
        # make sure the database is clean
        relations = RelationsManager.get()
        self.assertEqual(len(relations), 0)
        # application
        with Persistency.session("resources"):
            application = Application.make("test", description="My test application")
            # cluster - produces NO relations
            cluster = Cluster.make("test", description="My test cluster")
            # ip - produces NO relations
            ip = IPAddress.make("test", "8.8.8.8", IPAddressType.IPv4, description="My test ip")
            # node - produces 2 relations
            node = Node.make("test", [ip], cluster, description="My test node")
            # pod - produces 2 relations
            pod = Pod.make("test", node, application, description="My test pod")
            # (pod -> node) - duplicate, produces NO relations
            RelationsManager.create(pod, RelationType.BELONGS_TO, node)
            # (pod -> application) - duplicate, produces NO relations
            RelationsManager.create(pod, RelationType.BELONGS_TO, application)
        # make sure the correct number of relations ended up inside the database
        relations = RelationsManager.get()
        self.assertEqual(len(relations), 4)

    def test_serialize_pod_with_extra(self):
        # make sure the database is clean
        relations = RelationsManager.get()
        self.assertEqual(len(relations), 0)
        # application
        with Persistency.session("resources"):
            application = Application.make("test", description="My test application")
            # cluster - produces NO relations
            cluster = Cluster.make("test", description="My test cluster")
            # ip - produces NO relations
            ip = IPAddress.make("test", "8.8.8.8", IPAddressType.IPv4, description="My test ip")
            # node - produces 2 relations
            node = Node.make("test", [ip], cluster, description="My test node")
            # pod - produces 2 relations
            pod = Pod.make("test", node, application, description="My test pod")
            # pod -> cluster (though illegal) produces 1 extra relations
            RelationsManager.create(pod, RelationType.BELONGS_TO, cluster)
        # make sure the correct number of relations ended up inside the database
        relations = RelationsManager.get()
        self.assertEqual(len(relations), 5)

    def test_serialize_node_multiple_ips(self):
        # make sure the database is clean
        relations = RelationsManager.get()
        self.assertEqual(len(relations), 0)
        # application
        with Persistency.session("resources"):
            # cluster - produces NO relations
            cluster = Cluster.make("test", description="My test cluster")
            # ip - produces NO relations
            ip1 = IPAddress.make("test", "8.8.8.8", IPAddressType.IPv4, description="My test ip 1")
            ip2 = IPAddress.make("test", "4.4.4.4", IPAddressType.IPv4, description="My test ip 2")
            # node - produces 3 relations (2xIP, 1xCluster)
            Node.make("test", [ip1, ip2], cluster, description="My test node")
        # make sure the correct number of relations ended up inside the database
        relations = RelationsManager.get()
        self.assertEqual(len(relations), 3)

    def test_serialize_service(self):
        # make sure the database is clean
        relations = RelationsManager.get()
        self.assertEqual(len(relations), 0)
        # application
        with Persistency.session("resources"):
            application = Application.make("test", description="My test application")
            # port - produces NO relations
            port = Port.make("test", 80, 8080, TransportProtocol.TCP, description="My test port")
            # dns - produces NO relations
            dns = DNSRecord.make("test", DNSRecordType.A, "1.1.1.1", 60, description="My test dns")
            # service - produces 3 relations
            Service.make("test", application, port, dns, description="My test service")
        # make sure the correct number of relations ended up inside the database
        relations = RelationsManager.get()
        self.assertEqual(len(relations), 3)


if __name__ == '__main__':
    unittest.main()
