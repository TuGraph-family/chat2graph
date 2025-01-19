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
