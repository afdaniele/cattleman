from typing import Optional, List

from .basics import INode, ResourceID, IIPAddress, ICluster, Resource
from ..utils.misc import assert_type


class Node(INode):

    def __init__(self, name: str, ip_addresses: List[IIPAddress], cluster: ICluster, *, id: Optional[ResourceID] = None,
                 description: Optional[str] = None):
        # make new ID if needed
        if id is None:
            id = ResourceID.make("node")
        # verify types
        assert_type(name, str)
        assert_type(ip_addresses, list)
        assert_type(cluster, ICluster)
        assert_type(id, ResourceID, nullable=True)
        assert_type(description, str, nullable=True)
        # get IPs' ID
        ip_ids = list(map(lambda ip: ip.id, ip_addresses))
        super(Node, self).__init__(
            id=id,
            name=name,
            description=description,
            _ip_addresses=ip_ids,
            _cluster=cluster.id,
            **Resource.defaults()
        )
        self._commit()

    # @classmethod
    # def _from_dict(cls, data: dict) -> 'INode':
    #     return super(Node).__init__(**data)
