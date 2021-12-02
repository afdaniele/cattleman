from typing import Optional, List, Dict

import cbor2

from ..relations import RelationsManager
from ..types import INode, ResourceID, IIPAddress, ICluster, Resource, ResourceType, IPod, \
    RelationType
from ..utils.misc import assert_type


class Node(INode):

    def cluster(self) -> ICluster:
        # TODO
        return None

    def ip_addresses(self) -> List[IIPAddress]:
        # TODO
        return None

    def pods(self) -> List[IPod]:
        # TODO
        return None

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
            description=description
        )
        node.commit()
        # create relations
        # [ip] -> node
        for ip in ip_addresses:
            RelationsManager.create(ip, RelationType.BELONGS_TO, node)
        # node -> cluster
        RelationsManager.create(node, RelationType.BELONGS_TO, cluster)
        # ---
        return node

    @classmethod
    def deserialize(cls, value: bytes, metadata: Optional[Dict] = None) -> 'Node':
        data = cbor2.loads(value)
        return Node(
            **Resource.parse(data, metadata),
        )


    # @classmethod
    # def _from_dict(cls, data: dict) -> 'INode':
    #     return super(Node).__init__(**data)
