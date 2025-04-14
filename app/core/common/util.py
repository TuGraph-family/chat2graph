import json
import re
from typing import Any, Dict, List


def parse_jsons(
    text: str, start_marker: str = "```json", end_marker: str = "```"
) -> List[Dict[str, Any]]:
    """Extract JSON content from a text string.

    Args:
        text (str): The text string containing JSON content.
        start_marker (str): The marker indicating the start of the JSON content.
        end_marker (str): The marker indicating the end of the JSON content.

    Returns:
        List[Dict[str, Any]]: The extracted JSON content as a list of dictionaries
        if single or multiple matches are found.
    """
    # find all occurrences of content between markers
    pattern = f"{re.escape(start_marker)}(.*?){re.escape(end_marker)}"
    matches = re.finditer(pattern, text, re.DOTALL)
    results: List[Dict[str, Any]] = []

    for match in matches:
        json_str = match.group(1).strip()
        try:
            parsed_json = json.loads(json_str)
            results.append(parsed_json)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Error parsing JSON: {str(e)}", e.doc, e.pos)

    return results
