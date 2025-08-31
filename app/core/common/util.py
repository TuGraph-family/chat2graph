import json
import re
from typing import Any, Dict, List, Union
import uuid


def parse_jsons(
    text: str,
    start_marker: str = r"```(?:json)?\s*",
    end_marker: str = "```",
    placeholder_start_marker: str = "__PAYLOAD_START__",
    placeholder_end_marker: str = "__PAYLOAD_END__",
) -> List[Union[Dict[str, Any], json.JSONDecodeError]]:
    """Extracts and parses JSON objects enclosed within specified markers from a text string.

    This function is designed to robustly handle JSON content from LLMs. It finds
    content between `start_marker` and `end_marker`, cleans it, and parses it.

    Cleaning steps include:
    1.  Comment Removal (`// ...`).
    2.  Single-Quoted Key Fix (`'key':` -> `"key":`).
    3.  Trailing Comma Removal.
    4.  Control Character and BOM Removal.

    **Automatic Placeholder Feature for Complex Content:**
    This function includes a powerful "placeholder" mechanism to handle complex,
    multi-line string content (like code, HTML, or Markdown) without requiring the
    LLM to perform error-prone escaping. This feature is enabled by default.

    How it works:
    1.  The parser scans the raw JSON string for blocks enclosed by
        `placeholder_start_marker` (default: `__PAYLOAD_START__`) and
        `placeholder_end_marker` (default: `__PAYLOAD_END__`).
    2.  It extracts the raw content from within these markers and stores it.
    3.  It replaces the entire block (including markers) with a unique, quoted
        placeholder string (e.g., `"__PLACEHOLDER_uuid__"`). This makes the surrounding
        JSON syntactically valid for parsing.
    4.  It then proceeds with standard cleaning and parsing of the simplified JSON.
    5.  After successful parsing, it finds the placeholder string in the resulting
        Python object and injects the original raw content back.

    Example:
    text = '{"code": __PAYLOAD_START__\nprint("hello")\n__PAYLOAD_END__}'
    parse_jsons(text, start_marker='{', end_marker='}')
    # Result: [{'code': '\nprint("hello")\n'}]

    Args:
        text (str): The text string containing JSON content.
        start_marker (str): Regex pattern for the start of the JSON content.
        end_marker (str): The marker for the end of the JSON content.
        placeholder_start_marker (Optional[str]): The start marker for the complex block.
            Defaults to `__PAYLOAD_START__`. Set to `None` to disable.
        placeholder_end_marker (Optional[str]): The end marker for the complex block.
            Defaults to `__PAYLOAD_END__`.

    Returns:
        List[Union[Dict[str, Any], json.JSONDecodeError]]: A list of parsed JSON
            objects or `json.JSONDecodeError` instances.
    """
    # add re.MULTILINE flag to allow ^ to match start of lines
    json_pattern = f"{start_marker}(.*?){re.escape(end_marker)}"
    json_matches = re.finditer(json_pattern, text, re.DOTALL | re.MULTILINE)
    results: List[Union[Dict[str, Any], json.JSONDecodeError]] = []

    def find_and_replace_placeholders(obj: Any) -> None:
        """Recursively find and replace placeholders in the object."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value in extracted_payloads:
                    obj[key] = extracted_payloads[value]
                else:
                    find_and_replace_placeholders(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str) and item in extracted_payloads:
                    obj[i] = extracted_payloads[item]
                else:
                    find_and_replace_placeholders(item)

    for match in json_matches:
        json_str = match.group(1).strip()

        extracted_payloads: Dict[str, str] = {}

        use_placeholder_logic = placeholder_start_marker and placeholder_end_marker

        if use_placeholder_logic:
            placeholder_pattern = re.compile(
                f"{re.escape(placeholder_start_marker)}(.*?){re.escape(placeholder_end_marker)}",
                re.DOTALL,
            )

            # use a function for replacement to handle multiple occurrences
            def replace_with_placeholder(m):
                raw_content = m.group(1)
                # generate a unique placeholder for each match
                placeholder = f"__PLACEHOLDER_{uuid.uuid4().hex}__"
                extracted_payloads[placeholder] = raw_content
                # the replacement must be a valid JSON string value
                return f'"{placeholder}"'

            # replace all occurrences of the placeholder block
            json_str = placeholder_pattern.sub(replace_with_placeholder, json_str)

        try:
            # the rest of the cleaning logic remains the same
            # 1. remove comments
            lines = json_str.splitlines()
            cleaned_lines = []
            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith("//"):
                    continue
                in_quotes = False
                escaped = False
                comment_start_index = -1
                for i, char in enumerate(line):
                    if char == '"' and not escaped:
                        in_quotes = not in_quotes
                    elif char == "/" and not in_quotes:
                        if i + 1 < len(line) and line[i + 1] == "/":
                            comment_start_index = i
                            break
                    escaped = char == "\\" and not escaped
                if comment_start_index != -1:
                    cleaned_line = line[:comment_start_index].rstrip()
                else:
                    cleaned_line = line
                if cleaned_line.strip():
                    cleaned_lines.append(cleaned_line)
            json_str_no_comments = "\n".join(cleaned_lines)

            # 1.5 fix single-quoted keys
            json_str_fixed_keys = re.sub(
                r"(?<=[{,])(\s*)'([^']+)'(\s*:)", r'\1"\2"\3', json_str_no_comments
            )
            json_str_fixed_keys = re.sub(
                r"({)(\s*)'([^']+)'(\s*:)", r'\1\2"\3"\4', json_str_fixed_keys
            )

            # 2. fix trailing commas
            json_str_fixed_commas = re.sub(r",\s*(?=[\}\]])", "", json_str_fixed_keys)

            # 3. remove control characters and BOM
            json_str_cleaned_ctrl = re.sub(
                r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", json_str_fixed_commas
            )
            if json_str_cleaned_ctrl.startswith("\ufeff"):
                json_str_cleaned = json_str_cleaned_ctrl[1:]
            else:
                json_str_cleaned = json_str_cleaned_ctrl

            processed_json_for_error_reporting = json_str_cleaned
            if not processed_json_for_error_reporting.strip():
                continue

            # 4. parse the cleaned JSON string
            parsed_json = json.loads(processed_json_for_error_reporting)

            # post-processing to inject back the payloads
            if use_placeholder_logic and extracted_payloads:
                find_and_replace_placeholders(parsed_json)

            results.append(parsed_json)
        except json.JSONDecodeError as e:
            results.append(e)

    return results
