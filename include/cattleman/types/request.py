from typing import Optional

import cbor2

from .basics import ResourceID, IRequest, Resource, Fragment, ResourceType
from ..utils.misc import assert_type


class Request(IRequest):

    @staticmethod
    def make(name: str, fragment: Fragment, *, description: Optional[str] = None) -> 'Request':
        # verify types
        assert_type(name, str)
        assert_type(fragment, Fragment)
        assert_type(description, str, nullable=True)
        # ---
        request = Request(
            id=ResourceID.make(ResourceType.REQUEST),
            name=name,
            description=description,
            _fragment=fragment,
        )
        request.commit()
        return request

    @classmethod
    def deserialize(cls, data: bytes) -> 'Request':
        data = cbor2.loads(data)
        return Request(
            **Resource.parse(data),
            _fragment=Fragment(data['_fragment']),
        )
