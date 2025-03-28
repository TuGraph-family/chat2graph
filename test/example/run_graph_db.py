# test_neo4j.py

from app.plugin.neo4j.graph_store import get_graph_db


def test_connection():
    """Test the connection to the Neo4j database."""
    try:
        store = get_graph_db()

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
