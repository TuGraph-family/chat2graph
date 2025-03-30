from typing import Optional

from dbgpt_ext.storage.graph_store.tugraph_store import (  # type: ignore
    TuGraphStore,
    TuGraphStoreConfig,
)


def get_tugraph(config: Optional[TuGraphStoreConfig] = None) -> TuGraphStore:
    """initialize tugraph store with configuration.

    args:
        config: optional tugraph store configuration

    returns:
        initialized tugraph store instance
    """
    try:
        config = config or TuGraphStoreConfig()

        # initialize store
        store = TuGraphStore(config)

        # ensure graph exists
        print(f"[log] get graph: {config.name}")
        store.conn.create_graph(config.name)

        return store

    except Exception as e:
        print(f"failed to initialize tugraph: {str(e)}")
        raise
