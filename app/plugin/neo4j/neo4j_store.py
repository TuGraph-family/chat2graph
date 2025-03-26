from typing import Optional

from neo4j import GraphDatabase  # type: ignore


class Neo4jStoreConfig:
    """Neo4j store configuration."""

    def __init__(
        self,
        name: str = "neo4j",
        host: str = "localhost",
        port: int = 7687,
        username: str = "neo4j",
        password: str = "password",
        scheme: str = "bolt",
    ):
        """Initialize Neo4j configuration.

        Args:
            name(str): Name of the graph
            host(str): Neo4j server host
            port(int): Neo4j server port
            username(str): Neo4j username
            password(str): Neo4j password
            scheme(str): Connection scheme (bolt/neo4j)
        """
        self.name = name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.scheme = scheme

    @property
    def uri(self) -> str:
        """Get the connection URI."""
        return f"{self.scheme}://{self.host}:{self.port}"


class Neo4jStore:
    """Neo4j graph store implementation."""

    def __init__(self, config: Neo4jStoreConfig):
        """Initialize Neo4j store with configuration.

        Args:
            config: Neo4j store configuration
        """
        self.config = config
        self._driver = None

    @property
    def conn(self):
        """Get the database connection."""
        if not self._driver:
            self._driver = GraphDatabase.driver(
                self.config.uri, auth=(self.config.username, self.config.password)
            )
        return self._driver


def get_neo4j(config: Optional[Neo4jStoreConfig] = None) -> Neo4jStore:
    """Initialize neo4j store with configuration.

    Args:
        config: Optional neo4j store configuration

    Returns:
        Initialized neo4j store instance
    """
    try:
        config = config or Neo4jStoreConfig()
        store = Neo4jStore(config)
        print(f"[log] get graph: {config.name}")

        return store

    except Exception as e:
        print(f"Failed to initialize neo4j: {str(e)}")
        raise
