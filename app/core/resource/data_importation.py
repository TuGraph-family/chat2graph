import json
import re
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.common.system_env import SystemEnv
from app.core.model.message import ModelMessage
from app.core.reasoner.model_service_factory import ModelServiceFactory
from app.core.toolkit.tool import Tool
from app.plugin.tugraph.tugraph_store import get_tugraph

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

        result = f"{SCHEMA_BOOK}\n\n查询成功，得到当下的图 schema：\n" + json.dumps(
            json.loads(schema[0][0])["schema"], indent=4, ensure_ascii=False
        )

        return result


class CypherExecutor(Tool):
    """Tool for validating and executing TuGraph Cypher schema definitions."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.validate_and_execute_cypher.__name__,
            description=self.validate_and_execute_cypher.__doc__ or "",
            function=self.validate_and_execute_cypher,
        )

    async def validate_and_execute_cypher(self, cyphers: List[str], **kargs) -> str:
        """Validate the TuGraph Cypher and execute it in the TuGraph Database.
        Make sure the input cypher is only the code without any other information including ```Cypher``` or ```TuGraph Cypher```.
        This function can only execute one cypher schema at a time.
        If the schema is valid, return the validation results. Otherwise, return the error message.

        Args:
            cypher (str): TuGraph Cypher including only the code.

        Returns:
            Validation and execution results.
        """

        print("\n".join(cyphers))
        try:
            store = get_tugraph()
            for cypher in cyphers:
                print(f"result: {(store.conn.run(cypher)[0])}")
            return f"TuGraph 导入数据成功，成功运行如下指令：\n{'  '.join(cyphers)}"
        except Exception as e:
            prompt = (
                SCHEMA_BOOK
                + f"""假设你是 TuGraph DB 的管理员，经过数据库执行，得到的语句出现了报错，你需要给我信息反馈。

标准不要太严格，只要不和 TuGraph Cypher 语法冲突就行。最好是具体的修改提示，而不是泛泛而谈，只谈数据导入的问题。schema 是无法修改的。
我只能修改调用函数的参数，不能修改和查看调用函数的内部逻辑、graph schema 和数据库已有的数据。
信息反馈的部分中，需要返回错误信息，针对调用函数的参数的修改提示。

经过 TuGraph 内置的验证器，得到了执行错误：
{str(e)}

原始的执行语句（这些语句是由调用函数的参数转化而来的）：
{cyphers}

调用函数的参数：
{kargs}

你的最终回答是：由函数拼接出的 Cypher 语法不合规，然后给出错误信息和针对调用函数的参数的修改提示，而不仅仅是只传递错误信息。
"""  # noqa: E501
            )

            message = ModelMessage(payload=cypher, timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"))

            _model = ModelServiceFactory.create(platform_type=SystemEnv.PLATFORM_TYPE)
            response = await _model.generate(sys_prompt=prompt, messages=[message])
            raise Exception(response.get_payload())


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
            - Use the pingyin (by CamelCase naming) for the field if it is related to the identity
                instead of the number (e.g., "LiuBei" for person_id, instead of "1")

        Processing Mechanism:
            - Data is processed one triple at a time (source node, target node, and their relationship)
            - For each relationship, the function will:
                1. Find matching source and target entities
                2. Create/update the source node
                3. Create/update the target node
                4. Create/update the relationship

        Args:
            source_label (str): Label of the source node (e.g., "Person"), defined in the graph schema
            source_primary_key (str): Primary key of the source node (e.g., "id")
            source_properties (Dict[str, Any]): Properties of the source node, including:
                - some_primary_key_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - some_not_optional_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - Other related fields as defined in schema
            target_label (str): Label of the target node, defined in the graph schema
            target_primary_key (str): Primary key of the target node
            target_properties (Dict[str, Any]): Properties of the target node, including:
                - some_primary_key_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - some_not_optional_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - Other related fields as defined in schema
            relationship_label (str): Label of the relationship, defined in the graph schema
            relationship_properties (Dict[str, Any]): Properties of the relationship, including:
                - some_primary_key_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - some_not_optional_field (str): Required field. If it is related to the identity of
                    the entity, it should be in pingyin (by CamelCase naming)
                - Other related fields as defined in schema

        Returns:
            str: Summary of the import operation, including counts of entities and relationships
                processed, created, and updated.
        """

        def format_date(value: str) -> str:
            """Format date value to ensure it has a leading zero in the year."""
            # match date format like "XXX-XX-XX" or "XXX-XX-XXTxx:xx:xxZ"
            date_pattern = r"^(\d{3})-(\d{2})-(\d{2})(T[\d:]+Z)?$"
            match = re.match(date_pattern, value)
            if match:
                year = match.group(1)
                if len(year) == 3:
                    # add leading zero to three-digit year
                    time_part = match.group(4) or ""
                    return f"0{year}-{match.group(2)}-{match.group(3)}{time_part}"
            return value

        def format_property(key: str, value: Any) -> str:
            """Format property key-value pair for Cypher query."""
            if value is None:
                return f"{key}: null"
            elif isinstance(value, int | float):
                return f"{key}: {value}"
            else:
                str_value = str(value)
                if (
                    isinstance(str_value, str)
                    and str_value
                    and (key in ["date", "start_date", "end_date", "start_time"])
                ):
                    str_value = format_date(str_value)
                str_value = str_value.replace("'", "\\'")
                return f"{key}: '{str_value}'"

        def generate_property_string(properties: Dict[str, Any]) -> str:
            """Generate formatted property string for Cypher query."""
            return ", ".join(format_property(k, v) for k, v in properties.items())

        # process source node
        # source_properties["id"] = str(uuid4())
        source_props_str = generate_property_string(source_properties)
        source_statement = f"CALL db.upsertVertex('{source_label}', [{{{source_props_str}}}])"

        # process target node
        # target_properties["id"] = str(uuid4())
        target_props_str = generate_property_string(target_properties)
        target_statement = f"CALL db.upsertVertex('{target_label}', [{{{target_props_str}}}])"

        # process relationship
        rel_props = {
            **relationship_properties,
            "source_node": source_properties[source_primary_key],
            "target_node": target_properties[target_primary_key],
        }
        rel_props_str = generate_property_string(rel_props)

        rel_statement = (
            f"CALL db.upsertEdge('{relationship_label}', "
            f"{{type: '{source_label}', key: 'source_node'}}, "
            f"{{type: '{target_label}', key: 'target_node'}}, "
            f"[{{{rel_props_str}}}])"
        )

        cypher_executor = CypherExecutor()
        return await cypher_executor.validate_and_execute_cypher(
            [source_statement, target_statement, rel_statement],
            source_label=source_label,
            source_primary_key=source_primary_key,
            source_properties=source_properties,
            target_label=target_label,
            target_primary_key=target_primary_key,
            target_properties=target_properties,
            relationship_label=relationship_label,
            relationship_properties=relationship_properties,
        )


SCHEMA_BOOK = """
# 图数据库 Schema 指南 (LLM 友好版)

本指南旨在帮助你理解和设计图数据库的 Schema，以便 LLM (语言模型) 更好地理解图数据的结构。

## 1. 顶点 (Vertex) 定义 (实体定义)

在图数据库中，**顶点 (Vertex)** 代表 **实体 (Entity)**，是图结构中的基本单元。 每个 **顶点类型** 的定义描述了具有相同特征的实体的结构。

### 1.1. 顶点类型要素

每个 **顶点类型** 定义包含以下关键要素：

- **标签 (Label):**
    - **定义:**  **标签 (Label)** 是 **顶点类型** 的名称或标识符。它用于区分不同类型的实体。
    - **示例:** 例如，`"Person"` (人), `"Event"` (事件), `"Location"` (地点), `"Organization"` (组织) 等都是常见的 **顶点标签 (Vertex Label)**。
    - **JSON Schema 示例:** 在提供的 JSON Schema 中，`"label": "Person"`  定义了一个 **顶点类型** 的标签为 `"Person"`。

- **主键 (Primary Key):**
    - **定义:**  **主键 (Primary Key)** 是 **顶点类型** 的唯一标识属性。它用于在图中唯一地识别每个顶点实例。
    - **重要性:**  **主键** 必须是唯一的，并且通常选择一个核心属性作为 **主键**。
    - **示例:**  例如，`"person_id"` 可以作为 `"Person"` **顶点类型** 的 **主键**， `"event_id"` 可以作为 `"Event"` **顶点类型** 的 **主键**。
    - **JSON Schema 示例:**  在 JSON Schema 中，`"primary": "person_id"`  指定 `"person_id"` 属性为 `"Person"` **顶点类型** 的 **主键**。

- **属性 (Properties):**
    - **定义:**  **属性 (Properties)** 描述了 **顶点** 的特征或信息。每个 **顶点类型** 可以包含多个 **属性**。
    - **属性要素:**  每个 **属性** 定义包含以下子要素：
        - **名称 (name):**  **属性** 的标识符，例如 `"name"`, `"description"`, `"occurrence_time"` 等。
        - **数据类型 (type):**  **属性** 存储的数据类型，例如 `"STRING"` (字符串), `"INTEGER"` (整数), `"DATE"` (日期) 等。
        - **可选性 (optional):**  标记 **属性** 是否可以为空。`true` 表示可选，`false` 表示必填。
        - **索引 (index):**  标记 **属性** 是否创建索引以优化查询性能。`true` 表示创建索引。
        - **唯一性 (unique):**  标记 **属性** 值在同类型顶点中是否唯一。`true` 表示唯一。
    - **JSON Schema 示例:**  在 JSON Schema 中，`"properties": [...]`  数组定义了 **顶点类型** 的所有 **属性**，例如 `"name": {"name": "name", "type": "STRING", "optional": false}` 定义了一个名为 `"name"`，类型为 `"STRING"`，非可选的属性。

## 2. 边 (Edge) 定义 (关系定义)

在图数据库中，**边 (Edge)** 代表 **关系 (Relationship)**，用于连接不同的 **顶点 (Vertex)**，表达实体之间的联系。 每个 **边类型** 的定义描述了具有相同联系类型的关系结构。

### 2.1. 边类型要素

每个 **边类型** 定义包含以下关键要素：

- **标签 (Label):**
    - **定义:**  **标签 (Label)** 是 **边类型** 的名称或标识符。它用于区分不同类型的关系。
    - **示例:** 例如， `"Relationship"` (关系) 可以作为一个通用的 **边标签 (Edge Label)**， 或者更具体的标签如 `"LOCATED_IN"` (位于...), `"WORKS_FOR"` (工作于...) 等。
    - **JSON Schema 示例:** 在提供的 JSON Schema 中，`"label": "Relationship"`  定义了一个 **边类型** 的标签为 `"Relationship"`。

- **约束 (Constraints):**
    - **定义:**  **约束 (Constraints)**  定义了 **边类型** 可以连接的 **顶点类型** 对。它限制了关系的连接对象类型。
    - **重要性:**  **约束** 确保了关系的有效性和数据一致性。
    - **注意事项:**  **约束** 可以包含多个 **顶点类型** 对，表示 **边类型** 可以连接的多种 **顶点类型** 组合。并且，边的连接方向是有序的，即 `(source, target)` 和 `(target, source)` 是不同的。
    - **示例:**  例如，`"Relationship"`  **边类型** 的 **约束**  `[["Person", "Event"], ["Event", "Location"], ["Person", "Organization"]]` 表示：
        - `"Relationship"` 边可以连接 `"Person"` 类型的顶点 和 `"Event"` 类型的顶点。
        - `"Relationship"` 边可以连接 `"Event"` 类型的顶点 和 `"Location"` 类型的顶点。
        - `"Relationship"` 边可以连接 `"Person"` 类型的顶点 和 `"Organization"` 类型的顶点。
    - **JSON Schema 示例:**  在 JSON Schema 中，`"constraints": [[ "Person", "Event" ], ... ]`  定义了 `"Relationship"` **边类型** 的 **约束**。

- **属性分离 (Detach Property):**
    - **定义:**  `"detach_property": true`  标记 **边类型** 的 **属性** 是否可以独立于边本身存储。
    - **用途:**  `detach_property`  通常用于优化存储和性能，尤其是在属性数据量较大时。
    - **JSON Schema 示例:**  在 JSON Schema 中，`"detach_property": true` 表示启用了属性分离。

- **属性 (Properties):**
    - **定义:**  **属性 (Properties)** 描述了 **边** 的特征或信息。 每个 **边类型** 也可以包含多个 **属性**。
    - **属性要素:**  **边属性** 的结构和要素与 **顶点属性** 相同，包括 **名称 (name)**, **数据类型 (type)**, **可选性 (optional)** 等。
    - **示例:**  例如，`"relationship_id"`, `"description"`, `"strength"`, `"type"` 可以作为 `"Relationship"` **边类型** 的 **属性**。
    - **JSON Schema 示例:**  在 JSON Schema 中，`"properties": [...]`  数组定义了 **边类型** 的所有 **属性**，例如 `"type": {"name": "type", "type": "STRING", "optional": false}` 定义了一个名为 `"type"`，类型为 `"STRING"`，非可选的属性。

"""  # noqa: E501
