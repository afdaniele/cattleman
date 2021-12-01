import importlib
import os
import unittest
from typing import Tuple, TypeVar, Type

import cattleman
from cattleman.types import Cluster, IPAddressType, IPAddress, Node, PersistentResource, \
    TransportProtocol, DNSRecordType
from cattleman.persistency import Persistency
from cattleman.types.application import Application
from cattleman.types.basics import Fragment
from cattleman.types.dns_record import DNSRecord
from cattleman.types.port import Port
from cattleman.types.request import Request
from cattleman.types.service import Service

os.environ.update({
    f"CATTLEMAN_RESOURCES_DB": ":memory:"
})


class TestSerialization(unittest.TestCase):

    def setUp(self):
        print()
        # noinspection PyTypeChecker
        importlib.reload(cattleman.persistency)

    @staticmethod
    def _loop(resource: PersistentResource, klass: Type[PersistentResource]) -> PersistentResource:
        db = Persistency.database("resources")
        row = db.get(resource._sql_table(), resource.id)
        resource2 = klass.deserialize(row['value'])
        return resource2

    def test_serialize_cluster_empty(self):
        cluster = Cluster.make("test", description="My test cluster")
        cluster2 = self._loop(cluster, Cluster)
        self.assertEqual(cluster.serialize(), cluster2.serialize())

    def test_serialize_ip(self):
        ip = IPAddress.make("test", "8.8.8.8", IPAddressType.IPv4, description="My test ip")
        ip2 = self._loop(ip, IPAddress)
        self.assertEqual(ip.serialize(), ip2.serialize())

    def test_serialize_node(self):
        cluster = Cluster.make("test", description="My test cluster")
        ip = IPAddress.make("test", "8.8.8.8", IPAddressType.IPv4, description="My test ip")
        node = Node.make("test", [ip], cluster, description="My test node")
        node2 = self._loop(node, Node)
        self.assertEqual(node.serialize(), node2.serialize())

    def test_serialize_port_tcp(self):
        port = Port.make("test", 80, 8080, TransportProtocol.TCP, description="My test port")
        port2 = self._loop(port, Port)
        self.assertEqual(port.serialize(), port2.serialize())

    def test_serialize_port_udp(self):
        port = Port.make("test", 53, 5353, TransportProtocol.UDP, description="My test port")
        port2 = self._loop(port, Port)
        self.assertEqual(port.serialize(), port2.serialize())

    def test_serialize_dns_record_A(self):
        dns = DNSRecord.make("test", DNSRecordType.A, "1.1.1.1", 60, description="My test dns")
        dns2 = self._loop(dns, DNSRecord)
        self.assertEqual(dns.serialize(), dns2.serialize())

    def test_serialize_dns_record_AAAA(self):
        dns = DNSRecord.make("test", DNSRecordType.AAAA, "1.1.1.1", 60, description="My test dns")
        dns2 = self._loop(dns, DNSRecord)
        self.assertEqual(dns.serialize(), dns2.serialize())

    def test_serialize_dns_record_CNAME(self):
        dns = DNSRecord.make("test", DNSRecordType.CNAME, "abc.com", 60, description="My test dns")
        dns2 = self._loop(dns, DNSRecord)
        self.assertEqual(dns.serialize(), dns2.serialize())

    def test_serialize_application(self):
        application = Application.make("test", description="My test application")
        application2 = self._loop(application, Application)
        self.assertEqual(application.serialize(), application2.serialize())

    def test_serialize_service(self):
        application = Application.make("test", description="My test application")
        port = Port.make("test", 80, 8080, TransportProtocol.TCP, description="My test port")
        dns = DNSRecord.make("test", DNSRecordType.A, "1.1.1.1", 60, description="My test dns")
        # service
        service = Service.make("test", application, port, dns, description="My test service")
        service2 = self._loop(service, Service)
        self.assertEqual(service.serialize(), service2.serialize())

    def test_serialize_request(self):
        fragment = Fragment(
            a=1,
            b="22",
            c=333
        )
        request = Request.make("test", fragment, description="My test request")
        request2 = self._loop(request, Request)
        self.assertEqual(request.serialize(), request2.serialize())


if __name__ == '__main__':
    unittest.main()
