import json
import time
from typing import Dict, List, Optional, Set, Union
from uuid import uuid4

from app.core.agent.agent import AgentConfig, Profile
from app.core.common.system_env import SystemEnv
from app.core.model.message import ModelMessage
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.reasoner.model_service_factory import ModelServiceFactory
from app.core.reasoner.reasoner import Reasoner
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool
from app.core.toolkit.toolkit import Toolkit, ToolkitService
from app.core.workflow.operator import Operator, OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from app.plugin.tugraph.tugraph_store import get_tugraph

CYPHER_GRAMMER = """
===== TuGraph Cypher 语法书 =====

createVertexLabelByJson 命令用于创建顶点标签，基本语法：

```
CALL db.createVertexLabelByJson('{
    "label": "标签名",
    "primary": "主键字段名",
    "type": "VERTEX",
    "properties": [
        {
            "name": "字段名",
            "type": "字段类型",
            "optional": True/False,
            "index": True/False,
        }
        // ... 更多属性
    ]
}');
```

createEdgeLabelByJson 命令用于创建边标签，基本语法：

```
CALL db.createEdgeLabelByJson('{
    "label": "边标签名",
    "type": "EDGE",
    "properties": [
        {
            "name": "type",
            "type": "STRING",
            "optional": False,
        },
        // ... 更多属性
    ],
    "constraints": [
        ["源实体标签名", "目标实体标签名"],
    ]
}');
```

关键参数说明：

1. 顶点标签必填字段：
   - label: 节点标签名
   - primary: 主键字段名
   - type: 必须为 "VERTEX"
   - properties: 至少包含主键属性

2. 边标签必填字段：
   - label: 边标签名
   - type: 必须为 "EDGE"
   - properties: 至少包含主键属性

属性定义规则：
- name: 属性名
- type: 属性类型（见下方支持的数据类型）
- optional: 是否可选（True/False）
- index: 是否建立索引（可选参数）(字符串字段如果需要查询，建议设置 index: True)

支持的数据类型：
- 整数类型：INT8, INT16, INT32, INT64
- 浮点类型：FLOAT, DOUBLE
- 其他类型：STRING, BOOL, DATE, DATETIME

重要注意事项：

1. 格式要求：
   - JSON 必须用单引号包裹
   - 所有字符串值使用双引号
   - 标签名和字段名不能包含特殊字符

2. 字段规则：
   - 主键字段必须设置 optional: False

=====
"""

# operation 1: Document Analysis
DOC_ANALYSIS_PROFILE = """
你是一位专业的文档分析专家，专注于从文档中提取关键信息，为知识图谱的构建奠定坚实基础。
你需要理解文档内容。请注意，你分析的文档可能只是全集的一个子集，需要通过局部推断全局。
请注意，你的任务不是需要操作图数据库。你的任务是分析文档，为后续的 knowledge graph modeling 提供重要信息。
"""  # noqa: E501

DOC_ANALYSIS_INSTRUCTION = """
请仔细阅读给定的文档，并按以下要求完成任务：

1. 语义层分析
   - 显式信息（比如，关键词、主题、术语定义）
   - 隐式信息（比如，深层语义、上下文关联、领域映射）

2. 关系层分析  
   - 实体关系（比如，直接关系、间接关系、层次关系）。时序关系（比如，状态变迁、演化规律、因果链条）

3. 知识推理
   - 模式推理、知识补全

请确保你的分析全面、细致，并为每一个结论提供充分的理由。
"""

DOC_ANALYSIS_OUTPUT_SCHEMA = """
{
    "domain": "文档所属领域的详细描述，解释该领域的主要业务和数据特点",
    "data_full_view": "对文档数据全貌的详细推测，包括数据结构、规模、实体关系等，并提供思考链路和理由",
    "concepts": [
        {"concept": "概念名称", "description": "概念的详细描述", "importance": "概念在文档中的重要性"},
        ...
    ],
    "properties": [
        {"concept": "所属概念", "property": "属性名称", "description": "属性的详细描述", "data_type": "属性的数据类型"},
        ...
    ],
    "potential_relations": [
        {"relation": "关系类型", "entities_involved": ["实体1", "实体2", ...], "description": "关系的详细描述", "strength": "关系的强度或重要性"},
        ...
    ],
    "document_insights": "其他重要（多条）信息或（多个）发现，它们独属于本文档的特殊内容，请用分号隔开。",
    "document_snippets": "文档中的关键片段，用于支撑你的分析结论，提供上下文信息。",
}
"""  # noqa: E501

# operation 2: Concept Modeling
CONCEPT_MODELING_PROFILE = """
你是一位知识图谱建模专家，擅长将概念和关系转化为图数据库模式。你需要设计合适的实体-关系模型，然后操作图数据库，确保任务的顺利完成。
"""

CONCEPT_MODELING_INSTRUCTION = """
你应该基于文档分析的结果，完成概念建模的任务，同时确保图建模的正确性和可达性。

1. 实体类型定义
- 从以下维度思考和定义实体类型：
  * 时间维度：事件、时期、朝代等时序性实体
  * 空间维度：地点、区域、地理特征等空间性实体
  * 社会维度：人物、组织、势力等社会性实体（可选）
  * 文化维度：思想、文化、典故等抽象实体（可选）
  * 物理维度：物品、资源、建筑等具象实体（可选）
- 建立实体类型的层次体系：
  * 定义上下位关系（如：人物-君主-诸侯）
  * 确定平行关系（如：军事人物、政治人物、谋士）
  * 设计多重继承关系（如：既是军事人物又是谋士）
- 为每个实体类型设计丰富的属性集：
  * 基础属性：标识符、名称、描述等
  * 类型特有属性：根据实体类型特点定义
  * 关联属性：引用其他实体的属性
- 考虑实体的时态性：
  * 属性的时效性（如：官职随时间变化）（可选）
  * 状态的可变性（如：阵营的转变）（可选）
- 为每个实体类型定义完整的属性集，包括必需属性和可选属性
- 确保实体类型之间存在潜在的关联路径，但保持概念边界的独立性

2. 关系类型设计
- 定义实体间的关系类型，包括直接关系、派生关系和潜在关系
- 明确关系的方向性（有向）、设计关系的属性集
- 通过关系组合，验证关键实体间的可达性
- （可选）考虑添加反向关系以增强图的表达能力

3. Schema生成
- 使用 graph schema creator 的函数，可以使用该函数生成 schema，为 vertex 和 edge 创建特殊的 schema。你不能直接写 cypher 语句，而是使用工具函数来帮助你操作数据库。
- 请注意：Schema 不是在 DB 中插入节点、关系等具体的数据，而是定义图数据库的模式（schema/label）。预期应该是定义是实体的类型、关系的类型、约束等这些东西。
- 任务的背景是知识图谱，所以，不要具体的某个实体，而是相对通用的实体。比如，可以从时间、抽象概念、物理实体和社会实体等多个主要维度来考虑。
- 需要多次读取 TuGraph 现有的 Schema，目的是确保根据 DDL 创建的 schema 符合预期。

4. 验证图的可达性
- 可达性是图数据库的核心特性之一，确保图中的实体和关系之间存在有效的连接路径，以支持复杂的查询需求。这在图建模中很重要，因为如果图不可达，将无法在构建一个完整的知识图谱。
- 通过查询图数据库，获取图的结构信息，验证实体和关系的可达性。
"""  # noqa: E501

CONCEPT_MODELING_OUTPUT_SCHEMA = """
{
    "reachability": "说明实体和关系之间的可达性，是否存在有效的连接路径",
    "stauts": "模型状态，是否通过验证等",
    "entity_label": "成功创建的实体标签",
    "relation_label": "成功创建的关系标签",
}
"""

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


class VertexLabelGenerator(Tool):
    """Tool for generating Cypher statements to create vertex labels in TuGraph."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.create_vertex_label_by_json_schema.__name__,
            description=self.create_vertex_label_by_json_schema.__doc__ or "",
            function=self.create_vertex_label_by_json_schema,
        )

    async def create_vertex_label_by_json_schema(
        self,
        label: str,
        primary: str,
        properties: List[Dict[str, Union[str, bool]]],
    ) -> str:
        """Generate a TuGraph vertex label statement, and then operator the TuGraph database to
        create the labels in the database.
        Field names can only contain letters, numbers, and underscores.

        Args:
            label (str): The name of the vertex label to create
            primary (str): The name of the primary key field
            properties (List[Dict]): List of property definitions, each containing:
                - name (str): Property name
                - type (str): Property type (e.g., 'STRING', 'INT32', 'DOUBLE', 'BOOL', 'DATE',
                    'DATETIME', do not support 'LIST' and 'MAP')
                - optional (bool): Whether the property is optional
                - index (bool, optional): Whether to create an index
                And make sure the primary key occurs in the properties list and is not optional.

        Returns:
            str: The complete Cypher statement for creating the edge label, and it's result.

        Example:
            properties = [
                {
                    "name": "id",
                    "type": "STRING",
                    "optional": False,
                    "index": True,
                },
                {
                    "name": "name",
                    "type": "STRING",
                    "optional": True
                },
                // Add more properties as needed
            ]
            execution_result = create_vertex_label_by_json_schema("Person", "id", properties)
        """
        # Validate primary key exists in properties
        primary_prop = next((p for p in properties if p["name"] == primary), None)
        if not primary_prop or primary_prop.get("optional", False):
            properties.append(
                {
                    "name": primary,
                    "type": "STRING",
                    "optional": False,
                }
            )

        # Prepare the JSON structure
        label_json = {
            "label": label,
            "primary": primary,
            "type": "VERTEX",
            "properties": properties,
        }

        # Generate the Cypher statement
        cypher_exec = CypherExecutor()
        return await cypher_exec.validate_and_execute_cypher(
            f"CALL db.createVertexLabelByJson('{json.dumps(label_json)}')"
        )


class EdgeLabelGenerator(Tool):
    """Tool for generating Cypher statements to create edge labels in TuGraph."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.create_edge_label_by_json_schema.__name__,
            description=self.create_edge_label_by_json_schema.__doc__ or "",
            function=self.create_edge_label_by_json_schema,
        )

    async def create_edge_label_by_json_schema(
        self,
        label: str,
        primary: str,
        properties: List[Dict[str, Union[str, bool]]],
        constraints: List[List[str]],
    ) -> str:
        """Generate a TuGraph edge label statement, and then operator the TuGraph database to create
        the labels in the database.
        Field names can only contain letters, numbers, and underscores. The value of the parameters
        should be in English.

        Args:
            label (str): The name of the edge label to create
            primary (str): The name of the primary key field
            properties (List[Dict]): List of property definitions, each containing:
                - name (str): Property name
                - type (str): Property type (e.g., 'STRING', 'INT32')
                - optional (bool): Whether the property is optional
            constraints (List[List[str]]): List of source and target vertex label constraints, which
            presents the direction of the edge.
                It can configure multiple source and target vertex label constraints,
                for example, [["source label", "target label"], ["other source label", "other target
                    label"]]

        Returns:
            str: The complete Cypher statement for creating the edge label, and it's result.

        Example:
            properties = [
                {
                    "name": "type",
                    "type": "STRING",
                    "optional": False
                },
                // Add more properties as needed
            ]
            execution_result = create_edge_label_by_json_schema(
                "KNOWS",
                "id",
                properties,
                [
                    ["Person", "Person"],
                    ["Organization", "Person"]
                ]
            )
        """
        primary_prop = next((p for p in properties if p["name"] == primary), None)
        if not primary_prop or primary_prop.get("optional", False):
            properties.append(
                {
                    "name": primary,
                    "type": "STRING",
                    "optional": False,
                }
            )

        # prepare the JSON structure
        label_json = {
            "label": label,
            "type": "EDGE",
            "properties": properties,
            "constraints": constraints,
        }

        cypher_exec = CypherExecutor()
        return await cypher_exec.validate_and_execute_cypher(
            f"CALL db.createEdgeLabelByJson('{json.dumps(label_json)}')"
        )


class CypherExecutor(Tool):
    """Tool for validating and executing TuGraph Cypher schema definitions."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.validate_and_execute_cypher.__name__,
            description=self.validate_and_execute_cypher.__doc__ or "",
            function=self.validate_and_execute_cypher,
        )

    async def validate_and_execute_cypher(self, cypher_schema: str) -> str:
        """Validate the TuGraph Cypher and execute it in the TuGraph Database.
        Make sure the input cypher is only the code without any other information including
        ```Cypher``` or ```TuGraph Cypher```.
        This function can only execute one cypher schema at a time.
        If the schema is valid, return the validation results. Otherwise, return the error message.

        Args:
            cypher_schema (str): TuGraph Cypher schema including only the code.

        Returns:
            Validation and execution results.
        """

        try:
            store = get_tugraph()
            store.conn.run(cypher_schema)
            return f"TuGraph 成功运行如下 schema：\n{cypher_schema}"
        except Exception as e:
            prompt = (
                CYPHER_GRAMMER
                + f"""假设你是 TuGraph DB 的管理员，请验证我给你 TuGraph Cypher 指令的正确性。标准不要太严格，只要不和 TuGraph Cypher 语法冲突就行。
    无论你是否验证通过，都应该给出信息反馈。同时，请确保，输入是用于 Create Schema 的 TuGraph Cypher 指令，而不是数据导入的 Cypher 指令。
    你的最终回答是：语法不合规，然后给出错误信息和修改提示。

    如果输入包含多条 Cypher，则返回错误信息和修改提示，以反映输入的 Cypher 有误。

    经过 TuGraph 内置的验证器，得到了执行错误：{str(e)}
            """  # noqa: E501
            )

            message = ModelMessage(
                payload=cypher_schema, timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
            )

            _model = ModelServiceFactory.create(platform_type=SystemEnv.PLATFORM_TYPE)
            response = await _model.generate(sys_prompt=prompt, messages=[message])
            raise RuntimeError(response.get_payload()) from e


class GraphReachabilityGetter(Tool):
    """Tool for getting the reachability information of the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.get_graph_reachability.__name__,
            description=self.get_graph_reachability.__doc__ or "",
            function=self.get_graph_reachability,
        )

    async def get_graph_reachability(self) -> str:
        """Get the reachability information of the graph database which can help to understand the
        graph structure.

        Args:
            None args required

        Returns:
            str: The reachability of the graph database in string format

        Example:
            reachability_str = get_graph_reachability()
        """
        query = "CALL dbms.graph.getGraphSchema()"
        store = get_tugraph()
        schema = store.conn.run(query=query)

        edges: List = []
        vertexes: List = []
        for element in json.loads(schema[0][0])["schema"]:
            if element["type"] == "EDGE":
                edges.append(element)
            elif element["type"] == "VERTEX":
                vertexes.append(element)
        if not edges or not vertexes:
            return "The graph database schema was not created yet."

        # check if there are any isolated vertexes
        constraints: Set[str] = set()
        for edge in edges:
            for constraint in edge["constraints"]:
                constraints.add(constraint[0])
                constraints.add(constraint[1])
        vertex_labels = [vertex["label"] for vertex in vertexes]
        isolated_labels = []
        for vertex_label in vertex_labels:
            if vertex_label not in constraints:
                isolated_labels.append(vertex_label)

        # return the reachability information
        return self._format_reachability_info(vertex_labels, edges, isolated_labels)

    def _format_reachability_info(
        self,
        vertex_labels: List[str],
        edges: List[Dict],
        isolated_labels: Optional[List[str]] = None,
    ) -> str:
        """Format the reachability information of the graph database."""
        lines = ["Got the reachability of the graph:"]
        lines.append(f"Vertices: {', '.join(f'({label})' for label in vertex_labels)}")

        edge_lines = [
            f"({cons[0]})-[edge:{edge['label']}]->({cons[1]})"
            for edge in edges
            for cons in edge["constraints"]
        ]
        lines.extend(edge_lines)

        if isolated_labels:
            lines.append(
                "!!! This graph database schema does not have reachability.\n"
                "!!! Isolated vertices found: "
                f"{', '.join(f'({label})' for label in isolated_labels)}"
            )
        else:
            lines.append("After verified, the graph database schema has reachability.")

        return "\n".join(lines)


def get_analysis_operator():
    """Get the operator for document analysis."""
    analysis_toolkit = Toolkit()

    content_understanding_action = Action(
        id="doc_analysis.content_understanding",
        name="内容理解",
        description="通过阅读和批注理解文档的主要内容和结构",
    )
    concept_identification_action = Action(
        id="doc_analysis.concept_identification",
        name="核心概念识别",
        description="识别并提取文档中的关键概念和术语，对概念进行分类，建立层级关系。",
    )
    relation_pattern_recognition_action = Action(
        id="doc_analysis.relation_pattern",
        name="关系模式识别",
        description="发现概念间的关系模式和交互方式（结构模式、语义模式、演化模式）、提取概念网络特征（局部、全局、动态）。",
    )
    consistency_check_action = Action(
        id="doc_analysis.consistency_check",
        name="一致性检查",
        description="检查文档中的概念和关系是否一致，确保概念和关系已经对齐。并且没有孤立的概念（即，没有相邻的概念）",
    )
    read_document = DocumentReader(id="read_document_tool")

    analysis_toolkit.add_action(
        action=content_understanding_action,
        next_actions=[(concept_identification_action, 1)],
        prev_actions=[],
    )
    analysis_toolkit.add_action(
        action=concept_identification_action,
        next_actions=[(relation_pattern_recognition_action, 1)],
        prev_actions=[(content_understanding_action, 1)],
    )
    analysis_toolkit.add_action(
        action=relation_pattern_recognition_action,
        next_actions=[(consistency_check_action, 1)],
        prev_actions=[(concept_identification_action, 1)],
    )
    analysis_toolkit.add_action(
        action=consistency_check_action,
        next_actions=[],
        prev_actions=[(relation_pattern_recognition_action, 1)],
    )
    analysis_toolkit.add_tool(
        tool=read_document, connected_actions=[(content_understanding_action, 1)]
    )

    operator_config = OperatorConfig(
        id="analysis_operator",
        instruction=DOC_ANALYSIS_PROFILE + DOC_ANALYSIS_INSTRUCTION,
        output_schema=DOC_ANALYSIS_OUTPUT_SCHEMA,
        actions=[
            content_understanding_action,
            concept_identification_action,
            relation_pattern_recognition_action,
            consistency_check_action,
        ],
    )
    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=analysis_toolkit),
    )

    return operator


def get_concept_modeling_operator():
    """Get the operator for concept modeling."""
    entity_type_definition_action = Action(
        id="concept_modeling.entity_type",
        name="实体类型定义",
        description="定义和分类文档中识别出的核心实体类型，只需要分析即可",
    )
    relation_type_definition_action = Action(
        id="concept_modeling.relation_type",
        name="关系类型定义",
        description="设计实体间的关系类型和属性，只需要分析即可",
    )
    self_reflection_schema_action = Action(
        id="concept_modeling.reflection_schema",
        name="自我反思目前阶段的概念建模",
        description="不断检查和反思当前概念模型的设计，确保模型的完整性和准确性，并发现潜在概念和关系。最后确保实体关系之间是存在联系的，禁止出现孤立的实体概念（这很重要）。",
    )
    schema_design_action = Action(
        id="concept_modeling.schema_design",
        name="Schema设计创建 TuGraph labels",
        description="将概念模型转化为图数据库 label，并在 TuGraph 中创建 labels",
    )
    graph_validation_action = Action(
        id="concept_modeling.graph_validation",
        name="反思和检查图的可达性(Reachability)",
        description="需要调用相关的工具来检查。可达性指的是每个节点标签和关系标签都有至少一个节点或关系与之关联。如果不连通，则需要在目前的基础上调用工具来解决。",
    )
    vertex_label_generator = VertexLabelGenerator(id="vertex_label_generator_tool")
    edge_label_generator = EdgeLabelGenerator(id="edge_label_generator_tool")
    graph_reachability_getter = GraphReachabilityGetter(id="graph_reachability_getter_tool")

    concept_modeling_toolkit = Toolkit()

    concept_modeling_toolkit.add_action(
        action=entity_type_definition_action,
        next_actions=[(relation_type_definition_action, 1)],
        prev_actions=[],
    )
    concept_modeling_toolkit.add_action(
        action=relation_type_definition_action,
        next_actions=[(self_reflection_schema_action, 1)],
        prev_actions=[(entity_type_definition_action, 1)],
    )
    concept_modeling_toolkit.add_action(
        action=self_reflection_schema_action,
        next_actions=[(schema_design_action, 1)],
        prev_actions=[(relation_type_definition_action, 1)],
    )
    concept_modeling_toolkit.add_action(
        action=schema_design_action,
        next_actions=[(graph_validation_action, 1)],
        prev_actions=[(self_reflection_schema_action, 1)],
    )
    concept_modeling_toolkit.add_action(
        action=graph_validation_action,
        next_actions=[],
        prev_actions=[(schema_design_action, 1)],
    )
    concept_modeling_toolkit.add_tool(
        tool=vertex_label_generator, connected_actions=[(schema_design_action, 1)]
    )
    concept_modeling_toolkit.add_tool(
        tool=edge_label_generator, connected_actions=[(schema_design_action, 1)]
    )
    concept_modeling_toolkit.add_tool(
        tool=graph_reachability_getter, connected_actions=[(graph_validation_action, 1)]
    )

    operator_config = OperatorConfig(
        id="concept_modeling_operator",
        instruction=CONCEPT_MODELING_PROFILE + CONCEPT_MODELING_INSTRUCTION,
        output_schema=CONCEPT_MODELING_OUTPUT_SCHEMA,
        actions=[
            entity_type_definition_action,
            relation_type_definition_action,
            self_reflection_schema_action,
            schema_design_action,
            graph_validation_action,
        ],
    )

    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=concept_modeling_toolkit),
    )

    return operator


def get_graph_modeling_workflow():
    """Get the workflow for graph modeling and assemble the operators."""
    analysis_operator = get_analysis_operator()
    concept_modeling_operator = get_concept_modeling_operator()

    workflow = DbgptWorkflow()
    workflow.add_operator(
        operator=analysis_operator,
        previous_ops=[],
        next_ops=[concept_modeling_operator],
    )
    workflow.add_operator(
        operator=concept_modeling_operator,
        previous_ops=[analysis_operator],
        next_ops=None,
    )

    return workflow


def get_graph_modeling_expert_config(reasoner: Optional[Reasoner] = None) -> AgentConfig:
    """Get the expert configuration for graph modeling."""

    expert_config = AgentConfig(
        profile=Profile(name="Graph Modeling Expert", description=CONCEPT_MODELING_PROFILE),
        reasoner=reasoner or DualModelReasoner(),
        workflow=get_graph_modeling_workflow(),
    )

    return expert_config
