# test_neo4j.py

from app.plugin.neo4j.neo4j_store import Neo4jStoreConfig, get_neo4j


def test_connection():
    """Test the connection to the Neo4j database."""
    config = Neo4jStoreConfig(
        name="neo4j",
        host="localhost",
        port=7687,
        username="",
        password="",
    )

    try:
        store = get_neo4j(config)

        with store.conn.session() as session:
            result = session.run("RETURN 'Hello, Neo4j!' as message")
            message = result.single()["message"]
            print(f"Query result: {message}")

        print("Connection test successful!")
        return True

    except Exception as e:
        print(f"Connection test failed: {str(e)}")
        return False
    finally:
        if "store" in locals():
            store.conn.close()


if __name__ == "__main__":
    test_connection()
