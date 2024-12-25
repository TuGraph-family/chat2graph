import asyncio
import json
import time
from typing import Dict, List, Optional, Union

from dbgpt.storage.graph_store.tugraph_store import TuGraphStore, TuGraphStoreConfig

from app.agent.job import Job
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.reasoner.model_service_factory import ModelServiceFactory
from app.agent.workflow.operator.operator import Operator, OperatorConfig
from app.commom.system_env import SystemEnv
from app.memory.message import ModelMessage
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.toolkit import Toolkit, ToolkitService


# global function to get tugraph store
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
                password="your_password",
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
你是一位专业的文档分析专家。你的工作是，阅读提供的文档材料，给出一些结论，然后为后续的知识图谱的构建做好准备工作。
你需要帮助用户理解文档内容。你阅读的文档只是一部分，但是你需要管中窥豹，推测全局的数据的样貌。做好准备工作，尽可能地了解文档。
请注意，你的任务不是 knowledge graph modeling。你的任务是分析文档，为后续的 knowledge graph modeling 做准备。
"""

DOC_ANALYSIS_INSTRUCTION = """
请仔细阅读给定的文档,同时，按要求完成任务：

1. 文档内容分析
- 发现重要的业务规则和逻辑
- 推理文档的数据全貌
"""

DOC_ANALYSIS_OUTPUT_SCHEMA = """
{
    "domain": "文档所属领域",
    "init_properties": "文档中的属性信息",
    "business_rules": "推测文档中的业务规则",
    "analysis" : "从分析的文档中得出的有助于‘Graph Schema Modeling’设计的结论。比如这个文档的性质，需要注意的点。（这个 field 应该是几段很长的分析文本）",
    "data_full_view": "文档数据的全貌是什么样子，填写推测链路（这个 field 应该是几段很长的描述性文本）",
}
"""

# operation 2: Concept Modeling
CONCEPT_MODELING_PROFILE = """
你是一位知识图谱建模专家，擅长将概念和关系转化为图数据库模式。你需要帮助用户设计合适的实体-关系模型。
"""

CONCEPT_MODELING_INSTRUCTION = """
基于文档分析的结果,完成以下概念建模任务:

1. 实体类型定义
- 将相关概念归类为实体类型，确保类型之间具有明确的边界和区分度
- 为每个实体类型定义完整的属性集，包括必需属性和可选属性
- 实体类型应具有层次性和可扩展性，支持上下位关系
- 确保实体类型之间存在潜在的关联路径，但保持概念边界的独立性

2. 关系类型设计
- 定义实体间的关系类型，包括直接关系和派生关系
- 明确关系的方向性（有向）、设计关系的属性集
- 通过关系组合确保图的强连通性，支持未来可能出现的多跳查询的需求
- （可选）考虑添加反向关系以增强图的表达能力

3. Schema生成
- 使用 graph schema generator 的函数，可以使用该函数生成 schema，为 vertex 和 edge 创建特殊的 schema。
- 请注意：Schema 不是在 DB 中插入节点、关系等具体的数据，而是定义图数据库的模式（schema/label）。预期应该是定义是实体的类型、关系的类型、约束等这些东西。
- 任务的背景是知识图谱，所以，不要具体的某个实体，而是相对通用的实体。比如，可以从时间、抽象概念、物理实体和社会实体等多个主要维度来考虑。
- 需要多次读取 TuGraph 现有的 Schema，目的是确保根据 DDL 创建的 schema 符合预期。
"""

CONCEPT_MODELING_OUTPUT_SCHEMA = """
{
    "stauts": "模型状态，是否通过验证等",
    "entity_label": "成功创建的实体标签",
    "relation_label": "成功创建的关系标签",
}
"""

ROMANCE_OF_THE_THREE_KINGDOMS_CHAP_10 = """
第十回 
    勤王室马腾举义 报父仇曹操兴师
    
    却说李、郭二贼欲弑献帝。张济、樊稠谏曰：“不可。今日若便杀之，恐众人不服，不如仍旧奉之为主，赚诸侯入关，先去其羽翼，然后杀之，天下可图也。”李、郭二人从其言，按住兵器。帝在楼上宣谕曰：“王允既诛，军马何故不退？”李傕、郭汜曰：“臣等有功王室，未蒙赐爵，故不敢退军。”帝曰：“卿欲封何爵？”李、郭、张、樊四人各自写职衔献上，勒要如此官品，帝只得从之。封李傕为车骑将军、池阳侯，领司隶校尉假节钺，郭汜为后将军美阳侯假节钺，同秉朝政；樊稠为右将军万年侯，张济为骠骑将军平阳侯，领兵屯弘农。其余李蒙、王方等，各为校尉。然后谢恩，领兵出城。又下令追寻董卓尸首，获得些零碎皮骨，以香木雕成形体，安凑停当，大设祭祀，用王者衣冠棺椁，选择吉日，迁葬郿坞。临葬之期，天降大雷雨，平地水深数尺，霹雳震开其棺，尸首提出棺外。李傕候晴再葬，是夜又复如是。三次改葬，皆不能葬，零皮碎骨，悉为雷火消灭。天之怒卓。可谓甚矣！

    且说李傕、郭汜既掌大权，残虐百姓；密遣心腹侍帝左右，观其动静。献帝此时举动荆棘。朝廷官员，并由二贼升降。因采人望，特宣朱儁入朝封为太仆，同领朝政。一日，人报西凉太守马腾；并州刺史韩遂二将引军十余万，杀奔长安来，声言讨贼。原来二将先曾使人入长安，结连侍中马宇、谏议大夫种邵、左中郎将刘范三人为内应，共谋贼党。三人密奏献帝，封马腾为征西将军、韩遂为镇西将军，各受密诏，并力讨贼。当下李傕、郭汜、张济、樊稠闻二军将至，一同商议御敌之策。谋士贾诩曰：“二军远来，只宜深沟高垒，坚守以拒之。不过百日，彼兵粮尽，必将自退，然后引兵追之，二将可擒矣。”李蒙、王方出曰：“此非好计。愿借精兵万人，立斩马腾、韩遂之头，献于麾下。”贾诩曰：“今若即战，必当败绩。”李蒙、王方齐声曰：“若吾二人败，情愿斩首；吾若战胜，公亦当输首级与我。”诩谓李傕、郭汜曰：“长安西二百里盩厔山，其路险峻，可使张、樊两将军屯兵于此，坚壁守之；待李蒙、王方自引兵迎敌，可也。”李傕、郭汜从其言，点一万五千人马与李蒙、王方。二人忻喜而去，离长安二百八十里下寨。

    西凉兵到，两个引军迎去。西凉军马拦路摆开阵势。马腾、韩遂联辔而出，指李蒙、王方骂曰：“反国之贼！谁去擒之？”言未绝，只见一位少年将军，面如冠玉，眼若流星，虎体猿臂，彪腹狼腰；手执长枪，坐骑骏马，从阵中飞出。原来那将即马腾之子马超，字孟起，年方十七岁，英勇无敌。王方欺他年幼，跃马迎战。战不到数合，早被马超一枪刺于马下。马超勒马便回。李蒙见王方刺死，一骑马从马超背后赶来。超只做不知。马腾在阵门下大叫：“背后有人追赶！”声犹未绝，只见马超已将李蒙擒在马上。原来马超明知李蒙追赶，却故意俄延；等他马近举枪刺来，超将身一闪，李蒙搠个空，两马相并，被马超轻舒猿臂，生擒过去。军士无主，望风奔逃。马腾、韩遂乘势追杀，大获胜捷，直逼隘口下寨，把李蒙斩首号令。李傕、郭汜听知李蒙、王方皆被马超杀了，方信贾诩有先见之明，重用其计，只理会紧守关防，由他搦战，并不出迎。果然西凉军未及两月，粮草俱乏，商议回军。恰好长安城中马宇家僮出首家主与刘范、种邵，外连马腾、韩遂，欲为内应等情。李傕、郭汜大怒，尽收三家老少良贱斩于市，把三颗首级，直来门前号令。马腾、韩遂见军粮已尽，内应又泄，只得拔寨退军。李傕、郭汜令张济引军赶马腾，樊稠引军赶韩遂，西凉军大败。马超在后死战，杀退张济。樊稠去赶韩遂，看看赶上，相近陈仓，韩遂勒马向樊稠曰：“吾与公乃同乡之人，今日何太无情？”樊稠也勒住马答道：“上命不可违！”韩遂曰：“吾此来亦为国家耳，公何相逼之甚也？”樊稠听罢，拨转马头，收兵回寨，让韩遂去了。

    不提防李傕之侄李别，见樊稠放走韩遂，回报其叔。李傕大怒，便欲兴兵讨樊稠。贾翊曰：“目今人心未宁，频动干戈，深为不便；不若设一宴，请张济、樊稠庆功，就席间擒稠斩之，毫不费力。”李傕大喜，便设宴请张济、樊稠。二将忻然赴宴。酒半阑，李傕忽然变色曰：“樊稠何故交通韩遂，欲谋造反？”稠大惊，未及回言；只见刀斧手拥出，早把樊稠斩首于案下。吓得张济俯伏于地。李傕扶起曰：“樊稠谋反，故尔诛之；公乃吾之心腹，何须惊惧？”将樊稠军拨与张济管领。张济自回弘农去了。李傕、郭汜自战败西凉兵，诸侯莫敢谁何。贾诩屡劝抚安百姓，结纳贤豪。自是朝廷微有生意。不想青州黄巾又起，聚众数十万，头目不等，劫掠良民。太仆朱儁保举一人，可破群贼。李傕、郭汜问是何人。朱儁曰：“要破山东群贼，非曹孟德不可。”李傕曰：“孟德今在何处？”俊曰：“现为东郡太守，广有军兵。若命此人讨贼，贼可克日而破也。”李傕大喜，星夜草诏，差人赍往东郡，命曹操与济北相鲍信一同破贼。操领了圣旨，会同鲍信，一同兴兵，击贼于寿阳。鲍信杀入重地，为贼所害。操追赶贼兵，直到济北，降者数万。操即用贼为前驱，兵马到处，无不降顺。不过百余日，招安到降兵三十余万、男女百余万口。操择精锐者，号为“青州兵”，其余尽令归农。操自此威名日重。捷书报到长安，朝廷加曹操为镇东将军。操在兖州，招贤纳士。有叔侄二人来投操：乃颍川颍阴人，姓荀，名彧，字文若，荀绲之子也；旧事袁绍，今弃绍投操；操与语大悦，曰：“此吾之子房也！”遂以为行军司马。其侄荀攸，字公达，海内名士，曾拜黄门侍郎，后弃官归乡，今与其叔同投曹操，操以为行军教授。荀彧曰：“某闻兖州有一贤士，今此人不知何在。”操问是谁，彧曰：“乃东郡东阿人，姓程，名昱，字仲德。”操曰：“吾亦闻名久矣。”遂遣人于乡中寻问。访得他在山中读书，操拜请之。程昱来见，曹操大喜。昱谓荀彧曰：“某孤陋寡闻，不足当公之荐。公之乡人姓郭，名嘉，字奉孝，乃当今贤士，何不罗而致之？”彧猛省曰：“吾几忘却！”遂启操征聘郭嘉到兖州，共论天下之事。郭嘉荐光武嫡派子孙，淮南成德人，姓刘，名晔，字子阳。操即聘晔至。晔又荐二人：一个是山阳昌邑人，姓满，名宠，字伯宁；一个是武城人，姓吕，名虔，字子恪。曹操亦素知这两个名誉，就聘为军中从事。满宠、吕虔共荐一人，乃陈留平邱人，姓毛，名玠，字孝先。曹操亦聘为从事。

    又有一将引军数百人，来投曹操：乃泰山巨平人，姓于，名禁，字文则。操见其人弓马熟娴，武艺出众，命为点军司马。一日，夏侯惇引一大汉来见，操问何人，惇曰：“此乃陈留人，姓典，名韦，勇力过人。旧跟张邈，与帐下人不和，手杀数十人，逃窜山中。惇出射猎，见韦逐虎过涧，因收于军中。今特荐之于公。”操曰：“吾观此人容貌魁梧，必有勇力。”惇曰：“他曾为友报仇杀人，提头直出闹市，数百人不敢近。只今所使两枝铁戟，重八十斤，挟之上马，运使如飞。”操即令韦试之。韦挟戟骤马，往来驰骋。忽见帐下大旗为风所吹，岌岌欲倒，众军士挟持不定；韦下马，喝退众军，一手执定旗杆，立于风中，巍然不动。操曰：“此古之恶来也！”遂命为帐前都尉，解身上棉袄，及骏马雕鞍赐之。

    自是曹操部下文有谋臣，武有猛将，威镇山东。乃遣泰山太守应劭，往琅琊郡取父曹嵩。嵩自陈留避难，隐居琅琊；当日接了书信，便与弟曹德及一家老小四十余人，带从者百余人，车百余辆，径望兖州而来。道经徐州，太守陶谦，字恭祖，为人温厚纯笃，向欲结纳曹操，正无其由；知操父经过，遂出境迎接，再拜致敬，大设筵宴，款待两日。曹嵩要行，陶谦亲送出郭，特差都尉张闿，将部兵五百护送。曹嵩率家小行到华、费间，时夏末秋初，大雨骤至，只得投一古寺歇宿。寺僧接入。嵩安顿家小，命张闿将军马屯于两廊。众军衣装，都被雨打湿，同声嗟怨。张闿唤手下头目于静处商议曰：“我们本是黄巾余党，勉强降顺陶谦，未有好处。如今曹家辎重车辆无数，你们欲得富贵不难，只就今夜三更，大家砍将入去，把曹嵩一家杀了，取了财物，同往山中落草。此计何如？”众皆应允。是夜风雨未息，曹嵩正坐，忽闻四壁喊声大举。曹德提剑出看，就被搠死。曹嵩忙引一妾奔入方丈后，欲越墙而走；妾肥胖不能出，嵩慌急，与妾躲于厕中，被乱军所杀。应劭死命逃脱，投袁绍去了。张闿杀尽曹嵩全家，取了财物，放火烧寺，与五百人逃奔淮南去了。后人有诗曰：“曹操奸雄世所夸，曾将吕氏杀全家。如今阖户逢人杀，天理循环报不差。”当下应劭部下有逃命的军士，报与曹操。操闻之，哭倒于地。众人救起。操切齿曰：“陶谦纵兵杀吾父，此仇不共戴天！吾今悉起大军，洗荡徐州，方雪吾恨！”遂留荀彧、程昱领军三万守鄄城、范县、东阿三县，其余尽杀奔徐州来。夏侯惇、于禁、典韦为先锋。操令：但得城池，将城中百姓，尽行屠戮，以雪父仇。当有九江太守边让，与陶谦交厚，闻知徐州有难，自引兵五千来救。操闻之大怒，使夏侯惇于路截杀之。时陈宫为东郡从事，亦与陶谦交厚；闻曹操起兵报仇，欲尽杀百姓，星夜前来见操。操知是为陶谦作说客，欲待不见，又灭不过旧恩，只得请入帐中相见。宫曰：“今闻明公以大兵临徐州，报尊父之仇，所到欲尽杀百姓，某因此特来进言。陶谦乃仁人君子，非好利忘义之辈；尊父遇害，乃张闿之恶，非谦罪也。且州县之民，与明公何仇？杀之不祥。望三思而行。”操怒曰：“公昔弃我而去，今有何面目复来相见？陶谦杀吾一家，誓当摘胆剜心，以雪吾恨！公虽为陶谦游说，其如吾不听何！”陈宫辞出，叹曰：“吾亦无面目见陶谦也！”遂驰马投陈留太守张邈去了。

    且说操大军所到之处，杀戮人民，发掘坟墓。陶谦在徐州，闻曹操起军报仇，杀戮百姓，仰天恸哭曰：“我获罪于天，致使徐州之民，受此大难！”急聚众官商议。曹豹曰：“曹兵既至，岂可束手待死！某愿助使君破之。”陶谦只得引兵出迎，远望操军如铺霜涌雪，中军竖起白旗二面，大书报仇雪恨四字。军马列成阵势，曹操纵马出阵，身穿缟素，扬鞭大骂。陶谦亦出马于门旗下，欠身施礼曰：“谦本欲结好明公，故托张闿护送。不想贼心不改，致有此事。实不干陶谦之故。望明公察之。”操大骂曰：“老匹夫！杀吾父，尚敢乱言！谁可生擒老贼？”夏侯惇应声而出。陶谦慌走入阵。夏侯惇赶来，曹豹挺枪跃马，前来迎敌。两马相交，忽然狂风大作，飞沙走石，两军皆乱，各自收兵。

    陶谦入城，与众计议曰：“曹兵势大难敌，吾当自缚往操营，任其剖割，以救徐州一郡百姓之命。”言未绝，一人进前言曰：“府君久镇徐州，人民感恩。今曹兵虽众，未能即破我城。府君与百姓坚守勿出；某虽不才，愿施小策，教曹操死无葬身之地！”众人大惊，便问计将安出。正是：本为纳交反成怨，那知绝处又逢生。

    毕竟此人是谁，且听下文分解。
"""


class DocumentReader(Tool):
    """Tool for analyzing document content."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id,
            name=self.read_document.__name__,
            description=self.read_document.__doc__,
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

        return ROMANCE_OF_THE_THREE_KINGDOMS_CHAP_10


class VertexLabelGenerator(Tool):
    """Tool for generating Cypher statements to create vertex labels in TuGraph."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id,
            name=self.create_vertex_label_by_json_schema.__name__,
            description=self.create_vertex_label_by_json_schema.__doc__,
            function=self.create_vertex_label_by_json_schema,
        )

    async def create_vertex_label_by_json_schema(
        self,
        label: str,
        primary: str,
        properties: List[Dict[str, Union[str, bool]]],
    ) -> str:
        """Generate a TuGraph vertex label statement, and then operator the TuGraph database to create the labels in the database.
        Field names can only contain letters, numbers, and underscores.

        Args:
            label (str): The name of the vertex label to create
            primary (str): The name of the primary key field
            properties (List[Dict]): List of property definitions, each containing:
                - name (str): Property name
                - type (str): Property type (e.g., 'STRING', 'INT32')
                - optional (bool): Whether the property is optional
                - index (bool, optional): Whether to create an index
                And make sure the primary key occurs in the properties list and is not optional.

        Returns:
            str: The complete Cypher statement for creating the vertex label

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
            stmt = create_vertex_label_by_json_schema("Person", "id", properties)
        """
        # Validate primary key exists in properties
        primary_prop = next((p for p in properties if p["name"] == primary), None)
        if not primary_prop or primary_prop.get("optional", False):
            properties.append({
                "name": primary,
                "type": "STRING",
                "optional": False,
            })

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
            id=id,
            name=self.create_edge_label_by_json_schema.__name__,
            description=self.create_edge_label_by_json_schema.__doc__,
            function=self.create_edge_label_by_json_schema,
        )

    async def create_edge_label_by_json_schema(
        self,
        label: str,
        primary: str,
        properties: List[Dict[str, Union[str, bool]]],
        constraints: List[List[str]],
    ) -> str:
        """Generate a TuGraph edge label statement, and then operator the TuGraph database to create the labels in the database.
        Field names can only contain letters, numbers, and underscores.

        Args:
            label (str): The name of the edge label to create
            primary (str): The name of the primary key field
            properties (List[Dict]): List of property definitions, each containing:
                - name (str): Property name
                - type (str): Property type (e.g., 'STRING', 'INT32')
                - optional (bool): Whether the property is optional
            constraints (List[List[str]]): List of source and target vertex label constraints, which presents the direction of the edge.
                It can configure multiple source and target vertex label constraints,
                for example, [["source label", "target label"], ["other source label", "other target label"]]

        Returns:
            str: The complete Cypher statement for creating the edge label

        Example:
            properties = [
                {
                    "name": "type",
                    "type": "STRING",
                    "optional": False
                },
                // Add more properties as needed
            ]
            stmt = create_edge_label_by_json_schema(
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
            properties.append({
                "name": primary,
                "type": "STRING",
                "optional": False,
            })

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
            id=id,
            name=self.validate_and_execute_cypher.__name__,
            description=self.validate_and_execute_cypher.__doc__,
            function=self.validate_and_execute_cypher,
        )

    async def validate_and_execute_cypher(self, cypher_schema: str) -> str:
        """Validate the TuGraph Cypher and execute it in the TuGraph Database.
        Make sure the input cypher is only the code without any other information including ```Cypher``` or ```TuGraph Cypher```.
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
            """
            )

            message = ModelMessage(
                content=cypher_schema, timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
            )

            _model = ModelServiceFactory.create(platform_type=SystemEnv.platform_type())
            response = await _model.generate(sys_prompt=prompt, messages=[message])
            raise Exception(response.get_payload())


class LabelGetter(Tool):
    """Tool for getting all the labels of the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id,
            name=self.get_db_labels.__name__,
            description=self.get_db_labels.__doc__,
            function=self.get_db_labels,
        )

    async def get_db_labels(self) -> str:
        """Get all the labels of the graph database.

        Args:
            None

        Returns:
            The labels of the graph database.
        """
        store = get_tugraph()
        query_vertex_labels = "CALL db.vertexLabels()"
        query_edge_labels = "CALL db.edgeLabels()"
        return f"{store.conn.run(query_vertex_labels)}\n{store.conn.run(query_edge_labels)}"


def get_analysis_operator():
    """Get the operator for document analysis."""
    analysis_toolkit = Toolkit()

    content_understanding = Action(
        id="doc_analysis.content_understanding",
        name="内容理解",
        description="通过阅读和批注理解文档的主要内容和结构",
    )
    concept_identification = Action(
        id="doc_analysis.concept_identification",
        name="核心概念识别",
        description="识别并提取文档中的关键概念和术语",
    )
    relation_pattern_recognition = Action(
        id="doc_analysis.relation_pattern",
        name="关系模式识别",
        description="发现概念间的关系模式和交互方式，以及潜在的关联，越丰富越好",
    )
    read_document = DocumentReader(id="read_document_tool")

    analysis_toolkit.add_action(
        action=content_understanding,
        next_actions=[(concept_identification, 1)],
        prev_actions=[],
    )
    analysis_toolkit.add_action(
        action=concept_identification,
        next_actions=[(relation_pattern_recognition, 1)],
        prev_actions=[(content_understanding, 1)],
    )
    analysis_toolkit.add_action(
        action=relation_pattern_recognition,
        next_actions=[],
        prev_actions=[(concept_identification, 1)],
    )
    analysis_toolkit.add_tool(
        tool=read_document, connected_actions=[(content_understanding, 1)]
    )

    operator_config = OperatorConfig(
        id="analysis_operator",
        instruction=DOC_ANALYSIS_PROFILE + DOC_ANALYSIS_INSTRUCTION,
        output_schema=DOC_ANALYSIS_OUTPUT_SCHEMA,
        actions=[
            content_understanding,
            concept_identification,
            relation_pattern_recognition,
        ],
    )
    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=analysis_toolkit),
    )

    return operator


def get_concept_modeling_operator():
    """Get the operator for concept modeling."""
    entity_type_definition = Action(
        id="concept_modeling.entity_type",
        name="实体类型定义",
        description="定义和分类文档中识别出的核心实体类型，只需要分析即可",
    )
    relation_type_definition = Action(
        id="concept_modeling.relation_type",
        name="关系类型定义",
        description="设计实体间的关系类型和属性，只需要分析即可",
    )
    self_reflection_schema = Action(
        id="concept_modeling.reflection_schema",
        name="自我反思目前阶段的概念建模",
        description="不断检查和反思当前概念模型的设计，确保模型的完整性和准确性，并发现潜在概念和关系。最后确保实体关系之间是存在联系的，禁止出现孤立的实体概念（这很重要）。",
    )
    graph_validation = Action(
        id="concept_modeling.graph_validation",
        name="检查图的连通性",
        description="连通性指的是每个节点标签和关系标签都有至少一个节点或关系与之关联。",
    )
    schema_design = Action(
        id="concept_modeling.schema_design",
        name="Schema设计创建 TuGraph labels",
        description="将概念模型转化为图数据库 label，并在 TuGraph 中创建 labels",
    )
    vertex_label_generator = VertexLabelGenerator(id="vertex_label_generator_tool")
    edge_label_generator = EdgeLabelGenerator(id="edge_label_generator_tool")
    label_getter = LabelGetter(id="label_getter_tool")

    concept_modeling_toolkit = Toolkit()

    concept_modeling_toolkit.add_action(
        action=entity_type_definition,
        next_actions=[(relation_type_definition, 1)],
        prev_actions=[],
    )
    concept_modeling_toolkit.add_action(
        action=relation_type_definition,
        next_actions=[(self_reflection_schema, 1)],
        prev_actions=[(entity_type_definition, 1)],
    )
    concept_modeling_toolkit.add_action(
        action=self_reflection_schema,
        next_actions=[(schema_design, 1)],
        prev_actions=[(relation_type_definition, 1)],
    )
    concept_modeling_toolkit.add_action(
        action=graph_validation,
        next_actions=[(schema_design, 1)],
        prev_actions=[(self_reflection_schema, 1)],
    )
    concept_modeling_toolkit.add_action(
        action=schema_design,
        next_actions=[],
        prev_actions=[(graph_validation, 1), (self_reflection_schema, 1)],
    )
    concept_modeling_toolkit.add_tool(
        tool=vertex_label_generator, connected_actions=[(schema_design, 1)]
    )
    concept_modeling_toolkit.add_tool(
        tool=edge_label_generator, connected_actions=[(schema_design, 1)]
    )
    concept_modeling_toolkit.add_tool(
        tool=label_getter, connected_actions=[(graph_validation, 1)]
    )

    operator_config = OperatorConfig(
        id="concept_modeling_operator",
        instruction=CONCEPT_MODELING_PROFILE + CONCEPT_MODELING_INSTRUCTION,
        output_schema=CONCEPT_MODELING_OUTPUT_SCHEMA,
        actions=[
            entity_type_definition,
            relation_type_definition,
            schema_design,
            graph_validation,
        ],
    )

    operator = Operator(
        config=operator_config,
        toolkit_service=ToolkitService(toolkit=concept_modeling_toolkit),
    )

    return operator


def get_graph_rag_workflow():
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


async def main():
    """Main function"""
    workflow = get_graph_rag_workflow()

    job = Job(
        id="test_job_id",
        session_id="test_session_id",
        goal="「任务」",
        context="目前我们的问题的背景是，通过函数读取文档第10章节的内容，生成知识图谱图数据库的模式（Graph schema/label），最后调用相关函数来帮助在图数据库中创建 labels。"
        "文档的主题是三国演义。可能需要调用相关的工具（通过函数调用）来操作图数据库。",
    )
    reasoner = DualModelReasoner()

    result = await workflow.execute(job=job, reasoner=reasoner)

    print(f"Final result:\n{result.scratchpad}")


if __name__ == "__main__":
    asyncio.run(main())
