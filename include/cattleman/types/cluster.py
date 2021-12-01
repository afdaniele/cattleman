from typing import Optional

import cbor2

from .basics import ICluster, ResourceID, Resource, ResourceStatus, Status, INode
from ..utils.misc import assert_type


class Cluster(ICluster):

    @staticmethod
    def make(name: str, *, description: Optional[str] = None) -> 'Cluster':
        # verify types
        assert_type(name, str)
        assert_type(description, str, nullable=True)
        # ---
        cluster = Cluster(
            id=ResourceID.make("cluster"),
            name=name,
            description=description,
            status=[
                ResourceStatus(
                    key="created",
                    value=Status.SUCCESS
                )
            ]
        )
        cluster.commit()
        return cluster

    @classmethod
    def deserialize(cls, data: bytes) -> 'Cluster':
        data = cbor2.loads(data)
        return Cluster(
            **Resource.parse(data),
            _nodes=[ResourceID.deserialize(s) for s in data['_nodes']],
        )
