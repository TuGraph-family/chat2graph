from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.service.graph_db_service import GraphDbService
from app.core.service.service_factory import ServiceFactory

DaoFactory.initialize(DbSession())
ServiceFactory.initialize()


def test_connection():
    """Test the connection to the Neo4j database."""
    try:
        graph_db_service: GraphDbService = GraphDbService.instance
        store = graph_db_service.get_default_graph_db()
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
