from typing import Optional, List, Dict

import cbor2

from ..types import ICluster, ResourceID, Resource, INode, ResourceType
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
    def deserialize(cls, value: bytes, metadata: Optional[Dict] = None) -> 'Cluster':
        data = cbor2.loads(value)
        return Cluster(
            **Resource.parse(data, metadata),
        )
