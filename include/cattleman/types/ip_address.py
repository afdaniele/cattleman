from typing import Optional

from .basics import ResourceID, IIPAddress, IPAddressType


class IPAddress(IIPAddress):

    def __init__(self, name: str, type: IPAddressType, value: str, *, id: Optional[str] = None,
                 description: Optional[str] = None):
        if id is None:
            id = ResourceID.make("ip")
        super(IPAddress, self).__init__(id, name, description, type, value)
        self._commit()

    @classmethod
    def _from_dict(cls, data: dict) -> 'IIPAddress':
        return super(IPAddress).__init__(**data)
