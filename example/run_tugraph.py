import json
import logging
from typing import Optional

from dbgpt.datasource.conn_tugraph import TuGraphConnector
from dbgpt.storage.graph_store.tugraph_store import TuGraphStore, TuGraphStoreConfig

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_schema(connector: TuGraphConnector) -> None:
    """create basic schema for tugraph including vertices and edges.

    args:
        connector: initialized tugraph connector
    """
    try:
        # create vertex labels
        entity_schema = {
            "label": "entity",
            "type": "VERTEX",
            "primary": "id",
            "properties": [
                {"name": "id", "type": "STRING", "optional": False},
                {"name": "description", "type": "STRING", "optional": True},
            ],
        }

        document_schema = {
            "label": "document",
            "type": "VERTEX",
            "primary": "id",
            "properties": [
                {"name": "id", "type": "STRING", "optional": False},
                {"name": "content", "type": "STRING", "optional": False},
            ],
        }

        relation_schema = {
            "label": "relation",
            "type": "EDGE",
            "properties": [
                {"name": "type", "type": "STRING", "optional": False},
                {"name": "weight", "type": "DOUBLE", "optional": True},
            ],
        }

        # create vertex and edge labels
        entity_query = f"CALL db.createVertexLabelByJson('{json.dumps(entity_schema)}')"
        document_query = (
            f"CALL db.createVertexLabelByJson('{json.dumps(document_schema)}')"
        )
        relation_query = (
            f"CALL db.createEdgeLabelByJson('{json.dumps(relation_schema)}')"
        )

        # execute schema creation
        logger.info("creating entity schema")
        connector.run(entity_query)
        logger.info("creating document schema")
        connector.run(document_query)
        logger.info("creating relation schema")
        connector.run(relation_query)

        logger.info("successfully created schema")

    except Exception as e:
        logger.error(f"failed to create schema: {str(e)}")
        raise


def init_tugraph(config: Optional[TuGraphStoreConfig] = None) -> TuGraphStore:
    """initialize tugraph store with configuration.

    args:
        config: optional tugraph store configuration

    returns:
        initialized tugraph store instance
    """
    try:
        if not config:
            config = TuGraphStoreConfig(
                name="aaa_default_graph",
                host="127.0.0.1",
                port=7687,
                username="admin",
                password="73@TuGraph",
            )

        # initialize store
        store = TuGraphStore(config)

        # ensure graph exists
        logger.info(f"creating graph: {config.name}")
        store.conn.create_graph(config.name)

        return store

    except Exception as e:
        logger.error(f"failed to initialize tugraph: {str(e)}")
        raise


def main():
    """main function to demonstrate tugraph initialization and usage."""
    try:
        # initialize tugraph store
        store = init_tugraph()
        # create_schema(store.conn)

        # example: create a test vertex
        # create_query = "CALL db.upsertVertex('entity', [{id: '12', name: 'test_entity', type: 'test', properties: {description: 'test entity'}}])"
        create_query = "CALL db.getLabelSchema('edge', 'HOSTILE')"
        print(create_query)
        records = store.conn.run(create_query)
        print(records[0].keys())

        logger.info("successfully initialized and tested tugraph")

    except Exception as e:
        logger.error(f"main execution failed: {str(e)}")
        raise
    finally:
        if "store" in locals():
            store.conn.close()


if __name__ == "__main__":
    main()
