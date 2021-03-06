import copy
import dataclasses
import sqlite3
import uuid
from abc import abstractmethod, ABC
from datetime import datetime
from enum import Enum, IntEnum
from threading import Semaphore
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
    def deserialize(cls, value: Any, metadata: Optional[Dict] = None) -> 'Serializable':
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
    def shutdown():
        for resource in KnowledgeBase.__resources.values():
            resource.shutdown()

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


class ResourceType(Enum):
    CLUSTER = "cluster"
    NODE = "node"
    POD = "pod"
    APPLICATION = "application"
    SERVICE = "service"
    IP_ADDRESS = "ip"
    PORT = "port"
    DNS_RECORD = "dns"
    REQUEST = "request"
    RELATION = "relation"

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return self.value


class RelationType(Enum):
    IS_A = "isa"
    BELONGS_TO = "belongsto"

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return self.value


class ResourceID(str, Serializable):

    @staticmethod
    def make(type: ResourceType) -> 'ResourceID':
        assert_type(type, ResourceType)
        s = str(uuid.uuid4())[:8]
        return ResourceID(f"{type.value}:{s}")

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return str(self)

    def serialize(self) -> str:
        return str(self)

    @classmethod
    def deserialize(cls, value: str, metadata: Optional[Dict] = None) -> 'ResourceID':
        return ResourceID(value)


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
    def deserialize(cls, value: dict, metadata: Optional[Dict] = None) -> 'ResourceStatus':
        return ResourceStatus(**value)

    @staticmethod
    def created() -> 'ResourceStatus':
        return ResourceStatus(
            key="created",
            value=Status.SUCCESS
        )


# Resource base


@dataclasses.dataclass
class Resource(Serializable, ABC):
    id: ResourceID = make_field(ResourceID, serialize=False)
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
    def parse(value: dict, metadata: dict) -> dict:
        assert_type(metadata, dict, field="metadata")
        if 'id' not in metadata:
            raise KeyError(f"Missing ID in data loaded from database; Value: {value}")
        # ---
        return {
            "id": ResourceID.deserialize(metadata['id']),
            "name": value['name'],
            "description": value['description'],
            "status": [ResourceStatus.deserialize(s) for s in value['status']],
        }

    @abstractmethod
    def make(self, *args, **kwargs) -> 'Resource':
        pass

    @abstractmethod
    def get_type(self) -> ResourceType:
        pass

    @abstractmethod
    def shutdown(self):
        pass


@dataclasses.dataclass
class PersistentResource(Resource, ABC):

    def __post_init__(self):
        self._lock = Semaphore()

    def shutdown(self):
        self._lock.acquire()
        self.commit(lock=False)
        # lease lock acquired

    def commit(self, lock: bool = True):
        if lock:
            self._lock.acquire()
        # ---
        KnowledgeBase.set(self.id, self)
        data = self.serialize()
        table = self._sql_table()
        with Persistency.session("resources") as cursor:
            # TODO: move this to sqlite utils
            # TODO: this is only supported by SQLite 3.24+, ubuntu 18.04 runs SQLite 3.22
            query = f"INSERT INTO {table}(id, date, enabled, value) " \
                    f"VALUES (?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET value = excluded.value;"
            # query = f"INSERT INTO {table}(id, date, enabled, value) VALUES (?, ?, ?, ?)"
            cursor.execute(query, self.id, now(), True, data)
        # ---
        if lock:
            self._lock.release()

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
            if not field.metadata['serialize']:
                continue
            field_value = getattr(self, field.name)
            data[field.name] = self._serialize_value(field_value)
        print(cbor2.dumps(data))
        return cbor2.dumps(data)

    @abstractmethod
    def _sql_table(self) -> str:
        pass

    def _log_event(self, event: str):
        # TODO: implement this
        pass

    def _log_update(self, field: str, current: Any, new: Any, reason: Optional[str] = None):
        # TODO: implement this
        pass


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

    def get_type(self) -> ResourceType:
        return ResourceType.IP_ADDRESS


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

    def get_type(self) -> ResourceType:
        return ResourceType.PORT


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

    def get_type(self) -> ResourceType:
        return ResourceType.DNS_RECORD


@dataclasses.dataclass
class IPod(PersistentResource, ABC):

    @property
    @abstractmethod
    def node(self) -> 'INode':
        pass

    @property
    @abstractmethod
    def application(self) -> 'INode':
        pass

    def _sql_table(self) -> str:
        return "pods"

    def get_type(self) -> ResourceType:
        return ResourceType.POD


@dataclasses.dataclass
class IApplication(PersistentResource, ABC):

    def _sql_table(self) -> str:
        return "applications"

    def get_type(self) -> ResourceType:
        return ResourceType.APPLICATION


@dataclasses.dataclass
class IService(PersistentResource, ABC):

    @property
    @abstractmethod
    def application(self) -> IApplication:
        pass

    @property
    @abstractmethod
    def port(self) -> IPort:
        pass

    @property
    @abstractmethod
    def dns(self) -> IDNSRecord:
        pass

    def _sql_table(self) -> str:
        return "services"

    def get_type(self) -> ResourceType:
        return ResourceType.SERVICE


@dataclasses.dataclass
class INode(PersistentResource, ABC):

    @property
    @abstractmethod
    def ip_addresses(self) -> List['IIPAddress']:
        pass

    @property
    @abstractmethod
    def cluster(self) -> 'ICluster':
        pass

    @property
    @abstractmethod
    def pods(self) -> List[IPod]:
        pass

    def _sql_table(self) -> str:
        return "nodes"

    def get_type(self) -> ResourceType:
        return ResourceType.NODE


@dataclasses.dataclass
class ICluster(PersistentResource, ABC):

    @property
    @abstractmethod
    def nodes(self) -> List[INode]:
        pass

    def _sql_table(self) -> str:
        return "clusters"

    def get_type(self) -> ResourceType:
        return ResourceType.CLUSTER


@dataclasses.dataclass
class IRequest(PersistentResource, ABC):
    _fragment: Fragment = make_field(Fragment, content=(str, object))

    def _sql_table(self) -> str:
        return "requests"

    def get_type(self) -> ResourceType:
        return ResourceType.REQUEST


@dataclasses.dataclass
class IRelation(PersistentResource, ABC):
    _origin: ResourceID = make_field(ResourceID)
    _relation: RelationType = make_field(RelationType)
    _destination: ResourceID = make_field(ResourceID)
    _value: Dict[str, Any] = make_field(dict, content=(str, object))

    def commit(self, lock: bool = True):
        if lock:
            self._lock.acquire()
        # ---
        KnowledgeBase.set(self.id, self)
        data = self.serialize()
        table = self._sql_table()
        destination = KnowledgeBase.get(self._destination)
        with Persistency.session("resources") as cursor:
            # TODO: this is only supported by SQLite 3.24+, ubuntu 18.04 runs SQLite 3.22
            query = f"INSERT INTO {table}(id, origin, relation, destination, destination_type, " \
                    f"date, value) VALUES (?, ?, ?, ?, ?, ?, ?) " \
                    f"ON CONFLICT (origin, relation, destination) " \
                    f"DO UPDATE SET value = excluded.value;"
            # query = f"INSERT INTO {table}(id, origin, relation, destination, destination_type, date, value) " \
            #         f"VALUES (?, ?, ?, ?, ?, ?)"
            cursor.execute(query, self.id, self._origin, self._relation, self._destination,
                           destination.get_type(), now(), data)
        # ---
        if lock:
            self._lock.release()

    def _sql_table(self) -> str:
        return "relations"

    def get_type(self) -> ResourceType:
        return ResourceType.RELATION
