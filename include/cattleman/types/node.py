from typing import Optional

from .basics import INode, ResourceID, IIPAddress, ICluster


class Node(INode):

    def __init__(self, name: str, ip: IIPAddress, cluster: ICluster, *, id: Optional[str] = None,
                 description: Optional[str] = None):
        if id is None:
            id = ResourceID.make("node")
        super(Node, self).__init__(id, name, description, ip.id, cluster.id)
        self._commit()

    @classmethod
    def _from_dict(cls, data: dict) -> 'INode':
        return super(Node).__init__(**data)
