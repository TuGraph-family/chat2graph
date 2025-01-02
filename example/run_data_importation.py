import asyncio
import json
from typing import Optional
from uuid import uuid4

from dbgpt.storage.graph_store.tugraph_store import (  # type: ignore
    TuGraphStore,
    TuGraphStoreConfig,
)

from app.agent.job import Job
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.workflow.operator.operator import Operator, OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.toolkit import Toolkit, ToolkitService

EDGE_COUNT = 20

ROMANCE_OF_THE_THREE_KINGDOMS_CHAP_50 = """
第五十回

却说当夜张辽一箭射黄盖下水，救得曹操登岸，寻着马匹走时，军已大乱。韩当冒烟突火来攻水寨，忽听得士卒报道：“后梢舵上一人，高叫将军表字。”韩当细听，但闻高叫“义公救我？”当曰：“此黄公覆也！”急教救起。见黄盖负箭着伤，咬出箭杆，箭头陷在肉内。韩当急为脱去湿衣，用刀剜出箭头，扯旗束之，脱自己战袍与黄盖穿了，先令别船送回大寨医治。原来黄盖深知水性，故大寒之时，和甲堕江，也逃得性命。却说当日满江火滚，喊声震地。左边是韩当、蒋钦两军从赤壁西边杀来；右边是周泰、陈武两军从赤壁东边杀来；正中是周瑜、程普、徐盛、丁奉大队船只都到。火须兵应，兵仗火威。此正是：三江水战，赤壁鏖兵。曹军着枪中箭、火焚水溺者，不计其数。后人有诗曰：
 
魏吴争斗决雌雄，赤壁楼船一扫空。烈火初张照云海，周郎曾此破曹公。
 
又有一绝云：
 
山高月小水茫茫，追叹前朝割据忙。南士无心迎魏武，东风有意便周郎。
 
不说江中鏖兵。且说甘宁令蔡中引入曹寨深处，宁将蔡中一刀砍于马下，就草上放起火来。吕蒙遥望中军火起，也放十数处火，接应甘宁。潘璋、董袭分头放火呐喊，四下里鼓声大震。曹操与张辽引百余骑，在火林内走，看前面无一处不着。正走之间，毛玠救得文聘，引十数骑到。操令军寻路。张辽指道：“只有乌林地面，空阔可走。”操径奔乌林。正走间，背后一军赶到，大叫：“曹贼休走！”火光中现出吕蒙旗号。操催军马向前，留张辽断后，抵敌吕蒙。却见前面火把又起，从山谷中拥出一军，大叫：“凌统在此！”曹操肝胆皆裂。忽刺斜里一彪军到，大叫：“丞相休慌！徐晃在此！”彼此混战一场，夺路望北而走。忽见一队军马，屯在山坡前。徐晃出问，乃是袁绍手下降将马延、张顗，有三千北地军马，列寨在彼；当夜见满天火起，未敢转动，恰好接着曹操。操教二将引一千军马开路，其余留着护身。操得这枝生力军马，心中稍安。马延、张顗二将飞骑前行。不到十里，喊声起处，一彪军出。为首一将，大呼曰：“吾乃东吴甘兴霸也！”马延正欲交锋，早被甘宁一刀斩于马下；张顗挺枪来迎，宁大喝一声，顗措手不及，被宁手起一刀，翻身落马。后军飞报曹操。操此时指望合淝有兵救应；不想孙权在合淝路口，望见江中火光，知是我军得胜，便教陆逊举火为号，太史慈见了，与陆逊合兵一处，冲杀将来。操只得望彝陵而走。路上撞见张郃，操令断后。
 
纵马加鞭，走至五更，回望火光渐远，操心方定，问曰：“此是何处？”左右曰：“此是乌林之西，宜都之北。”操见树木丛杂，山川险峻，乃于马上仰面大笑不止。诸将问曰：“丞相何故大笑？”操曰：“吾不笑别人，单笑周瑜无谋，诸葛亮少智。若是吾用兵之时，预先在这里伏下一军，如之奈何？”说犹未了，两边鼓声震响，火光竟天而起，惊得曹操几乎坠马。刺斜里一彪军杀出，大叫：“我赵子龙奉军师将令，在此等候多时了！”操教徐晃、张郃双敌赵云，自己冒烟突火而去。子龙不来追赶，只顾抢夺旗帜。曹操得脱。
 
天色微明，黑云罩地，东南风尚不息。忽然大雨倾盆，湿透衣甲。操与军士冒雨而行，诸军皆有饥色。操令军士往村落中劫掠粮食，寻觅火种。方欲造饭，后面一军赶到。操心甚慌。原来却是李典、许褚保护着众谋士来到，操大喜，令军马且行，问：“前面是那里地面？”人报：“一边是南彝陵大路，一边是北彝陵山路。”操问：“那里投南郡江陵去近？”军士禀曰：“取南彝陵过葫芦口去最便。”操教走南彝陵。行至葫芦口，军皆饥馁，行走不上，马亦困乏，多有倒于路者。操教前面暂歇。马上有带得锣锅的，也有村中掠得粮米的，便就山边拣干处埋锅造饭，割马肉烧吃。尽皆脱去湿衣，于风头吹晒；马皆摘鞍野放，咽咬草根。操坐于疏林之下，仰面大笑。众官问曰：“适来丞相笑周瑜、诸葛亮，引惹出赵子龙来，又折了许多人马。如今为何又笑？”操曰：“吾笑诸葛亮、周瑜毕竟智谋不足。若是我用兵时，就这个去处，也埋伏一彪军马，以逸待劳；我等纵然脱得性命，也不免重伤矣。彼见不到此，我是以笑之。”正说间，前军后军一齐发喊、操大惊，弃甲上马。众军多有不及收马者。早见四下火烟布合，山口一军摆开，为首乃燕人张翼德，横矛立马，大叫：“操贼走那里去！”诸军众将见了张飞，尽皆胆寒。许褚骑无鞍马来战张飞。张辽、徐晃二将，纵马也来夹攻。两边军马混战做一团。操先拨马走脱，诸将各自脱身。张飞从后赶来。操迤逦奔逃，追兵渐远，回顾众将多已带伤。
 
正行时，军士禀曰：“前面有两条路，请问丞相从那条路去？”操问：“那条路近？”军士曰：“大路稍平，却远五十余里。小路投华容道，却近五十余里；只是地窄路险，坑坎难行。”操令人上山观望，回报：“小路山边有数处烟起；大路并无动静。”操教前军便走华容道小路。诸将曰：“烽烟起处，必有军马，何故反走这条路？”操曰：“岂不闻兵书有云：虚则实之，实则虚之。诸葛亮多谋，故使人于山僻烧烟，使我军不敢从这条山路走，他却伏兵于大路等着。吾料已定，偏不教中他计！”诸将皆曰：“丞相妙算，人不可及。”遂勒兵走华容道。此时人皆饥倒，马尽困乏。焦头烂额者扶策而行，中箭着枪者勉强而走。衣甲湿透，个个不全；军器旗幡，纷纷不整：大半皆是彝陵道上被赶得慌，只骑得秃马，鞍辔衣服，尽皆抛弃。正值隆冬严寒之时，其苦何可胜言。
 
操见前军停马不进，问是何故。回报曰：“前面山僻路小，因早晨下雨，坑堑内积水不流，泥陷马蹄，不能前进。”操大怒，叱曰：“军旅逢山开路，遇水叠桥，岂有泥泞不堪行之理！”传下号令，教老弱中伤军士在后慢行，强壮者担土束柴，搬草运芦，填塞道路。务要即时行动，如违令者斩。众军只得都下马，就路旁砍伐竹木，填塞山路。操恐后军来赶，令张辽、许褚、徐晃引百骑执刀在手，但迟慢者便斩之。此时军已饿乏，众皆倒地，操喝令人马践踏而行，死者不可胜数。号哭之声，于路不绝。操怒曰：“生死有命，何哭之有！如再哭者立斩！”三停人马：一停落后，一停填了沟壑，一停跟随曹操。过了险峻，路稍平坦。操回顾止有三百余骑随后，并无衣甲袍铠整齐者。操催速行。众将曰：“马尽乏矣，只好少歇。”操曰：“赶到荆州将息未迟。”又行不到数里，操在马上扬鞭大笑。众将问：“丞相何又大笑？”操曰：“人皆言周瑜、诸葛亮足智多谋，以吾观之，到底是无能之辈。若使此处伏一旅之师，吾等皆束手受缚矣。”
 
言未毕，一声炮响，两边五百校刀手摆开，为首大将关云长，提青龙刀，跨赤兔马，截住去路。操军见了，亡魂丧胆，面面相觑。操曰：“既到此处，只得决一死战！”众将曰：“人纵然不怯，马力已乏，安能复战？”程昱曰：“某素知云长傲上而不忍下，欺强而不凌弱；恩怨分明，信义素著。丞相旧日有恩于彼，今只亲自告之，可脱此难。”操从其说，即纵马向前，欠身谓云长曰：“将军别来无恙！”云长亦欠身答曰：“关某奉军师将令，等候丞相多时。”操曰：“曹操兵败势危，到此无路，望将军以昔日之情为重。”云长曰：“昔日关某虽蒙丞相厚恩，然已斩颜良，诛文丑，解白马之围，以奉报矣。今日之事，岂敢以私废公？”操曰：“五关斩将之时，还能记否？大丈夫以信义为重。将军深明《春秋》，岂不知庾公之斯追子濯孺子之事乎？”云长是个义重如山之人，想起当日曹操许多恩义，与后来五关斩将之事，如何不动心？又见曹军惶惶，皆欲垂泪，一发心中不忍。于是把马头勒回，谓众军曰：“四散摆开。”这个分明是放曹操的意思。操见云长回马，便和众将一齐冲将过去。云长回身时，曹操已与众将过去了。云长大喝一声，众军皆下马，哭拜于地。云长愈加不忍。正犹豫间，张辽纵马而至。云长见了，又动故旧之情，长叹一声，并皆放去。后人有诗曰：
 
曹瞒兵败走华容，正与关公狭路逢。只为当初恩义重，放开金锁走蛟龙。
 
曹操既脱华容之难。行至谷口，回顾所随军兵，止有二十七骑。比及天晚，已近南郡，火把齐明，一簇人马拦路。操大惊曰：“吾命休矣！”只见一群哨马冲到，方认得是曹仁军马。操才心安。曹仁接着，言：“虽知兵败，不敢远离，只得在附近迎接。”操曰：“几与汝不相见也！”于是引众入南郡安歇。随后张辽也到，说云长之德。操点将校，中伤者极多，操皆令将息。曹仁置酒与操解闷。众谋士俱在座。操忽仰天大恸。众谋士曰：“丞相于虎窟中逃难之时，全无惧怯；今到城中，人已得食，马已得料，正须整顿军马复仇，何反痛哭？”操曰：“吾哭郭奉孝耳！若奉孝在，决不使吾有此大失也！”遂捶胸大哭曰：“哀哉，奉孝！痛哉，奉孝！惜哉！奉孝！”众谋士皆默然自惭。
 
次日，操唤曹仁曰：“吾今暂回许都，收拾军马，必来报仇。汝可保全南郡。吾有一计，密留在此，非急休开，急则开之。依计而行，使东吴不敢正视南郡。”仁曰：“合淝、襄阳，谁可保守？”操曰：“荆州托汝管领；襄阳吾已拨夏侯惇守把；合淝最为紧要之地，吾令张辽为主将，乐进、李典为副将，保守此地。但有缓急，飞报将来。”操分拨已定，遂上马引众奔回许昌。荆州原降文武各官，依旧带回许昌调用。曹仁自遣曹洪据守彝陵、南郡，以防周瑜。
 
却说关云长放了曹操，引军自回。此时诸路军马，皆得马匹、器械、钱粮，已回夏口；独云长不获一人一骑，空身回见玄德。孔明正与玄德作贺，忽报云长至。孔明忙离坐席，执杯相迎曰：“且喜将军立此盖世之功，与普天下除大害。合宜远接庆贺！”云长默然。孔明曰：“将军莫非因吾等不曾远接，故尔不乐？”回顾左右曰：“汝等缘何不先报？”云长曰：“关某特来请死。”孔明曰：“莫非曹操不曾投华容道上来？”云长曰：“是从那里来。关某无能，因此被他走脱。”孔明曰：“拿得甚将士来？”云长曰：“皆不曾拿。”孔明曰：“此是云长想曹操昔日之恩，故意放了。但既有军令状在此，不得不按军法。”遂叱武士推出斩之。正是：
 
拚将一死酬知己，致令千秋仰义名。

"""


def get_tugraph(
    config: Optional[TuGraphStoreConfig] = None,
) -> TuGraphStore:
    """initialize tugraph store with configuration.

    args:
        config: optional tugraph store configuration

    returns:
        initialized tugraph store instance
    """
    try:
        if not config:
            config = TuGraphStoreConfig(
                name="default_graph",
                host="127.0.0.1",
                port=7687,
                username="admin",
                password="73@TuGraph",
            )

        # initialize store
        store = TuGraphStore(config)

        # ensure graph exists
        print(f"[log] get graph: {config.name}")
        store.conn.create_graph(config.name)

        return store

    except Exception as e:
        print(f"failed to initialize tugraph: {str(e)}")
        raise


class DocumentReader(Tool):
    """Tool for analyzing document content."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.read_document.__name__,
            description=self.read_document.__doc__ or "",
            function=self.read_document,
        )

    async def read_document(self, doc_name: str, chapter_name: str) -> str:
        """Read the document content given the document name and chapter name.

        Args:
            doc_name (str): The name of the document.
            chapter_name (str): The name of the chapter of the document.

        Returns:
            The content of the document.
        """

        return ROMANCE_OF_THE_THREE_KINGDOMS_CHAP_50


class SchemaGetter(Tool):
    """Tool for getting the schema of a graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.get_schema.__name__,
            description=self.get_schema.__doc__ or "",
            function=self.get_schema,
        )

    async def get_schema(self) -> str:
        """Get the schema of a graph database.

        Args:
            None args required

        Returns:
            str: The schema of the graph database in string format

        Example:
            schema_str = get_schema()
        """
        query = "CALL dbms.graph.getGraphSchema()"
        sstore = get_tugraph()
        schema = sstore.conn.run(query=query)

        result = f"参考{SCHEMA_TEMPLATE}进行理解，以下图模型：\n" + json.dumps(
            json.loads(schema[0][0])["schema"], indent=4, ensure_ascii=False
        )

        return result


class NodesToCypher(Tool):
    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.nodes_to_cypher_create.__name__,
            description=self.nodes_to_cypher_create.__doc__ or "",
            function=self.nodes_to_cypher_create,
        )

    def nodes_to_cypher_create(self, nodes):
        """Generate a instruction CREATE statement to create nodes in a TuGraph database.

        Parameters:
            nodes (list of dict): A list of dictionaries, where each dictionary represents a node and contains the following keys:
                - "label" (str): The label (type) of the node.
                - "properties" (dict): The properties of the node, represented as key-value pairs.

        Returns:
            list: A list containing a single instruction CREATE statement to create all the provided nodes.

        Example:
            Input:
                nodes = [
                    {"label": "Person", "properties": {"name": "Alice", "age": 30}},
                    {"label": "Person", "properties": {"name": "Bob", "age": 25}}
                ]

            Output:
                ["CREATE (:Person { name: 'Alice', age: '30' }), (:Person { name: 'Bob', age: '25' })"]
        """
        node_statements = []
        for node in nodes:
            node_type = node["label"]
            properties = node["properties"]
            property_str = ",".join(
                f"{key}: '{value}'" for key, value in properties.items()
            )
            node_statement = f"(:{node_type} {{ {property_str} }})"
            node_statements.append(node_statement)

        cypher_statement = f"CREATE {', '.join(node_statements)}"
        db = get_tugraph()
        res = db.conn.run(cypher_statement)
        return res


class EdgesToCypher(Tool):
    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.edges_to_cypher_create.__name__,
            description=self.edges_to_cypher_create.__doc__ or "",
            function=self.edges_to_cypher_create,
        )

    def edges_to_cypher_create(self, edges):
        """Generate instruction statements to create edges in a TuGraph database using the `db.upsertEdge` procedure.

        Parameters:
            edges (list of dict): A list of dictionaries, where each dictionary represents an edge and contains the following keys:
                - "label" (str): The label (type) of the edge.
                - "constraints" (list of lists): A list containing a single list with two elements, representing the types of the source and target nodes.
                Example: [["Person", "Movie"]] indicates that the source node is of type "Person" and the target node is of type "Movie".
                - "source" (str): The identifier (primary key value) of the source node.
                - "target" (str): The identifier (primary key value) of the target node.
                - "properties" (dict): The properties of the edge, represented as key-value pairs.

        Returns:
            list: A list of instruction statements, each calling the `db.upsertEdge` procedure to create the specified edges.

        Example:
            Input:
                edges = [
                    {
                        "label": "ACTED_IN",
                        "constraints": [["Person", "Movie"]],
                        "source": "Alice",
                        "target": "TheMatrix",
                        "properties": {"role": "Hero"}
                    },
                    {
                        "label": "DIRECTED",
                        "constraints": [["Person", "Movie"]],
                        "source": "Wachowski",
                        "target": "TheMatrix",
                        "properties": {"year": 1999}
                    }
                ]

            Output:
                [
                    "CALL db.upsertEdge('ACTED_IN', {type: 'Person', key: 'source'}, {type: 'Movie', key: 'target'}, [{ role: 'Hero', source: 'Alice', target: 'TheMatrix' }])",
                    "CALL db.upsertEdge('DIRECTED', {type: 'Person', key: 'source'}, {type: 'Movie', key: 'target'}, [{ year: '1999', source: 'Wachowski', target: 'TheMatrix' }])"
                ]
        """
        edge_types = {}
        db = get_tugraph()
        result_list = []
        for edge in edges:
            edge_type = edge["label"]
            if edge_type not in edge_types:
                edge_types[edge_type] = []
            edge_types[edge_type].append(edge)

        for edge_type, edges_list in edge_types.items():
            properties_str_list = []
            for edge in edges_list:
                properties = edge["properties"]
                properties["source"] = edge["source"]
                properties["target"] = edge["target"]
                property_str = ",".join(
                    f"{key}: '{value}'" for key, value in properties.items()
                )
                properties_str_list.append(f"{{ {property_str} }}")
            source_type, target_type = (
                edge["constraints"][0][0],
                edge["constraints"][0][1],
            )
            properties_str = ",".join(properties_str_list)
            cypher_statement = f"CALL db.upsertEdge('{edge_type}', {{type: '{source_type}', key: 'source'}}, {{type: '{target_type}', key: 'target'}}, [{properties_str}])"
            res = db.conn.run(cypher_statement)
            result_list.append(res)
        return result_list


SCHEMA_TEMPLATE = """
{
  "schema": [
    {
      "label": "实体类型",
      "primary": "实体属性",
      "properties": [
        {
          "name": "实体属性",
          "optional": false,
          "type": "STRING"
        },
        // ... 更多实体属性
      ],
      "type": "VERTEX"
    },
    // ... 更多实体类型
    {
      "constraints": [
        [
          "实体类型",
          "实体类型"
        ]
      ],
      "detach_property": true,
      "label": "关系类型",
      "properties": [
        {
          "name": "关系属性",
          "optional": true,
          "type": "STRING"
        },
        // ... 更多关系属性
      ],
      "type": "EDGE"
    },
    // // ... 更多关系类型
  ]
}
"""
# operation 1: Data Generation
DATA_GENERATION_PROFILE = """
你是一位资深的图数据抽取专家。
你的使命是，基于已分析的文档内容和图模型，精准地抽取关键信息，为构建知识图谱提供坚实的数据基础。
在这一阶段，你不是在创造知识，而是在发掘隐藏在文档中的事实。
你的目标是从文本中提取实体、关系和属性，请确保数据的准确、丰富、完整，因为后续的知识图谱构建将直接依赖于你抽取的数据质量。
"""

DATA_GENERATION_OUTPUT_DATA = """
{
    "entities":[
        {
            "label":"实体类型",
            "properties":{
                "实体属性":"属性值",
                // ...更多实体属性
            }
        }
        // ...更多实体
    ],
    "relationships":[
        {
            "label":"关系类型",
            "constraints": [
                ["实体类型","实体类型"]
            ],
            "source":"primary对应的实体属性的值",  
            "target":"primary对应的实体属性的值",
            "properties":{
                "关系属性":"属性值",
                // ...更多关系属性
            }           
        },
        // ... 更多关系
    ]
}
"""

DATA_GENERATION_INSTRUCTION = f"""
请安以下要求完成任务：
1. 理解图模型
2. 理解文本信息
3. 根据图模型和文本信息抽取关系数据，关系数据不能少于{EDGE_COUNT}条, 并确保抽取的关系数据属性与对应关系类型的属性一一对应。
4. 根据抽取出的关系数据、图模型和文本信息抽取实体数据，确保抽取的实体数据属性与对应实体类型的属性一一对应，并且要保证这些实体是从关系数据中得到的。
5. 严格按照{DATA_GENERATION_OUTPUT_DATA}格式，输出数据
"""


def get_data_generation_operator():
    analysis_toolkit = Toolkit()
    schema_understanding_action = Action(
        id="data_generattion.schema_understanding",
        name="图模型理解",
        description="调用相关工具获取真实图模型，并理解图模型结构",
    )
    content_understanding_action = Action(
        id="data_generattion.content_understanding",
        name="文本内容理解",
        description="调用相关工具, 结合图模型, 对文本内容进行充分理解和解析",
    )
    edge_data_generation_action = Action(
        id="data_generattion.edge_data_generation_action",
        name="关系数据抽取",
        description="根据对图模型理解和文本内容理解的理解，进行关系数据的抽取，输出的格式要严格符合输出模板",
    )
    node_data_generation_action = Action(
        id="data_generattion.node_data_generation_action",
        name="实体数据抽取",
        description="根据关系数据，图模型和文本内容，进行实体数据的抽取，输出的格式要严格符合输出模板",
    )

    graph_data_generation_action = Action(
        id="data_generattion.graph_data_generation_action",
        name="图数据输出",
        description="严格按照输出格式输出数据",
    )
    analysis_toolkit.add_action(
        action=schema_understanding_action,
        next_actions=[(content_understanding_action, 1)],
        prev_actions=[],
    )
    analysis_toolkit.add_action(
        action=content_understanding_action,
        next_actions=[(edge_data_generation_action, 1)],
        prev_actions=[(schema_understanding_action, 1)],
    )
    analysis_toolkit.add_action(
        action=edge_data_generation_action,
        next_actions=[(node_data_generation_action, 1)],
        prev_actions=[(content_understanding_action, 1)],
    )

    analysis_toolkit.add_action(
        action=node_data_generation_action,
        next_actions=[(graph_data_generation_action, 1)],
        prev_actions=[(edge_data_generation_action, 1)],
    )

    analysis_toolkit.add_action(
        action=graph_data_generation_action,
        next_actions=[],
        prev_actions=[(node_data_generation_action, 1)],
    )

    get_schema = SchemaGetter(id="get_schema_tool")
    analysis_toolkit.add_tool(
        tool=get_schema, connected_actions=[(schema_understanding_action, 1)]
    )

    get_document = DocumentReader(id="get_document_tool")
    analysis_toolkit.add_tool(
        tool=get_document, connected_actions=[(content_understanding_action, 1)]
    )

    operator_config = OperatorConfig(
        id="data_generation_operator",
        instruction=DATA_GENERATION_PROFILE + DATA_GENERATION_INSTRUCTION,
        output_schema=DATA_GENERATION_OUTPUT_DATA,
        actions=[
            schema_understanding_action,
            content_understanding_action,
            edge_data_generation_action,
            node_data_generation_action,
            graph_data_generation_action,
        ],
    )
    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=analysis_toolkit),
    )

    return operator


# operation 2: Data Import
DATA_IMPORT_PROFILE = """
你是一位资深的图数据库的管理员。
你的使命是，将标准的json结构化文本，转换成可执行的导入命令。
你的目标是执行这些命令，完成数据的导入。
"""

DATA_IMPORT_OUTPUT_DATA = """
{
    result:"导入的结果，成功导入点边数量，点边导入失败的数量，失败的原因。"
}
"""

DATA_IMPORT_INSTRUCTION = """
请安以下要求完成任务：
1. 导入数据，将json文本数据，准成对应的导入命令，并执行导入
2. 输出数据导入结果
"""


def get_import_data_operator():
    analysis_toolkit = Toolkit()
    json_to_cypher_action = Action(
        id="data_import.json_to_cypher",
        name="数据导入",
        description="调用相关工具，将json数据转换成导入命令，并执行对应命令",
    )
    output_result_action = Action(
        id="data_import.output_result",
        name="输出结果",
        description="输出数据导入的结果",
    )

    analysis_toolkit.add_action(
        action=json_to_cypher_action,
        next_actions=[(output_result_action, 1)],
        prev_actions=[],
    )

    analysis_toolkit.add_action(
        action=output_result_action,
        next_actions=[],
        prev_actions=[(json_to_cypher_action, 1)],
    )

    nodes_to_cypher = NodesToCypher(id="nodes_to_cypher")
    analysis_toolkit.add_tool(
        tool=nodes_to_cypher, connected_actions=[(json_to_cypher_action, 1)]
    )

    edges_to_cypher = EdgesToCypher(id="edges_to_cypher")
    analysis_toolkit.add_tool(
        tool=edges_to_cypher, connected_actions=[(json_to_cypher_action, 1)]
    )

    operator_config = OperatorConfig(
        id="import_data_operator",
        instruction=DATA_IMPORT_PROFILE + DATA_IMPORT_INSTRUCTION,
        output_schema=DATA_IMPORT_OUTPUT_DATA,
        actions=[json_to_cypher_action, output_result_action],
    )
    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=analysis_toolkit),
    )

    return operator


def get_workflow():
    """Get the workflow for graph modeling and assemble the operators."""
    data_generation_operator = get_data_generation_operator()
    data_import_operator = get_import_data_operator()
    workflow = DbgptWorkflow()
    workflow.add_operator(
        operator=data_generation_operator,
        previous_ops=[],
        next_ops=[data_import_operator],
    )
    workflow.add_operator(
        operator=data_import_operator,
        previous_ops=[data_generation_operator],
        next_ops=[],
    )

    return workflow


async def main():
    """Main function to run the data import."""
    workflow = get_workflow()
    job = Job(
        id="test_job_id",
        session_id="test_session_id",
        goal="「任务」",
        context="目前我们的问题的背景是，根据用户提供的内容和当前图数据库中的图模型完成实体和关系的数据抽取，执行数据的导入，并输出导入结果",
    )
    reasoner = DualModelReasoner()

    result = await workflow.execute(job=job, reasoner=reasoner)

    print(f"Final result:\n{result.scratchpad}")


if __name__ == "__main__":
    asyncio.run(main())
