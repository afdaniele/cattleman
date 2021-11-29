import sqlite3
from datetime import datetime

from dateutil import parser

from cattleman.types.basics import KnowledgeBase, ICluster


def load_configuration_from_database(dbpath: str):
    connection = sqlite3.connect(dbpath)
    cursor = connection.cursor()
    # read clusters
    cursor.execute("SELECT * FROM clusters WHERE enabled=1")
    for row in cursor.fetchall():
        c_id, _, _, c_data = row
        cluster = ICluster.deserialize(c_data)
        KnowledgeBase.set(c_id, cluster)
