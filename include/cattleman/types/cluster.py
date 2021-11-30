from typing import Optional

from .basics import ICluster, ResourceID, Resource
from ..utils.misc import assert_type


class Cluster(ICluster):

    def __init__(self, name: str, *, id: Optional[ResourceID] = None, description: Optional[str] = None, **kwargs):
        # make new ID if needed
        if id is None:
            id = ResourceID.make("cluster")
        # verify types
        assert_type(name, str)
        assert_type(id, ResourceID, nullable=True)
        assert_type(description, str, nullable=True)
        # ---
        super(Cluster, self).__init__(
            id=id,
            name=name,
            description=description,
            **Resource.defaults(),
            **kwargs
        )
        self._commit()

    # @classmethod
    # def _from_dict(cls, data: dict) -> 'ICluster':
    #     return super(Cluster).__init__(**data)
