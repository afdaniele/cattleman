from typing import Optional

import cbor2

from .basics import ResourceID, IPod, Resource, INode, IApplication, ResourceType
from ..utils.misc import assert_type


class Pod(IPod):

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
            description=description,
            _node=node.id,
            _application=application.id
        )
        pod.commit()
        return pod

    @classmethod
    def deserialize(cls, data: bytes) -> 'Pod':
        data = cbor2.loads(data)
        return Pod(
            **Resource.parse(data),
            _node=ResourceID(data['_node']),
            _application=ResourceID(data['_application']),
        )
