import os

from app.core.model.graph_db import Neo4jDbConfig
from app.plugin.neo4j.graph_store import GraphStore, get_graph_db


def test_direct_connection():
    """Test direct connection to Neo4j using GraphStore."""
    print("Testing direct connection to Neo4j...")

    # Create configuration for a local Neo4j Docker instance
    config = Neo4jDbConfig(
        type="neo4j",
        host="localhost",
        port=7687,
        user="neo4j",
        pwd="password",  # Change this to match your Neo4j Docker password
        name="neo4j",
    )

    # Initialize the graph store
    graph_store = GraphStore(config)

    # Test the connection with a simple query
    with graph_store.conn.session() as session:
        result = session.run("RETURN 1 as test")
        record = result.single()
        if record and record["test"] == 1:
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")


def test_environment_connection():
    """Test connection to Neo4j using environment variables."""
    print("Testing connection via environment variables...")

    # Set environment variables (in a real scenario, these would be set externally)
    os.environ["KNOWLEDGE_STORE_TYPE"] = "neo4j"
    os.environ["GRAPH_DB_HOST"] = "localhost"
    os.environ["GRAPH_DB_PORT"] = "7687"
    os.environ["GRAPH_DB_USERNAME"] = "neo4j"
    os.environ["GRAPH_DB_PASSWORD"] = "password"  # Change this to match your Neo4j Docker password
    os.environ["GRAPH_DB_NAME"] = "neo4j"

    # Get graph store through the factory function
    graph_store = get_graph_db()

    # Test the connection
    with graph_store.conn.session() as session:
        result = session.run("RETURN 'Connection through env vars' as message")
        record = result.single()
        if record:
            print(f"✅ {record['message']}")
        else:
            print("❌ Connection failed!")


def create_sample_data(graph_store: GraphStore):
    """Create some sample data in the Neo4j database."""
    print("Creating sample data...")

    with graph_store.conn.session() as session:
        # Clear existing data
        session.run("MATCH (n) DETACH DELETE n")

        # Create some nodes and relationships
        session.run("""
            CREATE (alice:Person {name: 'Alice', age: 30})
            CREATE (bob:Person {name: 'Bob', age: 35})
            CREATE (charlie:Person {name: 'Charlie', age: 25})
            CREATE (alice)-[:KNOWS {since: 2010}]->(bob)
            CREATE (bob)-[:KNOWS {since: 2015}]->(charlie)
            CREATE (charlie)-[:KNOWS {since: 2020}]->(alice)
        """)

        # Verify data was created
        result = session.run("MATCH (n:Person) RETURN count(n) as count")
        record = result.single()
        if record and record["count"] == 3:
            print(f"✅ Created {record['count']} Person nodes")
        else:
            print("❌ Failed to create sample data")


def query_data(graph_store: GraphStore):
    """Query and display data from the Neo4j database."""
    print("\nQuerying data from Neo4j...")

    with graph_store.conn.session() as session:
        # Query all persons
        print("\nAll persons:")
        result = session.run("MATCH (p:Person) RETURN p.name AS name, p.age AS age ORDER BY p.name")
        for record in result:
            print(f"  - {record['name']}, {record['age']} years old")

        # Query relationships
        print("\nRelationships:")
        result = session.run("""
            MATCH (p1:Person)-[r:KNOWS]->(p2:Person)
            RETURN p1.name AS person1, p2.name AS person2, r.since AS since
            ORDER BY r.since
        """)
        for record in result:
            print(f"  - {record['person1']} knows {record['person2']} since {record['since']}")


if __name__ == "__main__":
    print("=== Neo4j Graph Store Test ===")
    try:
        # Test connections
        test_direct_connection()
        print()
        test_environment_connection()

        # Use the graph store to create and query data
        config = Neo4jDbConfig(
            type="neo4j",
            host="localhost",
            port=7687,
            user="neo4j",
            pwd="password",  # Change this to match your Neo4j Docker password
            name="neo4j",
        )
        graph_store = GraphStore(config)

        print("\n=== Sample Data Operations ===")
        create_sample_data(graph_store)
        query_data(graph_store)

        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise
