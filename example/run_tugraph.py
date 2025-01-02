import json
import logging
from typing import Optional

from dbgpt.datasource.conn_tugraph import TuGraphConnector  # type: ignore
from dbgpt.storage.graph_store.tugraph_store import TuGraphStore, TuGraphStoreConfig  # type: ignore

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
                name="default_graph",
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

        query = "CALL db.getLabelSchema('edge', 'HOSTILE')"
        records = store.conn.run(query)
        print(records)

        logger.info("successfully initialized and tested tugraph")

    except Exception as e:
        logger.error(f"main execution failed: {str(e)}")
        raise
    finally:
        if "store" in locals():
            store.conn.close()


if __name__ == "__main__":
    main()
