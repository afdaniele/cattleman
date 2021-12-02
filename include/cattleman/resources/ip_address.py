from typing import Optional, Dict

import cbor2

from ..types import ResourceID, IIPAddress, IPAddressType, Resource, ResourceType
from ..utils.misc import assert_type


class IPAddress(IIPAddress):

    @staticmethod
    def make(name: str, value: str, type: IPAddressType, *,
             description: Optional[str] = None) -> 'IPAddress':
        # verify types
        assert_type(name, str)
        assert_type(value, str)
        assert_type(type, IPAddressType)
        assert_type(description, str, nullable=True)
        # ---
        ip = IPAddress(
            id=ResourceID.make(ResourceType.IP_ADDRESS),
            name=name,
            description=description,
            _type=type,
            _value=value
        )
        ip.commit()
        return ip

    @classmethod
    def deserialize(cls, value: bytes, metadata: Optional[Dict] = None) -> 'IPAddress':
        data = cbor2.loads(value)
        return IPAddress(
            **Resource.parse(data, metadata),
            _value=data['_value'],
            _type=IPAddressType(data['_type']),
        )
