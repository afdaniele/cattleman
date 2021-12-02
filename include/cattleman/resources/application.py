from typing import Optional, Dict

import cbor2

from ..types import ResourceID, IApplication, Resource, ResourceType
from ..utils.misc import assert_type


class Application(IApplication):

    @staticmethod
    def make(name: str, *, description: Optional[str] = None) -> 'Application':
        # verify types
        assert_type(name, str)
        assert_type(description, str, nullable=True)
        # ---
        application = Application(
            id=ResourceID.make(ResourceType.APPLICATION),
            name=name,
            description=description,
        )
        application.commit()
        return application

    @classmethod
    def deserialize(cls, value: bytes, metadata: Optional[Dict] = None) -> 'Application':
        data = cbor2.loads(value)
        return Application(
            **Resource.parse(data, metadata),
        )
