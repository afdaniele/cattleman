import copy
import sqlite3
import uuid
from abc import abstractmethod, ABC
from builtins import setattr
from datetime import datetime
from enum import Enum, IntEnum
from inspect import isclass
from typing import List, Dict, Union, Any, Optional, TypeVar

import cbor2
import dataclasses

from cattleman.constants import REQUIRED
from cattleman.exceptions import ResourceNotFoundException, TypeMismatchException
from cattleman.persistency import Persistency
from cattleman.utils.misc import assert_type, now, typing_type, typing_content_type

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


class DNSType(Enum):
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

    def serialize(self):
        return str(self)

    @classmethod
    def deserialize(cls, data: str):
        return ResourceID(data)


@dataclasses.dataclass
class ResourceStatus(Serializable):
    key: str
    value: Status
    description: Optional[str] = None
    reason: Optional[str] = None
    date: datetime = dataclasses.field(default_factory=now)

    def serialize(self):
        return copy.copy(self.__dict__)

    @classmethod
    def deserialize(cls, data):
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
    id: ResourceID
    name: str
    description: Optional[str]
    status: List[ResourceStatus] = dataclasses.field(
        default_factory=lambda: [ResourceStatus.created()]
    )

    # def __post_init__(self):
    #     assert_type(self.id, ResourceID)
    #     assert_type(self.name, str)
    #     assert_type(self.description, str, nullable=True)
    #     assert_type(self.status, list)

    def __post_init__(self):
        for field in dataclasses.fields(self):
            name = field.name
            type = field.type
            value = getattr(self, name)
            # check types
            assert_type(value, type, field=name)

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

    @staticmethod
    def _deserialize_value(value: Any, type: type):
        try:
            assert_type(value, type)
            return value
        except TypeMismatchException:
            pass
        # iterables
        if typing_type(type) in (list, set, tuple):
            iterable = typing_type(type)
            content_type = typing_content_type(type)
            return iterable([PersistentResource._deserialize_value(v, content_type) for v in value])

        # if not isclass(type):
        #     return value
        print(type)
        # pack enums
        if issubclass(type, Enum):
            value = type(value)
        # serializable elements
        if issubclass(type, Serializable) and not isinstance(value, type):
            value = type.deserialize(value)
        # # dictionary
        # if isinstance(value, dict):
        #     value = {k: PersistentResource._serialize_value(v) for k, v in value.items()}
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
        # print(super())
        # print(cls.__base__)
        data = cbor2.loads(data)

        print(data)

        values = {}
        for field in dataclasses.fields(cls):
            print(field)
            field_value = data[field.name]
            values[field.name] = PersistentResource._deserialize_value(field_value, field.type)
            # setattr(obj, field.name, obj._deserialize_value(field_value, field.type))

        print(values)

        obj = cls(**values)
        return obj

        return cls(**data)
        return cls._from_dict(cbor2.loads(data))


# Persistent resources


@dataclasses.dataclass
class IIPAddress(PersistentResource, ABC):
    _type: IPAddressType = REQUIRED
    _value: str = REQUIRED

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
    _internal: int = REQUIRED
    _external: int = REQUIRED
    _protocol: TransportProtocol = REQUIRED

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
    _type: DNSType = REQUIRED
    _value: str = REQUIRED
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
    _node: ResourceID = REQUIRED

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
    _application: ResourceID = REQUIRED
    _port: ResourceID = REQUIRED
    _dns: ResourceID = REQUIRED

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
    _ip_addresses: List[ResourceID] = REQUIRED
    _cluster: ResourceID = REQUIRED
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
    _fragment: Fragment = REQUIRED
    _status: Status = REQUIRED

    def __post_init__(self):
        assert_type(self._fragment, dict)
        assert_type(self._status, Status)
        super(IRequest, self).__post_init__()

    def _sql_table(self) -> str:
        return "requests"
