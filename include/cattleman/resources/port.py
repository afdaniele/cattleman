from typing import Optional, Dict

import cbor2

from ..types import ResourceID, IPort, Resource, TransportProtocol, ResourceType
from ..utils.misc import assert_type


class Port(IPort):

    @staticmethod
    def make(name: str, internal: int, external: int, protocol: TransportProtocol, *,
             description: Optional[str] = None) -> 'Port':
        # verify types
        assert_type(name, str)
        assert_type(internal, int)
        assert_type(external, int)
        assert_type(protocol, TransportProtocol)
        assert_type(description, str, nullable=True)
        # ---
        port = Port(
            id=ResourceID.make(ResourceType.PORT),
            name=name,
            description=description,
            _internal=internal,
            _external=external,
            _protocol=protocol
        )
        port.commit()
        return port

    @classmethod
    def deserialize(cls, value: bytes, metadata: Optional[Dict] = None) -> 'Port':
        data = cbor2.loads(value)
        return Port(
            **Resource.parse(data, metadata),
            _internal=data['_internal'],
            _external=data['_external'],
            _protocol=TransportProtocol(data['_protocol']),
        )
