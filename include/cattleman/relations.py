from typing import Optional, Dict

import cbor2

from cattleman.persistency import Persistency
from cattleman.types import ResourceType, ResourceID, RelationType, Resource
from cattleman.utils.misc import now
from cattleman.utils.sqlite import upsert_query

RELATIONS_TABLE_COLUMNS = (
    "id", "origin_type", "origin", "relation", "destination_type", "destination", "date", "value"
)


class RelationsManager:

    @staticmethod
    def get(origin_type: Optional[ResourceType] = None,
            origin: Optional[ResourceID] = None,
            destination_type: Optional[ResourceType] = None,
            destination: Optional[ResourceID] = None,
            relation: Optional[RelationType] = None):
        conditions = []
        parameters = []
        # - origin type
        if origin_type:
            conditions += ["origin_type=?"]
            parameters += [origin_type]
        # - origin
        if origin:
            conditions += ["origin=?"]
            parameters += [origin]
        # - destination type
        if destination_type:
            conditions += ["destination_type=?"]
            parameters += [destination_type]
        # - destination
        if destination:
            conditions += ["destination=?"]
            parameters += [destination]
        # - relation
        if relation:
            conditions += ["relation=?"]
            parameters += [relation]
        # compile condition
        condition = " AND ".join(conditions)
        # compile query
        query = f"SELECT * FROM relations {condition};"
        # get database
        database = Persistency.database("resources")
        return database.fetchall(query, *parameters)

    @staticmethod
    def create(origin: Resource,
               relation: RelationType,
               destination: Resource,
               value: Optional[Dict] = None):
        return RelationsManager.create_full(origin.get_type(), origin.id, relation,
                                            destination.get_type(), destination.id, value)

    @staticmethod
    def create_full(origin_type: ResourceType,
                    origin: ResourceID,
                    relation: RelationType,
                    destination_type: ResourceType,
                    destination: ResourceID,
                    value: Optional[Dict] = None):
        value = cbor2.dumps(value or {})
        id: ResourceID = ResourceID.make(ResourceType.RELATION)
        with Persistency.session("resources") as cursor:
            query = upsert_query(
                table="relations",
                columns=RELATIONS_TABLE_COLUMNS,
                conflict=("origin", "relation", "destination"),
                update="value"
            )
            # execute query
            cursor.execute(query, id, origin_type, origin, relation, destination_type, destination,
                           now(), value)
