import copy
import sqlite3
import uuid
from abc import abstractmethod, ABC
from datetime import datetime
from enum import Enum, IntEnum
from typing import List, Dict, Union, Any, Optional

import cbor2
import dataclasses

from cattleman.exceptions import ResourceNotFoundException
from cattleman.persistency import Persistency
from cattleman.utils.misc import assert_type, now

Arguments = List[str]


Fragment = Dict


class Serializable(ABC):

    @abstractmethod
    def serialize(self):
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data):
        pass


class KnowledgeBase:

    __resources: Dict[str, 'Resource'] = {}

    @staticmethod
    def get(resource_id: Union[str, 'ResourceID']):
        resource_id = resource_id if isinstance(resource_id, str) else str(resource_id)
        try:
            KnowledgeBase.__resources[resource_id]
        except KeyError:
            raise ResourceNotFoundException(resource_id)

    @staticmethod
    def set(resource_id: Union[str, 'ResourceID'], resource: 'Resource'):
        resource_id = resource_id.value if isinstance(resource_id, ResourceID) else str(resource_id)
        KnowledgeBase.__resources[resource_id] = resource

    @staticmethod
    def clear():
        KnowledgeBase.__resources.clear()


# Volatile objects


class IPAddressType(IntEnum):
    IPv4 = 4
    IPv6 = 6


class DNSType(Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"


class TransportProtocol(Enum):
    TCP = "TCP"
    UDP = "UDP"


class Status(Enum):
    SETUP = "setup"
    WAITING = "waiting"
    ERROR = "error"
    TIMEOUT = "timeout"
    READY = "ready"
    TERMINATED = "terminated"


@dataclasses.dataclass
class ResourceStatus(Serializable):
    description: str
    reason: str
    value: Status
    date: datetime = dataclasses.field(default_factory=now)

    def serialize(self):
        return copy.copy(self.__dict__)

    @classmethod
    def deserialize(cls, data):
        return ResourceStatus(**data)


@dataclasses.dataclass
class ResourceID(Serializable):
    value: str

    @staticmethod
    def make(category: str) -> 'ResourceID':
        s = str(uuid.uuid4())[:8]
        return ResourceID(f"{category}:{s}")

    def __str__(self):
        return self.value

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return self.value

    def serialize(self):
        return self.value

    @classmethod
    def deserialize(cls, data):
        return ResourceID(data)


# Resource base


@dataclasses.dataclass
class Resource:
    id: ResourceID
    name: str
    description: str
    status: List[Status]

    def __post_init__(self):
        assert_type(self.id, ResourceID)
        assert_type(self.name, str)
        assert_type(self.description, str, nullable=True)
        assert_type(self.status, list)

    @staticmethod
    def defaults() -> dict:

        return {
            "status": []
        }


@dataclasses.dataclass
class PersistentResource(Resource):

    @abstractmethod
    def _sql_table(self) -> str:
        pass

    # @classmethod
    # @abstractmethod
    # def _from_dict(cls, data: dict) -> 'PersistentResource':
    #     pass

    @classmethod
    def _from_dict(cls, data: dict) -> 'Resource':
        return super(cls).__init__(**data)

    def _log_event(self, event: str):
        # TODO: implement this
        pass

    def _log_update(self, field: str, current: Any, new: Any, reason: Optional[str] = None):
        # TODO: implement this
        pass

    def _commit(self):
        KnowledgeBase.set(self.id.value, self)
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
        # ---
        return value

    def serialize(self) -> bytes:
        data = {}
        for field in dataclasses.fields(self):
            field_value = getattr(self, field.name)
            data[field.name] = self._serialize_value(field_value)
        return cbor2.dumps(data)

    @classmethod
    def deserialize(cls, data: bytes) -> Resource:
        print(super())
        print(cls.__base__)
        data = cbor2.loads(data)
        obj = cls(**data)

        return cls(**data)
        return cls._from_dict(cbor2.loads(data))


# Persistent resources


@dataclasses.dataclass
class IIPAddress(PersistentResource, ABC):
    _type: IPAddressType
    _value: str

    def __post_init__(self):
        assert_type(self._type, IPAddressType)
        assert_type(self._value, str)
        super(IIPAddress, self).__post_init__()

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
        self._commit()

    @value.setter
    def value(self, value: str):
        assert_type(value, str)
        self._value = value
        self._commit()

    def _sql_table(self) -> str:
        return "ip_addresses"


@dataclasses.dataclass
class IPort(PersistentResource, ABC):
    _internal: int
    _external: int
    _protocol: TransportProtocol

    def __post_init__(self):
        assert_type(self._internal, int)
        assert_type(self._external, int)
        assert_type(self._protocol, TransportProtocol)
        super(IPort, self).__post_init__()

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
        self._commit()

    @external.setter
    def external(self, value: int):
        assert_type(value, int)
        self._external = value
        self._commit()

    @protocol.setter
    def protocol(self, value: TransportProtocol):
        assert_type(value, TransportProtocol)
        self._protocol = value
        self._commit()

    def _sql_table(self) -> str:
        return "ports"


@dataclasses.dataclass
class IDNSRecord(PersistentResource, ABC):
    _type: DNSType
    _value: str
    _ttl: int = 30

    def __post_init__(self):
        assert_type(self._type, DNSType)
        assert_type(self._value, str)
        assert_type(self._ttl, int)
        super(IDNSRecord, self).__post_init__()

    @property
    def type(self) -> DNSType:
        return self._type

    @property
    def value(self) -> str:
        return self._value

    @property
    def ttl(self) -> int:
        return self._ttl

    @type.setter
    def type(self, value: DNSType):
        assert_type(value, DNSType)
        self._type = value
        self._commit()

    @value.setter
    def value(self, value: str):
        assert_type(value, str)
        self._value = value
        self._commit()

    @ttl.setter
    def ttl(self, value: int):
        assert_type(value, int)
        self._ttl = value
        self._commit()

    def _sql_table(self) -> str:
        return "dns_records"


@dataclasses.dataclass
class IPod(PersistentResource, ABC):
    _node: ResourceID

    def __post_init__(self):
        assert_type(self._node, ResourceID)
        super(IPod, self).__post_init__()

    @property
    def node(self) -> 'INode':
        return KnowledgeBase.get(self._node)

    def _sql_table(self) -> str:
        return "pods"


@dataclasses.dataclass
class IApplication(PersistentResource, ABC):
    _pods: List[ResourceID] = dataclasses.field(default_factory=list)
    _services: List[ResourceID] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        assert_type(self._pods, list)
        assert_type(self._services, list)
        super(IApplication, self).__post_init__()

    @property
    def pods(self) -> List[IPod]:
        return [
            KnowledgeBase.get(p) for p in self._pods
        ]

    @property
    def services(self) -> List['IService']:
        return [
            KnowledgeBase.get(s) for s in self._services
        ]

    def _sql_table(self) -> str:
        return "applications"


@dataclasses.dataclass
class IService(PersistentResource, ABC):
    _application: ResourceID
    _port: ResourceID
    _dns: ResourceID

    def __post_init__(self):
        assert_type(self._application, ResourceID)
        assert_type(self._port, ResourceID)
        assert_type(self._dns, ResourceID)
        super(IService, self).__post_init__()

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
    _ip_addresses: List[ResourceID]
    _cluster: ResourceID
    _pods: List[ResourceID] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        assert_type(self._ip_addresses, list)
        assert_type(self._cluster, ResourceID)
        assert_type(self._pods, list)
        super(INode, self).__post_init__()

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
    _nodes: List[ResourceID] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        assert_type(self._nodes, list)
        super(ICluster, self).__post_init__()

    @property
    def nodes(self) -> List[INode]:
        return [
            KnowledgeBase.get(n) for n in self._nodes
        ]

    def _sql_table(self) -> str:
        return "clusters"


@dataclasses.dataclass
class IRequest(PersistentResource, ABC):
    _fragment: Fragment
    _status: Status

    def __post_init__(self):
        assert_type(self._fragment, dict)
        assert_type(self._status, Status)
        super(IRequest, self).__post_init__()

    def _sql_table(self) -> str:
        return "requests"
