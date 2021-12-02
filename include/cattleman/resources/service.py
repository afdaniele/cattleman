from typing import Optional, Dict

import cbor2

from ..relations import RelationsManager
from ..types import ResourceID, IService, Resource, IPort, IApplication, IDNSRecord, ResourceType, \
    RelationType
from ..utils.misc import assert_type


class Service(IService):

    @property
    def application(self) -> IApplication:
        # TODO
        return None

    @property
    def dns(self) -> IDNSRecord:
        # TODO
        return None

    @property
    def port(self) -> IPort:
        # TODO
        return None

    @staticmethod
    def make(name: str, application: IApplication, port: IPort, dns: IDNSRecord, *, description: Optional[str] = None) -> 'Service':
        # verify types
        assert_type(name, str)
        assert_type(application, IApplication)
        assert_type(port, IPort)
        assert_type(dns, IDNSRecord)
        assert_type(description, str, nullable=True)
        # ---
        service = Service(
            id=ResourceID.make(ResourceType.SERVICE),
            name=name,
            description=description,
        )
        service.commit()
        # create relations
        # service -> application
        RelationsManager.create(service, RelationType.BELONGS_TO, application)
        # service -> port
        RelationsManager.create(service, RelationType.BELONGS_TO, port)
        # service -> dns
        RelationsManager.create(service, RelationType.BELONGS_TO, dns)
        # ---
        return service

    @classmethod
    def deserialize(cls, value: bytes, metadata: Optional[Dict] = None) -> 'Service':
        data = cbor2.loads(value)
        return Service(
            **Resource.parse(data, metadata),
        )
