from typing import Optional

import cbor2

from .basics import ResourceID, IPort, Resource, TransportProtocol
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
            id=ResourceID.make("port"),
            name=name,
            description=description,
            _internal=internal,
            _external=external,
            _protocol=protocol
        )
        port.commit()
        return port

    @classmethod
    def deserialize(cls, data: bytes) -> 'Port':
        data = cbor2.loads(data)
        return Port(
            **Resource.parse(data),
            _internal=data['_internal'],
            _external=data['_external'],
            _protocol=TransportProtocol(data['_protocol']),
        )
