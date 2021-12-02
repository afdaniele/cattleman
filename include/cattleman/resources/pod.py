from typing import Optional, Dict

import cbor2

from ..types import ResourceID, IPod, Resource, INode, IApplication, ResourceType, RelationType
from ..relations import RelationsManager
from ..utils.misc import assert_type


class Pod(IPod):

    def application(self) -> IApplication:
        # TODO
        return None

    def node(self) -> INode:
        # TODO
        return None

    @staticmethod
    def make(name: str, node: INode, application: IApplication, *, description: Optional[str] = None) -> 'Pod':
        # verify types
        assert_type(name, str)
        assert_type(node, INode)
        assert_type(application, IApplication)
        assert_type(description, str, nullable=True)
        # ---
        pod = Pod(
            id=ResourceID.make(ResourceType.POD),
            name=name,
            description=description
        )
        pod.commit()
        # create relations
        # pod -> node
        RelationsManager.create(pod, RelationType.BELONGS_TO, node)
        # pod -> application
        RelationsManager.create(pod, RelationType.BELONGS_TO, application)
        # ---
        return pod

    @classmethod
    def deserialize(cls, value: bytes, metadata: Optional[Dict] = None) -> 'Pod':
        data = cbor2.loads(value)
        return Pod(
            **Resource.parse(data, metadata)
        )
