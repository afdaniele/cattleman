from typing import Optional

from .basics import IApplication, ResourceID, IPod, IService, Resource
from ..utils.misc import assert_type


class Application(IApplication):

    def __init__(self, name: str, *, id: Optional[ResourceID] = None, description: Optional[str] = None):
        # make new ID if needed
        if id is None:
            id = ResourceID.make("application")
        # verify types
        assert_type(name, str)
        assert_type(id, ResourceID, nullable=True)
        assert_type(description, str, nullable=True)
        # ---
        super(Application, self).__init__(
            id=id,
            name=name,
            description=description,
            **Resource.defaults()
        )
        self._commit()

    # @classmethod
    # def _from_dict(cls, data: dict) -> 'IApplication':
    #     return super(Application).__init__(**data)

    def add_pod(self, pod: IPod):
        self._pods.append(pod.id)
        self._commit()

    def add_service(self, service: IService):
        self._services.append(service.id)
        self._commit()
