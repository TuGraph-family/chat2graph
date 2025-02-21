import re
from typing import Any, Dict, Optional
from uuid import uuid4

from app.core.resource.read_doc import SchemaManager
from app.core.toolkit.tool import Tool
from app.plugin.neo4j.neo4j_store import get_neo4j

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
        """获取图数据库的 schema 信息"""
        schema = await SchemaManager.read_schema()

        result = "# Neo4j Graph Schema\n\n"

        # 节点信息
        result += "## Node Labels\n\n"
        for label, info in schema["nodes"].items():
            result += f"### {label}\n"
            result += f"- Primary Key: `{info['primary_key']}`\n"
            result += "- Properties:\n"
            for prop in info["properties"]:
                index_info = ""
                if prop["has_index"]:
                    index_info = f" (Indexed: {prop['index_name']})"
                else:
                    index_info = " (Indexed: not indexed)"
                result += f"  - `{prop['name']}` ({prop['type']}){index_info}\n"
            result += "\n"

        # 关系信息
        result += "## Relationship Types\n\n"
        for label, info in schema["relationships"].items():
            result += f"### {label}\n"
            result += f"- Primary Key: `{info['primary_key']}`\n"
            result += "- Properties:\n"
            for prop in info["properties"]:
                index_info = ""
                if prop["has_index"]:
                    index_info = f" (Indexed: {prop['index_name']})"
                result += f"  - `{prop['name']}` ({prop['type']}){index_info}\n"
            result += "\n"

        return result


class DataImport(Tool):
    """Tool for importing data into a graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.import_data.__name__,
            description=self.import_data.__doc__ or "",
            function=self.import_data,
        )

    async def import_data(
        self,
        source_label: str,
        source_primary_key: str,
        source_properties: Dict[str, Any],
        target_label: str,
        target_primary_key: str,
        target_properties: Dict[str, Any],
        relationship_label: str,
        relationship_properties: Dict[str, Any],
    ) -> str:
        """Import the graph data into the database by processing the triplet.
        Each relationship and its associated source/target nodes are processed as a triple unit.
        This function can be called multiple times to import multiple triplets.
        Please parse the arguments correctly after reading the schema, so that the data base accepts
            the data.

        Data Validation Rules:
            - All entities must have a valid primary key defined in their properties
            - Entity and relationship labels must exist in the database schema, and the constraints of the edges
                present the direction of the relationship. For example, constraints [A, B] and [B, A] are different
                directions of the relationship. Never flip the direction of the relationship
            - Properties must be a dictionary and contain all required fields defined in schema
            - Invalid entities or relationships will be silently skipped
            - Date values must be in YYYY-MM-DD format, for example, "2022-01-01" or
                "2022-01-01T00:00:00Z", but "208-01-01" (without a 0 in 208) is invalid
            - Use the English letters (by snake_case naming) for the field if it is related to the identity
                instead of the number (e.g., "LiuBei" for person_id, instead of "123")

        Args:
            source_label (str): Label of the source node (e.g., "Person"), defined in the graph schema
            source_primary_key (str): Primary key of the source node (e.g., "id")
            source_properties (Dict[str, Any]): Properties of the source node. If it is related to the identity of
                    the entity, it should be in English letters (by snake_case naming)
                - some_not_optional_field (str): Required field. If it is related to the identity of
                    the entity, it should be in English letters (by snake_case naming)
                - Other related fields as defined in schema
            target_label (str): Label of the target node, defined in the graph schema
            target_primary_key (str): Primary key of the target node
            target_properties (Dict[str, Any]): Properties of the target node. If it is related to the identity of
                    the entity, it should be in English letters (by snake_case naming)
                - Other related fields as defined in schema
            relationship_label (str): Label of the relationship, defined in the graph schema
            relationship_properties (Dict[str, Any]): Properties of the relationship. If it is related to the identity of
                    the entity, it should be in English letters (by snake_case naming)
                - Other related fields as defined in schema

        Returns:
            str: Summary of the import operation, including counts of entities and relationships
                processed, created, and updated.
        """

        def format_date(value: str) -> str:
            """Format date value to ensure it has a leading zero in the year."""
            date_pattern = r"^(\d{3})-(\d{2})-(\d{2})(T[\d:]+Z)?$"
            match = re.match(date_pattern, value)
            if match:
                year = match.group(1)
                if len(year) == 3:
                    time_part = match.group(4) or ""
                    return f"0{year}-{match.group(2)}-{match.group(3)}{time_part}"
            return value

        def format_property_value(value: Any) -> str:
            """Format property value for Cypher query."""
            if value is None:
                return "null"
            elif isinstance(value, int | float):
                return str(value)
            else:
                str_value = str(value)
                str_value = str_value.replace("'", "\\'")
                return f"'{str_value}'"

        def format_properties(properties: Dict[str, Any]) -> str:
            """Format properties dictionary to Cypher property string."""
            props = []
            for key, value in properties.items():
                if key in ["date", "start_date", "end_date", "start_time"] and isinstance(
                    value, str
                ):
                    value = format_date(value)
                props.append(f"{key}: {format_property_value(value)}")
            return "{" + ", ".join(props) + "}"

        try:
            # 格式化属性
            source_props = format_properties(source_properties)
            target_props = format_properties(target_properties)
            rel_props = format_properties(relationship_properties)

            # 构建Cypher语句
            cypher = f"""
            MERGE (source:{source_label} {{{source_primary_key}: {format_property_value(source_properties[source_primary_key])}}})
            ON CREATE SET source = {source_props}
            ON MATCH SET source = {source_props}
            WITH source
            MERGE (target:{target_label} {{{target_primary_key}: {format_property_value(target_properties[target_primary_key])}}})
            ON CREATE SET target = {target_props}
            ON MATCH SET target = {target_props}
            WITH source, target
            MERGE (source)-[r:{relationship_label}]->(target)
            ON CREATE SET r = {rel_props}
            ON MATCH SET r = {rel_props}
            RETURN source, target, r
            """

            store = get_neo4j()
            with store.conn.session() as session:
                # 执行导入操作
                print(f"Executing statement: {cypher}")
                result = session.run(cypher)
                summary = result.consume()
                nodes_created = summary.counters.nodes_created
                nodes_updated = summary.counters.properties_set
                rels_created = summary.counters.relationships_created

                # 获取本次操作的详细信息
                details = {
                    "source": f"{source_label}(id: {source_properties[source_primary_key]})",
                    "target": f"{target_label}(id: {target_properties[target_primary_key]})",
                    "relationship": f"{relationship_label}",
                }

                # 获取数据库当前状态
                # 1. 节点统计
                node_counts = {}
                for label in [source_label, target_label]:
                    result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                    node_counts[label] = result.single()["count"]

                # 2. 关系统计
                rel_count = session.run(
                    f"MATCH ()-[r:{relationship_label}]->() RETURN count(r) as count"
                ).single()["count"]

                # 3. 总体统计
                total_stats = session.run("""
                    MATCH (n) 
                    OPTIONAL MATCH (n)-[r]->() 
                    RETURN 
                        count(DISTINCT n) as total_nodes,
                        count(DISTINCT r) as total_relationships
                """).single()

                return f"""数据导入成功！
本次操作详情：
- 创建/更新的节点：
- 源节点: {details["source"]}
- 目标节点: {details["target"]}
- 创建的关系: {details["relationship"]}
- 操作统计：
- 新建节点数: {nodes_created}
- 更新属性数: {nodes_updated}
- 新建关系数: {rels_created}

当前数据库状态：
- 节点统计：
- {source_label}: {node_counts[source_label]} 个
- {target_label}: {node_counts[target_label]} 个
- 关系统计：
- {relationship_label}: {rel_count} 个
- 总体统计：
- 总节点数: {total_stats["total_nodes"]}
- 总关系数: {total_stats["total_relationships"]}
"""

        except Exception as e:
            raise Exception(f"Failed to import data: {str(e)}")


SCHEMA_BOOK = """
# Neo4j Schema 指南 (LLM 友好版)

本指南帮助理解Neo4j的数据模型和Schema设计。

## 1. 节点 (Node) 定义

Neo4j中的节点代表实体，具有以下特征：

### 1.1 标签 (Labels)
- 节点可以有一个或多个标签
- 标签用于分类和区分不同类型的节点
- 示例：`:Person`、`:Location`

### 1.2 属性 (Properties)
- 属性是键值对
- 支持的数据类型：
  - String：字符串
  - Integer：整数
  - Float：浮点数
  - Boolean：布尔值
  - Point：空间点
  - Date/DateTime：日期时间
  - Duration：时间段
- 属性可以建立索引提高查询性能

### 1.3 约束 (Constraints)
- 唯一性约束：确保属性值唯一性
- 示例：`CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE`

## 2. 关系 (Relationship) 定义

关系连接节点，具有以下特征：

### 2.1 类型 (Types)
- 关系必须有一个类型
- 关系类型通常使用大写字母
- 示例：`:KNOWS`、`:WORKS_FOR`

### 2.2 属性
- 关系也可以有属性
- 属性数据类型与节点相同
- 可以为关系属性创建索引

### 2.3 方向性
- 关系有方向，但可以双向查询
- 格式：`(source)-[relationship]->(target)`

## 3. 索引 (Indexes)
- 支持节点和关系的属性索引
- 用于优化查询性能
- 示例：`CREATE INDEX person_name_idx IF NOT EXISTS FOR (n:Person) ON (n.name)`

## 4. 最佳实践
- 使用有意义的标签名
- 合理使用索引提升性能
- 根据查询模式设计数据模型
"""
