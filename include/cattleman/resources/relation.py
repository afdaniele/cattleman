from typing import Optional, Dict, Any

import cbor2

from ..types import IRelation, Resource, ResourceID, RelationType, ResourceType
from ..utils.misc import assert_type


class Relation(IRelation):

    @staticmethod
    def make(name: str, origin: ResourceID, relation: RelationType, destination: ResourceID,
             value: Optional[Dict[str, Any]] = None, *,
             description: Optional[str] = None) -> 'Relation':
        value = value or {}
        # verify types
        assert_type(name, str)
        assert_type(origin, ResourceID)
        assert_type(relation, RelationType)
        assert_type(destination, ResourceID)
        assert_type(value, dict)
        assert_type(description, str, nullable=True)
        # ---
        relation = Relation(
            id=ResourceID.make(ResourceType.RELATION),
            name=name,
            description=description,
            _origin=origin,
            _relation=relation,
            _destination=destination,
            _value=value
        )
        relation.commit()
        return relation

    @classmethod
    def deserialize(cls, value: bytes, metadata: Optional[Dict] = None) -> 'Relation':
        data = cbor2.loads(value)
        return Relation(
            **Resource.parse(data, metadata),
            _origin=ResourceID(data['_origin']),
            _relation=RelationType(data['_relation']),
            _destination=ResourceID(data['_destination']),
            _value=data['_value']
        )
