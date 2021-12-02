from typing import Optional, Dict

import cbor2

from ..types import ResourceID, IDNSRecord, Resource, DNSRecordType, ResourceType
from ..utils.misc import assert_type


class DNSRecord(IDNSRecord):

    @staticmethod
    def make(name: str, type: DNSRecordType, value: str, ttl: int, *,
             description: Optional[str] = None) -> 'DNSRecord':
        # verify types
        assert_type(name, str)
        assert_type(type, DNSRecordType)
        assert_type(value, str)
        assert_type(ttl, int)
        assert_type(description, str, nullable=True)
        # ---
        dns_record = DNSRecord(
            id=ResourceID.make(ResourceType.DNS_RECORD),
            name=name,
            description=description,
            _type=type,
            _value=value,
            _ttl=ttl
        )
        dns_record.commit()
        return dns_record

    @classmethod
    def deserialize(cls, value: bytes, metadata: Optional[Dict] = None) -> 'DNSRecord':
        data = cbor2.loads(value)
        return DNSRecord(
            **Resource.parse(data, metadata),
            _type=DNSRecordType(data['_type']),
            _value=data['_value'],
            _ttl=int(data['_ttl']),
        )
