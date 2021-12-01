from typing import Optional, List

import cbor2

from .basics import INode, ResourceID, IIPAddress, ICluster, Resource, ResourceType
from ..utils.misc import assert_type


class Node(INode):

    @staticmethod
    def make(name: str, ip_addresses: List[IIPAddress], cluster: ICluster, *, description: Optional[str] = None) -> 'Node':
        # verify types
        assert_type(name, str)
        assert_type(ip_addresses, list, content_klass=IIPAddress)
        assert_type(cluster, ICluster)
        assert_type(description, str, nullable=True)
        # ---
        node = Node(
            id=ResourceID.make(ResourceType.NODE),
            name=name,
            description=description,
            _ip_addresses=list(map(lambda ip: ip.id, ip_addresses)),
            _cluster=cluster.id
        )
        node.commit()
        return node

    @classmethod
    def deserialize(cls, data: bytes) -> 'Node':
        data = cbor2.loads(data)
        return Node(
            **Resource.parse(data),
            _ip_addresses=[ResourceID.deserialize(s) for s in data['_ip_addresses']],
            _cluster=ResourceID.deserialize(data['_cluster']),
            _pods=[ResourceID.deserialize(s) for s in data['_pods']],
        )


    # @classmethod
    # def _from_dict(cls, data: dict) -> 'INode':
    #     return super(Node).__init__(**data)
