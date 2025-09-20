from app.core.common.type import GraphDbType
from app.core.service.graph_db_service import GraphDbConfig, GraphDbService
from app.core.toolkit.graph_db.graph_db import GraphDb
from app.core.toolkit.graph_db.graph_db_factory import GraphDbFactory
from test.resource.init_server import init_server

init_server()
DB_CONFIG = GraphDbConfig( #TODO
    type=GraphDbType.NEO4J,
    name="test",
    desc="test",
    host="192.168.18.197",
    port=7687,
    user="neo4j",
    pwd="shl102519"
)

def register_and_get_graph_db() -> GraphDb:
    db_service: GraphDbService = GraphDbService.instance
    for config in db_service.get_all_graph_db_configs():
        if config.name == DB_CONFIG.name:
            db_service.delete_graph_db(config.id)
    
    db_config =db_service.create_graph_db(DB_CONFIG)
    db: GraphDb = GraphDbFactory.get_graph_db(graph_db_type=db_config.type, config=db_config)
    with db.conn.session() as session:
            # 执行 Cypher 查询
            result = session.run(
                "RETURN 1 AS ping"
            ).single()
            print(f"{result}, conn successfully!")
        
    return db