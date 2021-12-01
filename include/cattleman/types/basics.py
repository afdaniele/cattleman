import copy
import dataclasses
import sqlite3
import uuid
from abc import abstractmethod, ABC
from datetime import datetime
from enum import Enum, IntEnum
from typing import List, Dict, Any, Optional

import cbor2

from cattleman.constants import NoneType, UNDEFINED
from cattleman.exceptions import ResourceNotFoundException, MissingParameterException
from cattleman.persistency import Persistency
from cattleman.utils.dataclasses import make_field
from cattleman.utils.misc import assert_type, now

Arguments = List[str]


class Serializable(ABC):

    @abstractmethod
    def serialize(self) -> bytes:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data) -> 'Serializable':
        pass


class KnowledgeBase:

    __resources: Dict[str, 'Resource'] = {}

    @staticmethod
    def get(id: 'ResourceID'):
        id = id if isinstance(id, str) else str(id)
        try:
            KnowledgeBase.__resources[id]
        except KeyError:
            raise ResourceNotFoundException(id)

    @staticmethod
    def set(id: 'ResourceID', resource: 'Resource'):
        KnowledgeBase.__resources[id] = resource

    @staticmethod
    def clear():
        KnowledgeBase.__resources.clear()


# Volatile objects


class IPAddressType(IntEnum):
    IPv4 = 4
    IPv6 = 6


class DNSRecordType(Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"


class TransportProtocol(Enum):
    TCP = "TCP"
    UDP = "UDP"


class Status(Enum):
    UNKNOWN = "unknown"
    FAILURE = "failure"
    SUCCESS = "success"


class ResourceID(str, Serializable):

    @staticmethod
    def make(category: str) -> 'ResourceID':
        s = str(uuid.uuid4())[:8]
        return ResourceID(f"{category}:{s}")

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return str(self)

    def serialize(self) -> str:
        return str(self)

    @classmethod
    def deserialize(cls, data: str) -> 'ResourceID':
        return ResourceID(data)


class Fragment(dict):
    pass


@dataclasses.dataclass
class ResourceStatus(Serializable):
    key: str = make_field(str)
    value: Status = make_field(Status)
    description: Optional[str] = make_field((str, NoneType), default=None)
    reason: Optional[str] = make_field(ResourceID, default=None)
    date: datetime = make_field(datetime, default=now)

    def serialize(self) -> dict:
        return copy.copy(self.__dict__)

    @classmethod
    def deserialize(cls, data) -> 'ResourceStatus':
        return ResourceStatus(**data)

    @staticmethod
    def created() -> 'ResourceStatus':
        return ResourceStatus(
            key="created",
            value=Status.SUCCESS
        )


# Resource base


@dataclasses.dataclass
class Resource(Serializable, ABC):
    id: ResourceID = make_field(ResourceID)
    name: str = make_field(str)
    description: Optional[str] = make_field((str, NoneType))
    status: List[ResourceStatus] = make_field(list,
                                              content=ResourceStatus,
                                              factory=lambda: [ResourceStatus.created()])

    def __post_init__(self):
        for field in dataclasses.fields(self):
            name = field.name
            metadata = field.metadata
            vtype = metadata['type']
            value = getattr(self, name)
            # required
            if value is UNDEFINED:
                raise MissingParameterException(type(self), "__init__", name)
            # check types
            assert_type(value, vtype, field=name)
            # iterables
            if type(value) in [list, set, tuple]:
                ctype = metadata['content']
                for i, elem in enumerate(value):
                    assert_type(elem, ctype, field=f"{field}[{i}]")
            # dictionaries
            if isinstance(value, dict):
                ktype, vtype = metadata['content']
                for kelem, velem in value.items():
                    assert_type(kelem, ktype, field=f"key {kelem} in {field}")
                    assert_type(velem, vtype, field=f"{field}[{kelem}]")

    @staticmethod
    def parse(data: dict) -> dict:
        return {
            "id": ResourceID.deserialize(data['id']),
            "name": data['name'],
            "description": data['description'],
            "status": [ResourceStatus.deserialize(s) for s in data['status']],
        }

    @abstractmethod
    def make(self, *args, **kwargs) -> 'Resource':
        pass


@dataclasses.dataclass
class PersistentResource(Resource, ABC):

    @abstractmethod
    def _sql_table(self) -> str:
        pass

    def _log_event(self, event: str):
        # TODO: implement this
        pass

    def _log_update(self, field: str, current: Any, new: Any, reason: Optional[str] = None):
        # TODO: implement this
        pass

    def commit(self):
        KnowledgeBase.set(self.id, self)
        data = self.serialize()
        table = self._sql_table()
        with Persistency.session("resources") as cursor:
            # TODO: this is only supported by SQLite 3.24+, ubuntu 18.04 runs SQLite 3.22
            # query = f"INSERT INTO {table}(id, date, enabled, value) " \
            #         f"VALUES (?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET value = excluded.value;"
            query = f"INSERT INTO {table}(id, date, enabled, value) VALUES (?, ?, ?, ?)"
            cursor.execute(query, self.id, now(), True, data)

    @staticmethod
    def _serialize_value(value):
        # unpack enums
        if isinstance(value, Enum):
            value = value.value
        # serializable elements
        if isinstance(value, Serializable):
            value = value.serialize()
        # iterables
        if isinstance(value, (list, set, tuple)):
            iterable = type(value)
            value = iterable([PersistentResource._serialize_value(v) for v in value])
        # dictionary
        if isinstance(value, dict):
            value = {k: PersistentResource._serialize_value(v) for k, v in value.items()}
        # ---
        return value

    def serialize(self) -> bytes:
        data = {}
        for field in dataclasses.fields(self):
            field_value = getattr(self, field.name)
            data[field.name] = self._serialize_value(field_value)
        return cbor2.dumps(data)


# Persistent resources


@dataclasses.dataclass
class IIPAddress(PersistentResource, ABC):
    _type: IPAddressType = make_field(IPAddressType)
    _value: str = make_field(str)

    @property
    def type(self) -> IPAddressType:
        return self._type

    @property
    def value(self) -> str:
        return self._value

    @type.setter
    def type(self, value: IPAddressType):
        assert_type(value, IPAddressType)
        self._type = value
        self.commit()

    @value.setter
    def value(self, value: str):
        assert_type(value, str)
        self._value = value
        self.commit()

    def _sql_table(self) -> str:
        return "ip_addresses"


@dataclasses.dataclass
class IPort(PersistentResource, ABC):
    _internal: int = make_field(int)
    _external: int = make_field(int)
    _protocol: TransportProtocol = make_field(TransportProtocol)

    @property
    def internal(self) -> int:
        return self._internal

    @property
    def external(self) -> int:
        return self._external

    @property
    def protocol(self) -> TransportProtocol:
        return self._protocol

    @internal.setter
    def internal(self, value: int):
        assert_type(value, int)
        self._internal = value
        self.commit()

    @external.setter
    def external(self, value: int):
        assert_type(value, int)
        self._external = value
        self.commit()

    @protocol.setter
    def protocol(self, value: TransportProtocol):
        assert_type(value, TransportProtocol)
        self._protocol = value
        self.commit()

    def _sql_table(self) -> str:
        return "ports"


@dataclasses.dataclass
class IDNSRecord(PersistentResource, ABC):
    _type: DNSRecordType = make_field(DNSRecordType)
    _value: str = make_field(str)
    _ttl: int = make_field(int, default=30)

    @property
    def type(self) -> DNSRecordType:
        return self._type

    @property
    def value(self) -> str:
        return self._value

    @property
    def ttl(self) -> int:
        return self._ttl

    @type.setter
    def type(self, value: DNSRecordType):
        assert_type(value, DNSRecordType)
        self._type = value
        self.commit()

    @value.setter
    def value(self, value: str):
        assert_type(value, str)
        self._value = value
        self.commit()

    @ttl.setter
    def ttl(self, value: int):
        assert_type(value, int)
        self._ttl = value
        self.commit()

    def _sql_table(self) -> str:
        return "dns_records"


@dataclasses.dataclass
class IPod(PersistentResource, ABC):
    _node: ResourceID = make_field(ResourceID)
    _application: ResourceID = make_field(ResourceID)

    @property
    def node(self) -> 'INode':
        return KnowledgeBase.get(self._node)

    @property
    def application(self) -> 'INode':
        return KnowledgeBase.get(self._application)

    def _sql_table(self) -> str:
        return "pods"


@dataclasses.dataclass
class IApplication(PersistentResource, ABC):

    def _sql_table(self) -> str:
        return "applications"


@dataclasses.dataclass
class IService(PersistentResource, ABC):
    _application: ResourceID = make_field(ResourceID)
    _port: ResourceID = make_field(ResourceID)
    _dns: ResourceID = make_field(ResourceID)

    @property
    def application(self) -> IApplication:
        return KnowledgeBase.get(self._application)

    @property
    def port(self) -> IPort:
        return KnowledgeBase.get(self._port)

    @property
    def dns(self) -> IDNSRecord:
        return KnowledgeBase.get(self._dns)

    def _sql_table(self) -> str:
        return "services"


@dataclasses.dataclass
class INode(PersistentResource, ABC):
    _ip_addresses: List[ResourceID] = make_field(list, content=ResourceID)
    _cluster: ResourceID = make_field(ResourceID)
    _pods: List[ResourceID] = make_field(list, content=ResourceID, factory=list)

    @property
    def ip_addresses(self) -> List['IIPAddress']:
        return [
            KnowledgeBase.get(ip) for ip in self._ip_addresses
        ]

    @property
    def cluster(self) -> 'ICluster':
        return KnowledgeBase.get(self._cluster)

    @property
    def pods(self) -> List[IPod]:
        return [
            KnowledgeBase.get(p) for p in self._pods
        ]

    def _sql_table(self) -> str:
        return "nodes"


@dataclasses.dataclass
class ICluster(PersistentResource, ABC):
    _nodes: List[ResourceID] = make_field(list, content=ResourceID, default=list)

    @property
    def nodes(self) -> List[INode]:
        return [
            KnowledgeBase.get(n) for n in self._nodes
        ]

    def _sql_table(self) -> str:
        return "clusters"


@dataclasses.dataclass
class IRequest(PersistentResource, ABC):
    _fragment: Fragment = make_field(Fragment, content=(str, object))

    def _sql_table(self) -> str:
        return "requests"
