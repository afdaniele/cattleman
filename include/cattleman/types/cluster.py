from typing import Optional

from .basics import ICluster, ResourceID


class Cluster(ICluster):

    def __init__(self, name: str, *, id: Optional[str] = None, description: Optional[str] = None):
        if id is None:
            id = ResourceID.make("cluster")
        super(Cluster, self).__init__(id, name, description)
        self._commit()

    @classmethod
    def _from_dict(cls, data: dict) -> 'ICluster':
        return super(Cluster).__init__(**data)
