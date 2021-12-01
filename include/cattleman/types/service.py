from typing import Optional

import cbor2

from .basics import ResourceID, IService, Resource, IPort, IApplication, IDNSRecord, ResourceType
from ..utils.misc import assert_type


class Service(IService):

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
            _application=application.id,
            _port=port.id,
            _dns=dns.id,
        )
        service.commit()
        return service

    @classmethod
    def deserialize(cls, data: bytes) -> 'Service':
        data = cbor2.loads(data)
        return Service(
            **Resource.parse(data),
            _application=ResourceID(data['_application']),
            _port=ResourceID(data['_port']),
            _dns=ResourceID(data['_dns']),
        )
