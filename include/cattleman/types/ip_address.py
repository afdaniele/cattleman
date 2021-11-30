from typing import Optional

from .basics import ResourceID, IIPAddress, IPAddressType, Resource
from ..utils.misc import assert_type


class IPAddress(IIPAddress):

    def __init__(self, name: str, type: IPAddressType, value: str, *, id: Optional[ResourceID] = None,
                 description: Optional[str] = None):
        # make new ID if needed
        if id is None:
            id = ResourceID.make("ip")
        # verify types
        assert_type(name, str)
        assert_type(type, IPAddressType)
        assert_type(value, str)
        assert_type(id, ResourceID, nullable=True)
        assert_type(description, str, nullable=True)
        # ---
        super(IPAddress, self).__init__(
            id=id,
            name=name,
            description=description,
            _type=type,
            _value=value,
            **Resource.defaults()
        )
        self._commit()

    # @classmethod
    # def _from_dict(cls, data: dict) -> 'IIPAddress':
    #     return super(IPAddress).__init__(**data)
