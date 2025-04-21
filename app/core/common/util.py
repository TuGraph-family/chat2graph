import json
import re
from typing import Any, Dict, List, Union


def parse_jsons(
    text: str,
    start_marker: str = "```json",
    end_marker: str = "```",
) -> List[Union[Dict[str, Any], json.JSONDecodeError]]:
    """Extract JSON content from a text string.

    Args:
        text (str): The text string containing JSON content.
        start_marker (str): The marker indicating the start of the JSON content.
        end_marker (str): The marker indicating the end of the JSON content.

    Returns:
        List[Union[Dict[str, Any], json.JSONDecodeError]]: A list of parsed JSON objects or
            error messages. Each JSON object is represented as a dictionary. If no JSON content
            is found, an empty list is returned.
    """
    # find all occurrences of content between markers
    json_pattern = f"{re.escape(start_marker)}(.*?){re.escape(end_marker)}"
    json_matches = re.finditer(json_pattern, text, re.DOTALL)
    results: List[Union[Dict[str, Any], json.JSONDecodeError]] = []

    for match in json_matches:
        json_str = match.group(1).strip()
        try:
            # attempt to fix trailing commas before parsing using lookahead
            # remove comma and trailing whitespace if followed by } or ]
            json_str_fixed = re.sub(r",\s*(?=[\}\]])", "", json_str)

            parsed_json = json.loads(json_str_fixed)
            results.append(parsed_json)
        except json.JSONDecodeError as e:
            results.append(e)

    return results
