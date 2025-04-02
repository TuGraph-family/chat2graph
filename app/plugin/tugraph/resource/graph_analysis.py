import json
from typing import Dict, List, Optional
from uuid import uuid4

from app.core.service.graph_db_service import GraphDbService
from app.core.toolkit.tool import Tool


class AlgorithmsGetter(Tool):
    """Tool to get all algorithms from the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.get_algorithms.__name__,
            description=self.get_algorithms.__doc__ or "",
            function=self.get_algorithms,
        )

    async def get_algorithms(self, grapb_db_service: GraphDbService) -> str:
        """Retrieve all algorithm plugins of a specified type and version supported by the graph
        database.

        This function queries the database to fetch all algorithm plugins of type 'CPP' and version
        'v1' or 'v2', and returns their description information as a JSON formatted string.

        Returns:
            str: A JSON string containing the description information of all matching algorithm
            plugins.
        """
        plugins: List[Dict[str, str]] = []
        query_v1 = "CALL db.plugin.listPlugin('CPP','v1')"
        query_v2 = "CALL db.plugin.listPlugin('CPP','v2')"
        db = grapb_db_service.get_default_graph_db()
        records_1 = db.conn.run(query=query_v1)
        records_2 = db.conn.run(query=query_v2)
        for record in records_1:
            plugin_str = str(record["plugin_description"])
            plugin_json = json.loads(plugin_str)
            plugins.append(
                {
                    "algorithm_name": plugin_json["name"],
                    "algorithm_description": plugin_json["description"],
                }
            )
        for record in records_2:
            plugin_str = str(record["plugin_description"])
            plugin_json = json.loads(plugin_str)
            plugins.append(
                {
                    "algorithm_name": plugin_json["name"],
                    "algorithm_description": plugin_json["description"],
                }
            )

        return json.dumps(plugins, indent=4)


class AlgorithmsExecutor(Tool):
    """Tool to execute algorithms on the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.execute_algorithms.__name__,
            description=self.execute_algorithms.__doc__ or "",
            function=self.execute_algorithms,
        )

    async def execute_algorithms(
        self, graph_db_service: GraphDbService, algorithms_name: str
    ) -> str:
        """Execute the specified algorithm on the graph database.

        This function calls the specified algorithm plugin on the graph database and returns the
        result.

        Args:
            algorithms_name (str): The name of the algorithm to execute. Pay attention to the format
            of the algorithm name.

        Returns:
            str: The result of the algorithm execution.
        """
        query = f"""CALL db.plugin.callPlugin(
            'CPP', 
            '{algorithms_name}', 
            '{{"num_iterations": 100}}', 
            10000.0, 
            false
        )"""

        store = graph_db_service.get_default_graph_db()
        result = store.conn.run(query=query)

        return str(result)
