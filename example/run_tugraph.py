from typing import Optional

from dbgpt.storage.graph_store.tugraph_store import TuGraphStore, TuGraphStoreConfig  # type: ignore


def get_tugraph(config: Optional[TuGraphStoreConfig] = None) -> TuGraphStore:
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
        print(f"[log] get graph: {config.name}")
        store.conn.create_graph(config.name)

        return store

    except Exception as e:
        print(f"failed to initialize tugraph: {str(e)}")
        raise


def main():
    """main function to demonstrate tugraph initialization and usage."""
    try:
        # get tugraph store
        store = get_tugraph()

        query = "CALL db.getLabelSchema('edge', 'HOSTILE')"
        records = store.conn.run(query)
        print(records)

        print("successfully initialized and tested tugraph")

    except Exception as e:
        print(f"main execution failed: {str(e)}")
        raise
    finally:
        if "store" in locals():
            store.conn.close()


if __name__ == "__main__":
    main()
