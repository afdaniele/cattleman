from typing import Optional

import cbor2

from .basics import ResourceID, IApplication, Resource
from ..utils.misc import assert_type


class Application(IApplication):

    @staticmethod
    def make(name: str, *, description: Optional[str] = None) -> 'Application':
        # verify types
        assert_type(name, str)
        assert_type(description, str, nullable=True)
        # ---
        application = Application(
            id=ResourceID.make("application"),
            name=name,
            description=description,
        )
        application.commit()
        return application

    @classmethod
    def deserialize(cls, data: bytes) -> 'Application':
        data = cbor2.loads(data)
        return Application(
            **Resource.parse(data),
        )
