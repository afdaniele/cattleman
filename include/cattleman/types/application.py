from typing import Optional

from .basics import IApplication, ResourceID, IPod, IService


class Application(IApplication):

    def __init__(self, name: str, *, id: Optional[str] = None, description: Optional[str] = None):
        if id is None:
            id = ResourceID.make("application")
        super(Application, self).__init__(id, name, description)
        self._commit()

    @classmethod
    def _from_dict(cls, data: dict) -> 'IApplication':
        return super(Application).__init__(**data)

    def add_pod(self, pod: IPod):
        self._pods.append(pod.id)
        self._commit()

    def add_service(self, service: IService):
        self._services.append(service.id)
        self._commit()
