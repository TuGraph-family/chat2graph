import asyncio  # Added import
import json
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.service.graph_db_service import GraphDbService
from app.core.service.service_factory import ServiceFactory
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

    async def get_algorithms(self) -> str:
        """Retrieve all algorithm plugins supported by the Neo4j graph database.

        This function queries the Neo4j Graph Data Science library to get a list of
        available algorithms and their descriptions.

        Args:
            None

        Returns:
            str: A JSON string containing the list of supported algorithms,
                their categories and descriptions.
        """
        # the algorithms from the screenshot
        algorithms = [
            {
                "name": "PageRankExecutor",
                "category": "Centrality",
                "description": "Measures the importance of nodes based on the importance of their incoming neighbors.",  # noqa: E501
            },
            {
                "name": "BetweennessCentralityExecutor",
                "category": "Centrality",
                "description": "Measures the number of shortest paths that pass through a node.",
            },
            {
                "name": "LouvainExecutor",
                "category": "Community Detection",
                "description": "Detects communities in a graph using the Louvain method for optimizing modularity.",  # noqa: E501
            },
            {
                "name": "LabelPropagationExecutor",
                "category": "Community Detection",
                "description": "Detects communities by propagating labels based on neighbor consensus.",  # noqa: E501
            },
            {
                "name": "ShortestPathExecutor",
                "category": "Path Finding",
                "description": "Finds the shortest path between two nodes in a graph.",
            },
            {
                "name": "NodeSimilarityExecutor",
                "category": "Similarity",
                "description": "Computes similarity between nodes based on their shared neighbors.",
            },
            {
                "name": "CommonNeighborsExecutor",
                "category": "Similarity",
                "description": "Computes the number of common neighbors between pairs of nodes.",
            },
            {
                "name": "KMeansExecutor",
                "category": "Machine Learning",
                "description": "Clusters nodes based on their properties using the K-means algorithm.",  # noqa: E501
            },
        ]

        return json.dumps({"algorithms": algorithms}, indent=2, ensure_ascii=False)


class PageRankExecutor(Tool):
    """Tool to execute the PageRank algorithm on the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.execute_page_rank_algorithm.__name__,
            description=self.execute_page_rank_algorithm.__doc__ or "",
            function=self.execute_page_rank_algorithm,
        )

    async def execute_page_rank_algorithm(
        self,
        graph_db_service: GraphDbService,
        vertex_label: str = "*",
        relationship_type: str = "*",
        iterations: int = 20,
        damping_factor: float = 0.85,
        tolerance: float = 0.0000001,
        top_n: int = 10,
    ) -> str:
        """Execute the PageRank algorithm on the graph database.

        Args:
            vertex_label (str): Label of nodes to include in calculation, "*" for all nodes.
            relationship_type (str): Type of relationships to consider, "*" for all relationships.
            iterations (int): Maximum number of iterations to run the algorithm.
            damping_factor (float): The probability of following relationships versus randomly jumping to a node.
            tolerance (float): Minimum change in scores between iterations to continue calculation.
            top_n (int): Number of top-ranked nodes to return.

        Returns:
            str: The result of the algorithm execution in JSON format.
        """  # noqa: E501
        store = graph_db_service.get_default_graph_db()
        # generate a unique name for the graph projection
        graph_name = f"pagerank_graph_{uuid4().hex[:8]}"

        result = {}

        try:
            with store.conn.session() as session:
                # step 1: Create graph projection
                result["graph_creation"] = session.run(
                    f"""
                    CALL gds.graph.project(
                        '{graph_name}',
                        '{vertex_label}',
                        '{relationship_type}'
                    )
                    YIELD graphName, nodeCount, relationshipCount
                    RETURN graphName, nodeCount, relationshipCount
                    """
                ).data()

                # step 2: Execute PageRank algorithm
                pagerank_result = session.run(
                    f"""
                    CALL gds.pageRank.stream('{graph_name}', {{
                        maxIterations: {iterations},
                        dampingFactor: {damping_factor},
                        tolerance: {tolerance}
                    }})
                    YIELD nodeId, score
                    WITH gds.util.asNode(nodeId) AS node, score
                    RETURN node.name AS name, node.id AS id, labels(node) AS labels, score
                    ORDER BY score DESC
                    LIMIT {top_n}
                    """
                ).data()

                # Clean up result for better readability
                cleaned_result = []
                for record in pagerank_result:
                    cleaned_record = {
                        "name": record.get("name", "N/A"),
                        "id": record.get("id", "N/A"),
                        "labels": record.get("labels", []),
                        "score": record.get("score"),
                    }
                    cleaned_result.append(cleaned_record)

                result["pagerank_results"] = cleaned_result

                # step 3: Get algorithm statistics
                stats = session.run(
                    f"""
                    CALL gds.pageRank.stats('{graph_name}', {{
                        maxIterations: {iterations},
                        dampingFactor: {damping_factor},
                        tolerance: {tolerance}
                    }})
                    YIELD ranIterations, didConverge, preProcessingMillis, computeMillis, postProcessingMillis
                    RETURN ranIterations, didConverge, preProcessingMillis, computeMillis, postProcessingMillis
                    """  # noqa: E501
                ).data()

                result["algorithm_stats"] = stats[0] if stats else {}

                # step 4: Remove graph projection
                drop_result = session.run(
                    f"""
                    CALL gds.graph.drop('{graph_name}')
                    YIELD graphName
                    RETURN graphName
                    """
                ).data()

                result["graph_removal"] = drop_result

        except Exception as e:
            # in case of errors, try to clean up the graph projection
            try:
                with store.conn.session() as session:
                    session.run(f"CALL gds.graph.drop('{graph_name}', false)")
            except Exception:
                pass

            result["error"] = str(e)

        # return results as JSON string
        return json.dumps(result, indent=2, ensure_ascii=False)


class BetweennessCentralityExecutor(Tool):
    """Tool to execute the Betweenness Centrality algorithm on the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.execute_betweenness_centrality_algorithm.__name__,
            description=self.execute_betweenness_centrality_algorithm.__doc__ or "",
            function=self.execute_betweenness_centrality_algorithm,
        )

    async def execute_betweenness_centrality_algorithm(
        self,
        graph_db_service: GraphDbService,
        vertex_label: str = "*",
        relationship_type: str = "*",
        sample_size: int = 100,
        top_n: int = 10,
    ) -> str:
        """Execute the Betweenness Centrality algorithm on the graph database.

        this function will:
        1. create a graph projection with the specified node labels and relationship types
        2. execute the betweenness centrality algorithm on the projected graph
        3. retrieve the top-ranked nodes based on betweenness score
        4. gather statistics about the algorithm execution
        5. remove the graph projection

        example cypher queries executed (for a graph with Person nodes and BELONGS_TO relationships):
        - create projection:
          CALL gds.graph.project('betweenness_graph_12345678', 'Person', 'BELONGS_TO')
        - execute betweenness centrality:
          CALL gds.betweenness.stream('betweenness_graph_12345678', {samplingSize: 100})
          YIELD nodeId, score
          WITH gds.util.asNode(nodeId) AS node, score
          RETURN node.name AS name, node.id AS id, labels(node) AS labels, score
          ORDER BY score DESC LIMIT 10
        - get statistics:
          CALL gds.betweenness.stats('betweenness_graph_12345678', {samplingSize: 100})
        - remove projection:
          CALL gds.graph.drop('betweenness_graph_12345678')

        Args:
            vertex_label (str): Label of nodes to include in calculation, "*" for all nodes.
            relationship_type (str): Type of relationships to consider, "*" for all relationships.
            sample_size (int): Number of nodes to sample for approximation (0 means exact computation).
            top_n (int): Number of top-ranked nodes to return.

        Returns:
            str: The result of the algorithm execution in JSON format.
        """  # noqa: E501
        store = graph_db_service.get_default_graph_db()
        # generate a unique name for the graph projection
        graph_name = f"betweenness_graph_{uuid4().hex[:8]}"

        result = {}

        try:
            with store.conn.session() as session:
                # step 1: create graph projection
                result["graph_creation"] = session.run(
                    f"""
                    CALL gds.graph.project(
                        '{graph_name}',
                        '{vertex_label}',
                        '{relationship_type}'
                    )
                    YIELD graphName, nodeCount, relationshipCount
                    RETURN graphName, nodeCount, relationshipCount
                    """
                ).data()

                # step 2: execute betweenness centrality algorithm
                sampling_config = f"{{samplingSize: {sample_size}}}" if sample_size > 0 else "{}"
                betweenness_result = session.run(
                    f"""
                    CALL gds.betweenness.stream('{graph_name}', {sampling_config})
                    YIELD nodeId, score
                    WITH gds.util.asNode(nodeId) AS node, score
                    RETURN node.name AS name, node.id AS id, labels(node) AS labels, score
                    ORDER BY score DESC
                    LIMIT {top_n}
                    """
                ).data()

                # clean up result for better readability
                cleaned_result = []
                for record in betweenness_result:
                    cleaned_record = {
                        "name": record.get("name", "N/A"),
                        "id": record.get("id", "N/A"),
                        "labels": record.get("labels", []),
                        "score": record.get("score"),
                    }
                    cleaned_result.append(cleaned_record)

                result["betweenness_results"] = cleaned_result

                # step 3: get algorithm statistics
                stats = session.run(
                    f"""
                    CALL gds.betweenness.stats('{graph_name}', {sampling_config})
                    YIELD preProcessingMillis, computeMillis, postProcessingMillis
                    RETURN preProcessingMillis, computeMillis, postProcessingMillis
                    """
                ).data()

                result["algorithm_stats"] = stats[0] if stats else {}

                # step 4: remove graph projection
                drop_result = session.run(
                    f"""
                    CALL gds.graph.drop('{graph_name}')
                    YIELD graphName
                    RETURN graphName
                    """
                ).data()

                result["graph_removal"] = drop_result

        except Exception as e:
            # in case of errors, try to clean up the graph projection
            try:
                with store.conn.session() as session:
                    session.run(f"CALL gds.graph.drop('{graph_name}', false)")
            except Exception:
                pass

            result["error"] = str(e)

        # return results as json string
        return json.dumps(result, indent=2, ensure_ascii=False)


class LouvainExecutor(Tool):
    """Tool to execute the Louvain community detection algorithm on the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.execute_louvain_algorithm.__name__,
            description=self.execute_louvain_algorithm.__doc__ or "",
            function=self.execute_louvain_algorithm,
        )

    async def execute_louvain_algorithm(
        self,
        graph_db_service: GraphDbService,
        vertex_label: str = "*",
        relationship_type: str = "*",
        include_intermediate_communities: bool = False,
        max_levels: int = 10,
        max_iterations: int = 10,
        tolerance: float = 0.0001,
        top_n: int = 10,
    ) -> str:
        """Execute the Louvain community detection algorithm on the graph database.

        this function will:
        1. create a graph projection with the specified node labels and relationship types
        2. execute the louvain community detection algorithm on the projected graph
        3. retrieve community assignments for nodes
        4. gather statistics about the algorithm execution
        5. remove the graph projection

        example cypher queries executed (for a graph with Person and Location nodes, and BELONGS_TO relationships):
        - create projection:
          CALL gds.graph.project('louvain_graph_12345678', ['Person', 'Location'], 'BELONGS_TO')
        - execute louvain algorithm:
          CALL gds.louvain.stream('louvain_graph_12345678', {
            includeIntermediateCommunities: false,
            maxLevels: 10,
            maxIterations: 10,
            tolerance: 0.0001
          })
          YIELD nodeId, communityId, intermediateCommunityIds
          WITH gds.util.asNode(nodeId) AS node, communityId
          RETURN node.name AS name, node.id AS id, labels(node) AS labels, communityId
          ORDER BY communityId, name LIMIT 10
        - get statistics:
          CALL gds.louvain.stats('louvain_graph_12345678')
        - remove projection:
          CALL gds.graph.drop('louvain_graph_12345678')

        Args:
            vertex_label (str): Label of nodes to include in calculation, "*" for all nodes.
            relationship_type (str): Type of relationships to consider, "*" for all relationships.
            include_intermediate_communities (bool): Whether to include communities from all iterations.
            max_levels (int): Maximum number of hierarchy levels.
            max_iterations (int): Maximum number of iterations per level.
            tolerance (float): Minimum change in modularity between iterations.
            top_n (int): Number of top nodes to return (per community if grouping by community).

        Returns:
            str: The result of the algorithm execution in JSON format.
        """  # noqa: E501
        store = graph_db_service.get_default_graph_db()
        # generate a unique name for the graph projection
        graph_name = f"louvain_graph_{uuid4().hex[:8]}"

        result = {}

        try:
            with store.conn.session() as session:
                # step 1: create graph projection
                result["graph_creation"] = session.run(
                    f"""
                    CALL gds.graph.project(
                        '{graph_name}',
                        '{vertex_label}',
                        '{relationship_type}'
                    )
                    YIELD graphName, nodeCount, relationshipCount
                    RETURN graphName, nodeCount, relationshipCount
                    """
                ).data()

                # step 2: execute louvain algorithm
                louvain_result = session.run(
                    f"""
                    CALL gds.louvain.stream('{graph_name}', {{
                        includeIntermediateCommunities: {str(include_intermediate_communities).lower()},
                        maxLevels: {max_levels},
                        maxIterations: {max_iterations},
                        tolerance: {tolerance}
                    }})
                    YIELD nodeId, communityId, intermediateCommunityIds
                    WITH gds.util.asNode(nodeId) AS node, communityId, intermediateCommunityIds
                    RETURN 
                        node.name AS name, 
                        node.id AS id, 
                        labels(node) AS labels, 
                        communityId,
                        intermediateCommunityIds
                    ORDER BY communityId, name
                    LIMIT {top_n}
                    """  # noqa: E501
                ).data()

                # clean up result for better readability
                cleaned_result = []
                for record in louvain_result:
                    cleaned_record = {
                        "name": record.get("name", "N/A"),
                        "id": record.get("id", "N/A"),
                        "labels": record.get("labels", []),
                        "community_id": record.get("communityId"),
                        "intermediate_community_ids": record.get("intermediateCommunityIds", []),
                    }
                    cleaned_result.append(cleaned_record)

                result["louvain_results"] = cleaned_result

                # step 3: get community distribution statistics
                community_stats = session.run(
                    f"""
                    CALL gds.louvain.stream('{graph_name}', {{
                        includeIntermediateCommunities: false,
                        maxLevels: {max_levels},
                        maxIterations: {max_iterations},
                        tolerance: {tolerance}
                    }})
                    YIELD nodeId, communityId
                    RETURN 
                        communityId, 
                        count(*) AS communitySize
                    ORDER BY communitySize DESC
                    LIMIT 10
                    """
                ).data()

                result["community_stats"] = community_stats

                # step 4: get algorithm execution statistics
                stats = session.run(
                    f"""
                    CALL gds.louvain.stats('{graph_name}', {{
                        includeIntermediateCommunities: {str(include_intermediate_communities).lower()},
                        maxLevels: {max_levels},
                        maxIterations: {max_iterations},
                        tolerance: {tolerance}
                    }})
                    YIELD preProcessingMillis, computeMillis, postProcessingMillis, communityCount, modularity, modularities
                    RETURN preProcessingMillis, computeMillis, postProcessingMillis, communityCount, modularity, modularities
                    """  # noqa: E501
                ).data()

                result["algorithm_stats"] = stats[0] if stats else {}

                # step 5: remove graph projection
                drop_result = session.run(
                    f"""
                    CALL gds.graph.drop('{graph_name}')
                    YIELD graphName
                    RETURN graphName
                    """
                ).data()

                result["graph_removal"] = drop_result

        except Exception as e:
            # in case of errors, try to clean up the graph projection
            try:
                with store.conn.session() as session:
                    session.run(f"CALL gds.graph.drop('{graph_name}', false)")
            except Exception:
                pass

            result["error"] = str(e)

        # return results as json string
        return json.dumps(result, indent=2, ensure_ascii=False)


class LabelPropagationExecutor(Tool):
    """Tool to execute the Label Propagation community detection algorithm on the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.execute_label_propagation_algorithm.__name__,
            description=self.execute_label_propagation_algorithm.__doc__ or "",
            function=self.execute_label_propagation_algorithm,
        )

    async def execute_label_propagation_algorithm(
        self,
        graph_db_service: GraphDbService,
        vertex_label: str = "*",
        relationship_type: str = "*",
        max_iterations: int = 10,
        weight_property: Optional[str] = None,
        seed_property: Optional[str] = None,
        top_n: int = 10,
    ) -> str:
        """Execute the Label Propagation community detection algorithm on the graph database.

        this function will:
        1. create a graph projection with the specified node labels and relationship types
        2. execute the label propagation algorithm on the projected graph
        3. retrieve community assignments for nodes
        4. gather statistics about the algorithm execution and community distribution
        5. remove the graph projection

        example cypher queries executed (for a graph with Event nodes and AFFECTS relationships):
        - create projection:
          CALL gds.graph.project('labelprop_graph_12345678', 'Event', 'AFFECTS')
        - execute label propagation algorithm:
          CALL gds.labelPropagation.stream('labelprop_graph_12345678', {
            maxIterations: 10
          })
          YIELD nodeId, communityId
          WITH gds.util.asNode(nodeId) AS node, communityId
          RETURN node.name AS name, node.id AS id, labels(node) AS labels, communityId
          ORDER BY communityId, name LIMIT 10
        - get statistics:
          CALL gds.labelPropagation.stats('labelprop_graph_12345678', {maxIterations: 10})
        - remove projection:
          CALL gds.graph.drop('labelprop_graph_12345678')

        Args:
            vertex_label (str): Label of nodes to include in calculation, "*" for all nodes.
            relationship_type (str): Type of relationships to consider, "*" for all relationships.
            max_iterations (int): Maximum number of iterations to run.
            weight_property (Optional[str]): Name of relationship property to use as weight.
            seed_property (Optional[str]): Node property to use as initial community.
            top_n (int): Number of top nodes to return (per community if grouping by community).

        Returns:
            str: The result of the algorithm execution in JSON format.
        """  # noqa: E501
        store = graph_db_service.get_default_graph_db()
        # generate a unique name for the graph projection
        graph_name = f"labelprop_graph_{uuid4().hex[:8]}"

        result = {}

        try:
            with store.conn.session() as session:
                # step 1: create graph projection with relationship properties if needed
                projection_query = f"""
                CALL gds.graph.project(
                    '{graph_name}',
                    '{vertex_label}',
                    '{relationship_type}'
                """

                # add relationship properties config if weight property is specified
                if weight_property:
                    projection_query += f""",
                    {{
                        relationshipProperties: {{
                            '{weight_property}': {{
                                property: '{weight_property}',
                                defaultValue: 1.0
                            }}
                        }}
                    }}
                """

                projection_query += """)
                YIELD graphName, nodeCount, relationshipCount
                RETURN graphName, nodeCount, relationshipCount
                """

                result["graph_creation"] = session.run(projection_query).data()

                # step 2: build configuration for label propagation
                config_params = [f"maxIterations: {max_iterations}"]

                if weight_property:
                    config_params.append(f"relationshipWeightProperty: '{weight_property}'")

                if seed_property:
                    config_params.append(f"seedProperty: '{seed_property}'")

                config = "{" + ", ".join(config_params) + "}"

                # step 3: execute label propagation algorithm
                lp_result = session.run(
                    f"""
                    CALL gds.labelPropagation.stream('{graph_name}', {config})
                    YIELD nodeId, communityId
                    WITH gds.util.asNode(nodeId) AS node, communityId
                    RETURN 
                        node.name AS name, 
                        node.id AS id, 
                        labels(node) AS labels, 
                        communityId
                    ORDER BY communityId, name
                    LIMIT {top_n}
                    """
                ).data()

                # clean up result for better readability
                cleaned_result = []
                for record in lp_result:
                    cleaned_record = {
                        "name": record.get("name", "N/A"),
                        "id": record.get("id", "N/A"),
                        "labels": record.get("labels", []),
                        "community_id": record.get("communityId"),
                    }
                    cleaned_result.append(cleaned_record)

                result["labelprop_results"] = cleaned_result

                # step 4: get community distribution statistics
                community_stats = session.run(
                    f"""
                    CALL gds.labelPropagation.stream('{graph_name}', {config})
                    YIELD nodeId, communityId
                    RETURN 
                        communityId, 
                        count(*) AS communitySize
                    ORDER BY communitySize DESC
                    LIMIT 10
                    """
                ).data()

                result["community_stats"] = community_stats

                # step 5: get algorithm execution statistics
                stats = session.run(
                    f"""
                    CALL gds.labelPropagation.stats('{graph_name}', {config})
                    YIELD preProcessingMillis, computeMillis, postProcessingMillis, communityCount, didConverge, ranIterations
                    RETURN preProcessingMillis, computeMillis, postProcessingMillis, communityCount, didConverge, ranIterations
                    """  # noqa: E501
                ).data()

                result["algorithm_stats"] = stats[0] if stats else {}

                # step 6: remove graph projection
                drop_result = session.run(
                    f"""
                    CALL gds.graph.drop('{graph_name}')
                    YIELD graphName
                    RETURN graphName
                    """
                ).data()

                result["graph_removal"] = drop_result

        except Exception as e:
            # in case of errors, try to clean up the graph projection
            try:
                with store.conn.session() as session:
                    session.run(f"CALL gds.graph.drop('{graph_name}', false)")
            except Exception:
                pass

            result["error"] = str(e)

        # return results as json string
        return json.dumps(result, indent=2, ensure_ascii=False)


class ShortestPathExecutor(Tool):
    """Tool to execute the Shortest Path algorithm on the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.execute_shortest_path_algorithm.__name__,
            description=self.execute_shortest_path_algorithm.__doc__ or "",
            function=self.execute_shortest_path_algorithm,
        )

    async def execute_shortest_path_algorithm(
        self,
        graph_db_service: GraphDbService,
        start_node_id: str,
        end_node_id: Union[str, List[str]],
        vertex_label: str = "*",
        relationship_type: str = "*",
        weight_property: Optional[str] = None,
        path_details: bool = True,
    ) -> str:
        """Execute the Shortest Path algorithm (Dijkstra) on the graph database.

        this function will:
        1. create a graph projection with the specified node labels and relationship types
        2. execute the dijkstra shortest path algorithm between the specified start and end nodes
        3. retrieve the path details including nodes and relationships in the path
        4. gather statistics about the algorithm execution
        5. remove the graph projection

        example cypher queries executed (for a graph with LOCATION nodes and BELONGS_TO relationships):
        - create projection with relationship property:
            CALL gds.graph.project('shortestpath_graph_12345678', 'LOCATION', 'BELONGS_TO',
                {relationshipProperties: {weight: {property: 'distance', defaultValue: 1.0}}})
        - create projection without relationship property:
            CALL gds.graph.project('shortestpath_graph_12345678', 'LOCATION', 'BELONGS_TO')
        - execute shortest path algorithm:
            MATCH (source) WHERE source.id = 'loc123'
            MATCH (target) WHERE target.id = 'loc456'
            CALL gds.shortestPath.dijkstra.stream('shortestpath_graph_12345678', {
                sourceNode: elementId(source), // Use elementId()
                targetNodes: [elementId(target)], // Use elementId()
                relationshipWeightProperty: 'weight'
            })
            YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path
            RETURN
                index,
                gds.util.asNode(sourceNode).name AS sourceNodeName,
                gds.util.asNode(targetNode).name AS targetNodeName,
                totalCost,
                [nodeId IN nodeIds | gds.util.asNode(nodeId).name] AS nodeNames,
                costs,
                path
        - get statistics:
            MATCH (source) WHERE source.id = 'loc123'
            MATCH (target) WHERE target.id = 'loc456'
            CALL gds.shortestPath.dijkstra.stream('shortestpath_graph_12345678', {
                sourceNode: elementId(source), // Use elementId()
                targetNodes: [elementId(target)], // Use elementId()
                relationshipWeightProperty: 'weight'
            })
            YIELD totalCost
            RETURN min(totalCost) AS minCost, max(totalCost) AS maxCost, count(*) AS pathCount
        - remove projection:
          CALL gds.graph.drop('shortestpath_graph_123456')

        Args:
            start_node_id (str): ID of the starting point node, not the elementId.
            end_node_id (Union[str, List[str]]): ID or list of IDs for destination point(s).
            vertex_label (str): Label of nodes to include in calculation, "*" for all nodes.
            relationship_type (str): Type of relationships to consider, "*" for all relationships.
            weight_property (Optional[str]): Name of relationship property to use as weight.
            path_details (bool): Whether to include full path details in the result.

        Returns:
            str: The result of the algorithm execution in JSON format.
        """  # noqa: E501
        store = graph_db_service.get_default_graph_db()
        # generate a unique name for the graph projection
        graph_name = f"shortestpath_graph_{uuid4().hex[:8]}"

        result = {}

        try:
            with store.conn.session() as session:
                # step 1: create graph projection with relationship properties if needed
                projection_query = ""

                # determine if we need to add relationship properties
                if weight_property:
                    # use proper format for relationship properties with default value
                    projection_query = f"""
                    CALL gds.graph.project(
                        '{graph_name}',
                        '{vertex_label}',
                        '{relationship_type}',
                        {{
                            relationshipProperties: {{
                                weight: {{
                                    property: '{weight_property}',
                                    defaultValue: 1.0
                                }}
                            }}
                        }}
                    )
                    YIELD graphName, nodeCount, relationshipCount
                    RETURN graphName, nodeCount, relationshipCount
                    """
                else:
                    # create projection without relationship properties
                    projection_query = f"""
                    CALL gds.graph.project(
                        '{graph_name}',
                        '{vertex_label}',
                        '{relationship_type}'
                    )
                    YIELD graphName, nodeCount, relationshipCount
                    RETURN graphName, nodeCount, relationshipCount
                    """

                result["graph_creation"] = session.run(projection_query).data()

                # step 2: first find the node objects based on their IDs
                # convert end_node_id to list if it's a single value
                target_ids = end_node_id if isinstance(end_node_id, list) else [end_node_id]

                # find source node using elementId()
                source_node_query = f"""
                MATCH (source)
                WHERE source.id = '{start_node_id}'
                RETURN elementId(source) AS sourceNodeId
                """
                source_result = session.run(source_node_query).data()
                if not source_result:
                    raise ValueError(f"Source node with id '{start_node_id}' not found")
                source_node_id = source_result[0]["sourceNodeId"]

                # find target nodes using elementId()
                target_node_ids = []
                for target_id in target_ids:
                    target_node_query = f"""
                    MATCH (target)
                    WHERE target.id = '{target_id}'
                    RETURN elementId(target) AS targetNodeId
                    """
                    target_result = session.run(target_node_query).data()
                    if target_result:
                        target_node_ids.append(target_result[0]["targetNodeId"])

                if not target_node_ids:
                    raise ValueError("No target nodes found with the provided IDs")

                # step 3: build configuration for shortest path
                # GDS requires the internal node ID, not the elementId string.
                # We need to match the nodes again within the CALL block or pass the internal IDs.
                # Passing internal IDs directly is cleaner if we fetch them first.
                # However, GDS procedures often accept the node object itself or its elementId.
                # Let's try passing elementId strings directly first, as it's simpler.
                # If that fails, we'll need to adjust to pass internal IDs or node objects.

                # re-fetch internal IDs for GDS call
                source_internal_id_query = (
                    f"MATCH (n) WHERE elementId(n) = '{source_node_id}' RETURN id(n) AS internalId"
                )
                source_internal_id = session.run(source_internal_id_query).single()["internalId"]

                target_internal_ids = []
                for target_node_id_str in target_node_ids:
                    target_internal_id_query = (
                        "MATCH (n) WHERE elementId(n) = "
                        f"'{target_node_id_str}' RETURN id(n) AS internalId"
                    )
                    target_internal_id = session.run(target_internal_id_query).single()[
                        "internalId"
                    ]
                    target_internal_ids.append(target_internal_id)

                config_params = [
                    f"sourceNode: {source_internal_id}",
                    f"targetNodes: {target_internal_ids}",
                ]

                if weight_property:
                    config_params.append("relationshipWeightProperty: 'weight'")

                config = "{" + ", ".join(config_params) + "}"

                # step 4: execute shortest path algorithm using dijkstra
                if path_details:
                    path_result = session.run(
                        f"""
                        CALL gds.shortestPath.dijkstra.stream('{graph_name}', {config})
                        YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path
                        RETURN 
                            index,
                            gds.util.asNode(sourceNode).name AS sourceNodeName,
                            gds.util.asNode(sourceNode).id AS sourceNodeId,
                            gds.util.asNode(targetNode).name AS targetNodeName,
                            gds.util.asNode(targetNode).id AS targetNodeId,
                            totalCost,
                            [nodeId IN nodeIds | gds.util.asNode(nodeId).name] AS nodeNames,
                            [nodeId IN nodeIds | gds.util.asNode(nodeId).id] AS nodeIds,
                            costs
                        """
                    ).data()
                else:
                    path_result = session.run(
                        f"""
                        CALL gds.shortestPath.dijkstra.stream('{graph_name}', {config})
                        YIELD sourceNode, targetNode, totalCost
                        RETURN 
                            gds.util.asNode(sourceNode).name AS sourceNodeName,
                            gds.util.asNode(sourceNode).id AS sourceNodeId,
                            gds.util.asNode(targetNode).name AS targetNodeName,
                            gds.util.asNode(targetNode).id AS targetNodeId,
                            totalCost
                        """
                    ).data()

                result["path_results"] = path_result

                # step 5: get algorithm execution statistics
                stats = session.run(
                    f"""
                    CALL gds.shortestPath.dijkstra.stream('{graph_name}', {config})
                    YIELD totalCost
                    RETURN min(totalCost) AS minCost, max(totalCost) AS maxCost, count(*) AS pathCount
                    """  # noqa: E501
                ).data()

                result["algorithm_stats"] = stats[0] if stats else {}

                # step 6: remove graph projection
                drop_result = session.run(
                    f"""
                    CALL gds.graph.drop('{graph_name}')
                    YIELD graphName
                    RETURN graphName
                    """
                ).data()

                result["graph_removal"] = drop_result

        except Exception as e:
            # in case of errors, try to clean up the graph projection
            try:
                with store.conn.session() as session:
                    session.run(f"CALL gds.graph.drop('{graph_name}', false)")
            except Exception:
                pass

            result["error"] = str(e)

        # return results as json string
        return json.dumps(result, indent=2, ensure_ascii=False)


class NodeSimilarityExecutor(Tool):
    """Tool to execute the Node Similarity algorithm on the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.execute_node_similarity_algorithm.__name__,
            description=self.execute_node_similarity_algorithm.__doc__ or "",
            function=self.execute_node_similarity_algorithm,
        )

    async def execute_node_similarity_algorithm(
        self,
        graph_db_service: GraphDbService,
        vertex_label: str = "*",
        relationship_type: str = "*",
        top_k: int = 10,
        top_n: int = 10,
        similarity_cutoff: float = 0.1,
        degree_cutoff: int = 1,
    ) -> str:
        """Execute the Node Similarity algorithm on the graph database.

        this function will:
        1. create a graph projection with the specified node labels and relationship types
        2. execute the node similarity algorithm to find similar nodes based on their relationships
        3. retrieve the top similar node pairs with their similarity scores
        4. gather statistics about the algorithm execution
        5. remove the graph projection

        example cypher queries executed (for a graph with Person nodes and AFFECTS relationships):
        - create projection:
            CALL gds.graph.project('similarity_graph_12345678', 'Person', 'AFFECTS')
        - execute node similarity algorithm:
            CALL gds.nodeSimilarity.stream('similarity_graph_12345678', {
                topK: 10,
                similarityCutoff: 0.1,
                degreeCutoff: 1
            })
            YIELD node1, node2, similarity
            RETURN
                gds.util.asNode(node1).name AS person1,
                gds.util.asNode(node2).name AS person2,
                similarity
            ORDER BY similarity DESCENDING, person1, person2
            LIMIT 10
        - get statistics:
            CALL gds.nodeSimilarity.stats('similarity_graph_12345678', {
                topK: 10,
                similarityCutoff: 0.1,
                degreeCutoff: 1
            })
            YIELD preProcessingMillis, computeMillis, postProcessingMillis, similarityPairs, similarityDistribution
            RETURN preProcessingMillis, computeMillis, postProcessingMillis, similarityPairs, similarityDistribution
        - remove projection:
            CALL gds.graph.drop('similarity_graph_12345678')

        Args:
            vertex_label (str): Label of nodes to include in calculation, "*" for all nodes.
            relationship_type (str): Type of relationships to consider, "*" for all relationships.
            top_k (int): Maximum number of similar nodes to compute per node.
            top_n (int): Number of similar node pairs to return in the result.
            similarity_cutoff (float): Lower bound for similarity scores (0-1).
            degree_cutoff (int): Minimum node degree to be considered in the calculation.

        Returns:
            str: The result of the algorithm execution in JSON format.
        """  # noqa: E501
        store = graph_db_service.get_default_graph_db()
        # generate a unique name for the graph projection
        graph_name = f"similarity_graph_{uuid4().hex[:8]}"

        result = {}

        try:
            with store.conn.session() as session:
                # step 1: create graph projection
                result["graph_creation"] = session.run(
                    f"""
                    CALL gds.graph.project(
                        '{graph_name}',
                        '{vertex_label}',
                        '{relationship_type}'
                    )
                    YIELD graphName, nodeCount, relationshipCount
                    RETURN graphName, nodeCount, relationshipCount
                    """
                ).data()

                # step 2: build configuration for node similarity
                config = f"""{{
                    topK: {top_k},
                    similarityCutoff: {similarity_cutoff},
                    degreeCutoff: {degree_cutoff}
                }}"""

                # step 3: execute node similarity algorithm
                similarity_result = session.run(
                    f"""
                    CALL gds.nodeSimilarity.stream('{graph_name}', {config})
                    YIELD node1, node2, similarity
                    WITH 
                        gds.util.asNode(node1) AS first_node,
                        gds.util.asNode(node2) AS second_node,
                        similarity
                    RETURN 
                        first_node.name AS first_node_name,
                        first_node.id AS first_node_id,
                        labels(first_node) AS first_node_labels,
                        second_node.name AS second_node_name,
                        second_node.id AS second_node_id,
                        labels(second_node) AS second_node_labels,
                        similarity
                    ORDER BY similarity DESC, first_node_name, second_node_name
                    LIMIT {top_n}
                    """
                ).data()

                # clean up result for better readability
                cleaned_result = []
                for record in similarity_result:
                    cleaned_record = {
                        "first_node": {
                            "name": record.get("first_node_name", "N/A"),
                            "id": record.get("first_node_id", "N/A"),
                            "labels": record.get("first_node_labels", []),
                        },
                        "second_node": {
                            "name": record.get("second_node_name", "N/A"),
                            "id": record.get("second_node_id", "N/A"),
                            "labels": record.get("second_node_labels", []),
                        },
                        "similarity": record.get("similarity"),
                    }
                    cleaned_result.append(cleaned_record)

                result["similarity_results"] = cleaned_result

                # step 4: get algorithm execution statistics
                stats = session.run(
                    f"""
                    CALL gds.nodeSimilarity.stats('{graph_name}', {config})
                    YIELD preProcessingMillis, computeMillis, postProcessingMillis, similarityPairs, similarityDistribution
                    RETURN preProcessingMillis, computeMillis, postProcessingMillis, similarityPairs, similarityDistribution
                    """  # noqa: E501
                ).data()

                result["algorithm_stats"] = stats[0] if stats else {}

                # step 5: remove graph projection
                drop_result = session.run(
                    f"""
                    CALL gds.graph.drop('{graph_name}')
                    YIELD graphName
                    RETURN graphName
                    """
                ).data()

                result["graph_removal"] = drop_result

        except Exception as e:
            # in case of errors, try to clean up the graph projection
            try:
                with store.conn.session() as session:
                    session.run(f"CALL gds.graph.drop('{graph_name}', false)")
            except Exception:
                pass

            result["error"] = str(e)

        # return results as json string
        return json.dumps(result, indent=2, ensure_ascii=False)


class CommonNeighborsExecutor(Tool):
    """Tool to execute the Common Neighbors algorithm on the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.execute_common_neighbors_algorithm.__name__,
            description=self.execute_common_neighbors_algorithm.__doc__ or "",
            function=self.execute_common_neighbors_algorithm,
        )

    async def execute_common_neighbors_algorithm(
        self,
        graph_db_service: GraphDbService,
        node1_id: str,
        node2_id: str,
        vertex_label: str = "*",
        relationship_type: Optional[str] = None,
        include_neighbor_details: bool = True,
    ) -> str:
        """Execute the Common Neighbors algorithm on the graph database.

        this function will:
        1. find the two nodes based on their IDs
        2. execute the common neighbors algorithm to count shared neighbors
        3. optionally retrieve details of the common neighbors

        example cypher queries executed (for nodes with PERSON labels):
        - execute common neighbors algorithm:
          MATCH (n1:PERSON {id: 'Romeo'})
          MATCH (n2:PERSON {id: 'Tybalt'})
          RETURN gds.alpha.linkprediction.commonNeighbors(n1, n2) AS commonNeighborsCount,
                 n1.name AS node1_name, n2.name AS node2_name

        - find common neighbors details (when relationship_type is specified):
          MATCH (n1 {id: 'Romeo'})-[:BELONGS_TO]-(common)-[:BELONGS_TO]-(n2 {id: 'Tybalt'})
          RETURN common.name AS neighbor_name, common.id AS neighbor_id, labels(common) AS neighbor_labels

        Args:
            node1_id (str): ID of the first node (e.g., 'Romeo').
            node2_id (str): ID of the second node (e.g., 'Tybalt').
            vertex_label (str): Label of nodes to include in calculation, "*" for all nodes.
            relationship_type (Optional[str]): Type of relationships to consider when finding common neighbors details.
            include_neighbor_details (bool): Whether to include details of the common neighbors.

        Returns:
            str: The result of the algorithm execution in JSON format.
        """  # noqa: E501
        store = graph_db_service.get_default_graph_db()
        result: Dict[str, Any] = {}

        try:
            with store.conn.session() as session:
                # step 1: get node details and common neighbors count
                node_label_clause = "" if vertex_label == "*" else f":{vertex_label}"

                common_neighbors_query = f"""
                MATCH (n1{node_label_clause} {{id: '{node1_id}'}})
                MATCH (n2{node_label_clause} {{id: '{node2_id}'}})
                RETURN 
                    gds.alpha.linkprediction.commonNeighbors(n1, n2) AS commonNeighborsCount,
                    n1.name AS node1_name, 
                    n1.id AS node1_id,
                    labels(n1) AS node1_labels,
                    n2.name AS node2_name, 
                    n2.id AS node2_id,
                    labels(n2) AS node2_labels
                """

                common_neighbors_result = session.run(common_neighbors_query).data()

                if not common_neighbors_result:
                    raise ValueError(
                        f"One or both nodes with IDs '{node1_id}' and '{node2_id}' not found"
                    )

                result["node_details"] = {
                    "node1": {
                        "name": common_neighbors_result[0].get("node1_name", "N/A"),
                        "id": common_neighbors_result[0].get("node1_id", "N/A"),
                        "labels": common_neighbors_result[0].get("node1_labels", []),
                    },
                    "node2": {
                        "name": common_neighbors_result[0].get("node2_name", "N/A"),
                        "id": common_neighbors_result[0].get("node2_id", "N/A"),
                        "labels": common_neighbors_result[0].get("node2_labels", []),
                    },
                }

                result["common_neighbors_count"] = common_neighbors_result[0].get(
                    "commonNeighborsCount", 0
                )

                # step 2: get common neighbors details if requested and relationship type is specified  # noqa: E501
                if include_neighbor_details and relationship_type:
                    rel_type = f":{relationship_type}"
                    neighbors_query = f"""
                    MATCH (n1 {{id: '{node1_id}'}})-[{rel_type}]-(common)-[{rel_type}]-(n2 {{id: '{node2_id}'}})
                    RETURN 
                        common.name AS neighbor_name, 
                        common.id AS neighbor_id, 
                        labels(common) AS neighbor_labels
                    ORDER BY neighbor_name
                    """  # noqa: E501

                    neighbors_details = session.run(neighbors_query).data()

                    # clean up result for better readability
                    cleaned_neighbors: List[Dict[str, Any]] = []
                    for record in neighbors_details:
                        cleaned_record = {
                            "name": record.get("neighbor_name", "N/A"),
                            "id": record.get("neighbor_id", "N/A"),
                            "labels": record.get("neighbor_labels", []),
                        }
                        cleaned_neighbors.append(cleaned_record)

                    result["common_neighbors"] = cleaned_neighbors

        except Exception as e:
            result["error"] = str(e)

        # return results as json string
        return json.dumps(result, indent=2, ensure_ascii=False)


class KMeansExecutor(Tool):
    """Tool to execute the K-Means clustering algorithm on the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.execute_kmeans_algorithm.__name__,
            description=self.execute_kmeans_algorithm.__doc__ or "",
            function=self.execute_kmeans_algorithm,
        )

    async def execute_kmeans_algorithm(
        self,
        graph_db_service: GraphDbService,
        vertex_label: str = "*",
        node_properties: Optional[List[str]] = None,
        k: int = 3,
        max_iterations: int = 20,
        seed: int = 42,
        top_n: int = 10,
    ) -> str:
        """Execute the K-Means clustering algorithm on the graph database.

        this function will:
        1. create a graph projection with the specified node labels and node properties
        2. execute the k-means algorithm to cluster nodes based on their properties
        3. retrieve node cluster assignments and centroids
        4. gather statistics about the algorithm execution and cluster distribution
        5. remove the graph projection

        example cypher queries executed (for a graph with Location nodes with latitude and longitude properties):
        - create projection:
          CALL gds.graph.project(
            'kmeans_graph_12345678',
            'Location',
            '*',
            {nodeProperties: ['latitude', 'longitude']}
          )
        - execute k-means algorithm:
          CALL gds.beta.kmeans.stream('kmeans_graph_12345678', {
            k: 3,
            maxIterations: 20,
            randomSeed: 42,
            nodeProperties: ['latitude', 'longitude']
          })
          YIELD nodeId, communityId
          WITH gds.util.asNode(nodeId) AS node, communityId
          RETURN node.name AS name, node.id AS id, labels(node) AS labels,
                 node.latitude AS latitude, node.longitude AS longitude, communityId
          ORDER BY communityId, name
          LIMIT 10
        - get statistics:
          CALL gds.beta.kmeans.stats('kmeans_graph_12345678', {k: 3, ...})
        - remove projection:
          CALL gds.graph.drop('kmeans_graph_12345678')

        Args:
            vertex_label (str): Label of nodes to include in clustering, "*" for all nodes.
            node_properties (List[str]): List of node properties to use as features for clustering. (only numeric properties)
            k (int): Number of clusters to create.
            max_iterations (int): Maximum number of iterations to run.
            seed (int): Random seed for initialization.
            top_n (int): Number of nodes to return per cluster.

        Returns:
            str: The result of the algorithm execution in JSON format.
        """  # noqa: E501
        store = graph_db_service.get_default_graph_db()
        # generate a unique name for the graph projection
        graph_name = f"kmeans_graph_{uuid4().hex[:8]}"

        # default to empty list if node_properties is None
        if node_properties is None:
            node_properties = []

        # convert node properties list to string for cypher query
        properties_str = str(node_properties).replace("'", '"')

        result: Dict[str, Any] = {}

        try:
            with store.conn.session() as session:
                # step 1: create graph projection with node properties
                projection_query = f"""
                CALL gds.graph.project(
                    '{graph_name}',
                    '{vertex_label}',
                    '*',
                    {{nodeProperties: {properties_str}}}
                )
                YIELD graphName, nodeCount, relationshipCount
                RETURN graphName, nodeCount, relationshipCount
                """

                result["graph_creation"] = session.run(projection_query).data()

                # step 2: build configuration for k-means
                config = f"""{{
                    k: {k},
                    maxIterations: {max_iterations},
                    randomSeed: {seed},
                    nodeProperties: {properties_str}
                }}"""

                # step 3: execute k-means algorithm
                kmeans_result = session.run(
                    f"""
                    CALL gds.beta.kmeans.stream('{graph_name}', {config})
                    YIELD nodeId, communityId
                    WITH gds.util.asNode(nodeId) AS node, communityId
                    RETURN 
                        node.name AS name, 
                        node.id AS id, 
                        labels(node) AS labels, 
                        communityId
                    ORDER BY communityId, name
                    LIMIT {top_n}
                    """
                ).data()

                # add node properties to the result if provided
                if node_properties:
                    # clean up result with properties
                    cleaned_result = []
                    for record in kmeans_result:
                        cleaned_record = {
                            "name": record.get("name", "N/A"),
                            "id": record.get("id", "N/A"),
                            "labels": record.get("labels", []),
                            "cluster_id": record.get("communityId"),
                            "properties": {},
                        }

                        # get node properties if available
                        node_props_result = session.run(
                            f"""
                            MATCH (n) WHERE n.id = '{cleaned_record["id"]}'
                            RETURN {", ".join([f"n.{prop} AS {prop}" for prop in node_properties])}
                            """
                        ).data()

                        if node_props_result:
                            for prop in node_properties:
                                cleaned_record["properties"][prop] = node_props_result[0].get(prop)

                        cleaned_result.append(cleaned_record)
                else:
                    # clean up result without properties
                    cleaned_result = []
                    for record in kmeans_result:
                        cleaned_record = {
                            "name": record.get("name", "N/A"),
                            "id": record.get("id", "N/A"),
                            "labels": record.get("labels", []),
                            "cluster_id": record.get("communityId"),
                        }
                        cleaned_result.append(cleaned_record)

                result["kmeans_results"] = cleaned_result

                # step 4: get cluster distribution statistics
                cluster_stats = session.run(
                    f"""
                    CALL gds.beta.kmeans.stream('{graph_name}', {config})
                    YIELD nodeId, communityId
                    RETURN 
                        communityId, 
                        count(*) AS clusterSize
                    ORDER BY clusterSize DESC
                    """
                ).data()

                result["cluster_stats"] = cluster_stats

                # step 5: get algorithm execution statistics
                stats = session.run(
                    f"""
                    CALL gds.beta.kmeans.stats('{graph_name}', {config})
                    YIELD preProcessingMillis, computeMillis, postProcessingMillis, k, didConverge, ranIterations
                    RETURN preProcessingMillis, computeMillis, postProcessingMillis, k, didConverge, ranIterations
                    """  # noqa: E501
                ).data()

                result["algorithm_stats"] = stats[0] if stats else {}

                # step 6: get centroids if node properties are provided
                if node_properties:
                    centroids = session.run(
                        f"""
                        CALL gds.beta.kmeans.stats('{graph_name}', {config})
                        YIELD centroids
                        RETURN centroids
                        """
                    ).data()

                    if centroids and centroids[0].get("centroids"):
                        result["centroids"] = centroids[0]["centroids"]

                # step 7: remove graph projection
                drop_result = session.run(
                    f"""
                    CALL gds.graph.drop('{graph_name}')
                    YIELD graphName
                    RETURN graphName
                    """
                ).data()

                result["graph_removal"] = drop_result

        except Exception as e:
            # in case of errors, try to clean up the graph projection
            try:
                with store.conn.session() as session:
                    session.run(f"CALL gds.graph.drop('{graph_name}', false)")
            except Exception:
                pass

            result["error"] = str(e)

        # return results as json string
        return json.dumps(result, indent=2, ensure_ascii=False)


# Added main function for testing ShortestPathExecutor
async def main():
    """Main function to test ShortestPathExecutor."""
    graph_db_service = None  # Initialize to None
    try:
        # Initialize services needed for the test
        # Assuming DbSession needs setup or can be default
        DaoFactory.initialize(DbSession())
        ServiceFactory.initialize()
        graph_db_service = GraphDbService.instance
        # Ensure the service is ready if it has an async init
        # await graph_db_service.initialize() # Uncomment if needed

        executor = ShortestPathExecutor()

        start_node_id = "Romeo"
        # end_node_id = "4:3641d659-da64-4b2a-8926-1377e9b7755a:2"
        end_node_id = "Juliet"
        vertex_label = "*"
        relationship_type = "*"
        weight_property = None
        path_details = True

        print(f"Executing shortest path from '{start_node_id}' to '{end_node_id}'...")

        result_json = await executor.execute_shortest_path_algorithm(
            graph_db_service=graph_db_service,
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            vertex_label=vertex_label,
            relationship_type=relationship_type,
            weight_property=weight_property,
            path_details=path_details,
        )
        print("\nExecution Result:")
        print(result_json)
    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")


if __name__ == "__main__":
    # Requires a running Neo4j instance with the sample graph data (e.g., Shakespeare)
    # and GDS plugin installed.
    # Ensure environment variables for Neo4j connection are set if GraphDbService uses them.
    print("Running Shortest Path Test...")
    asyncio.run(main())
