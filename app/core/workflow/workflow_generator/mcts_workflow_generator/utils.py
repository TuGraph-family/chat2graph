import json
from pathlib import Path
import re
from typing import Callable, Dict, List, Union

import yaml

from app.core.common.type import MessageSourceType
from app.core.common.util import parse_jsons
from app.core.model.message import ModelMessage
from app.core.reasoner.model_service_factory import ModelService
from app.core.sdk.agentic_service import AgenticService
from app.core.workflow.workflow_generator.mcts_workflow_generator.model import (
    AgenticConfigSection,
    ExecuteResult,
)


def load_agentic_service(optimized_path: str, round_num: int) -> AgenticService:
    workflow_path = optimized_path + f"/round{round_num}" + "/workflow.yml"
    mas = AgenticService.load(workflow_path)
    return mas


def load_config_dict(path: str, skip_section: List[AgenticConfigSection]) -> Dict[str, str]:
    try:
        with open(path, encoding="utf-8") as file:
            content = file.read()
            results = {}

        for section in AgenticConfigSection:
            if section in skip_section:
                continue
            section_name = str(section.value)
            # 匹配某个 key 到下一个顶级 key 或文件末尾
            pattern = re.compile(rf"(^|\n){section_name}:(.*?)(?=\n\w+:|\Z)", re.DOTALL)
            match = pattern.search(content)
            if match:
                results[section_name] = match.group(0).strip()

        return results
    except FileNotFoundError:
        print(f"Not found file: {path}")
        return {}
    except Exception as e:
        print(f"Error while reading file: {e}")
        return {}


def format_yaml_with_anchor(
    text: str, key: str, fields: List[str], need_anchor_name: bool = True
) -> str:
    if fields is None:
        fields = []
    anchor_pattern = re.compile(r"-\s*&(\w+)\s*\n")
    anchors: List[str] = []

    def capture_anchor(match: re.Match):
        anchor_name = match.group(1)
        anchors.append(anchor_name)
        return "- \n"

    text_without_anchor_def = anchor_pattern.sub(capture_anchor, text)

    text_cleaned = re.sub(r"\*(\w+)", r"\1", text_without_anchor_def)

    try:
        parsed_data = yaml.safe_load(text_cleaned)
        if not isinstance(parsed_data, Dict) or key not in parsed_data:
            raise ValueError(f"Cann't find {key} field.")
        yaml_list = parsed_data[key]
        if not isinstance(yaml_list, List):
            raise ValueError("'actions' is not a valid list")
    except yaml.YAMLError as e:
        raise ValueError(f"parse failed：{str(e)}") from e

    if need_anchor_name and len(anchors) != len(yaml_list):
        raise ValueError(
            f"length of anchors（{len(anchors)} unmatch length of actions list {len(yaml_list)}"
        )

    new_text: List[Dict] = []
    for idx, item in enumerate(yaml_list):
        info = {}
        if need_anchor_name:
            info["name"] = anchors[idx]
        extra_info: Dict = {field: item.get(field, "") for field in fields}
        info.update(extra_info)
        new_text.append(info)
    return json.dumps(new_text, indent=4, ensure_ascii=False)


JsonValue = Union[str, int, float, bool, None, Dict[str, "JsonValue"], List["JsonValue"]]


async def generate_json(
    model: ModelService,
    sys_prompt: str,
    messages: List[ModelMessage],
    max_retry: int = 3,
    filter: Callable[[List[JsonValue]], JsonValue] = lambda data: True,
    need_parse: bool = True,
) -> JsonValue:
    times = 0
    while times < max_retry:
        times += 1
        try:
            response = await model.generate(sys_prompt=sys_prompt, messages=messages)
            resp_str = response.get_payload()
            if need_parse:
                parsed_strs = parse_jsons(resp_str)
                for strs in parsed_strs:
                    if isinstance(strs, json.JSONDecodeError):
                        raise Exception(f"{strs}")
                valid_strs: List[JsonValue] = [
                    strs for strs in parsed_strs if not isinstance(strs, json.JSONDecodeError)
                ]
            return filter(valid_strs)
        except Exception as e:
            print(f"[generate_json] failed, reason={e}, str = {resp_str}, times={times}")
            messages.append(
                ModelMessage(
                    payload=resp_str,
                    source_type=MessageSourceType.MODEL,
                    job_id=messages[-1].get_job_id(),
                    step=messages[-1].get_step(),
                )
            )
            messages.append(
                ModelMessage(
                    payload=f"When parse and filter json encounter exception={e}, \
                        please output the right json format.",
                    source_type=MessageSourceType.MODEL,
                    job_id=messages[-1].get_job_id(), 
                    step=messages[-1].get_step() + 1,
                )
            )
    return None


def load_execute_result(path: Path) -> List[ExecuteResult]:
    with open(path, encoding="utf-8") as f:
        reuslts = json.load(f)

    execute_results: List[ExecuteResult] = []
    for result in reuslts:
        execute_results.append(ExecuteResult.model_validate(result))

    return execute_results
