import json

from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.dal.drop_db import drop_db
from app.core.dal.init_db import init_db
from app.core.service.file_service import FileService
from app.core.service.service_factory import ServiceFactory
from app.plugin.neo4j.resource.read_doc import SchemaManager

drop_db()
init_db()

DaoFactory.initialize(DbSession())
ServiceFactory.initialize()


async def test():
    """Test function to check the module."""

    # Test schema reading
    print("Initial schema:")
    schema = await SchemaManager.read_schema(file_service=FileService.instance)
    print(json.dumps(schema, indent=2))
    print("-" * 50)

    # Test schema writing
    print("Updating schema...")
    # Create a new node type to add to the schema
    new_node = {"Person": {"properties": {"name": "string", "age": "integer"}}}
    # Create a new relationship type
    new_relationship = {"WORKS_FOR": {"properties": {"since": "date"}}}
    # Create modified schema with new node and relationship
    modified_schema = {"nodes": new_node, "relationships": new_relationship}

    # Write the modified schema
    await SchemaManager.write_schema(file_service=FileService.instance, schema=modified_schema)
    print("Schema updated successfully")
    print("-" * 50)

    # Read the updated schema to verify changes
    print("Updated schema:")
    updated_schema = await SchemaManager.read_schema(file_service=FileService.instance)
    print(json.dumps(updated_schema, indent=2))
    print("-" * 50)


if __name__ == "__main__":
    import asyncio
    import json

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
