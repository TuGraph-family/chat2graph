import json
from typing import Dict


def parse_json(
    text: str, start_marker: str = "```json", end_marker: str = "```"
) -> Dict[str, Dict[str, str]]:
    """Extract JSON content from a text string.

    Args:
        text (str): The text string containing JSON content.
        start_marker (str): The marker indicating the start of the JSON content.
        end_marker (str): The marker indicating the end of the JSON content.

    Returns:
        Dict[str, Dict[str, str]]: The extracted JSON content as a dictionary.
    """
    start_idx = text.find(start_marker)
    if start_idx == -1:
        raise ValueError(f"Start marker '{start_marker}' not found in scratchpad.")

    json_start = start_idx + len(start_marker)
    end_idx = text.find(end_marker, json_start)
    if end_idx == -1:
        raise ValueError(f"End marker '{end_marker}' not found in scratchpad.")

    json_str = text[json_start:end_idx].strip()
    return json.loads(json_str)
