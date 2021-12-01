from typing import Optional, List

import cbor2

from .basics import ICluster, ResourceID, Resource, ResourceStatus, Status, INode, ResourceType
from ..utils.misc import assert_type


class Cluster(ICluster):

    def nodes(self) -> List[INode]:
        query = "SELECT * FROM relations WHERE origin=? AND relation=? AND "

    @staticmethod
    def make(name: str, *, description: Optional[str] = None) -> 'Cluster':
        # verify types
        assert_type(name, str)
        assert_type(description, str, nullable=True)
        # ---
        cluster = Cluster(
            id=ResourceID.make(ResourceType.CLUSTER),
            name=name,
            description=description
        )
        cluster.commit()
        return cluster

    @classmethod
    def deserialize(cls, data: bytes) -> 'Cluster':
        data = cbor2.loads(data)
        return Cluster(
            **Resource.parse(data),
        )
