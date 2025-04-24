import json
import re
from typing import Any, Dict, List, Union


def parse_jsons(
    text: str,
    start_marker: str = r"```(?:json)?\s*",
    end_marker: str = "```",
) -> List[Union[Dict[str, Any], json.JSONDecodeError]]:
    """Extracts and parses JSON objects enclosed within specified markers from a text string.

    This function is designed to robustly handle JSON content often found in the output
    of Large Language Models (LLMs), which may include common deviations from strict
    JSON syntax. It iterates through the text, finds all occurrences of content
    between the start and end markers, and attempts to parse each block as JSON.

    Before parsing, the function applies several cleaning steps to increase the
    likelihood of successful parsing:
    1.  Comment Removal: Removes single-line comments (`// ...`) that start at the
        beginning of a line (after optional whitespace) or appear after JSON code,
        taking care not to remove `//` sequences within string literals.
    2.  Single-Quoted Key Fix: Converts single quotes around keys (e.g., `'key':`)
        to double quotes (`"key":`), a common LLM formatting error.
    3.  Trailing Comma Removal: Removes trailing commas found immediately before
        closing braces (`}`) or brackets (`]`).
    4.  Control Character Removal: Strips most ASCII control characters
        (U+0000 to U+001F), excluding tab, newline, and carriage return.

    If a block successfully parses after cleaning, the resulting Python dictionary or
    list is added to the results. If parsing fails even after cleaning, an error
    tuple is added, containing a descriptive error message, the original
    `json.JSONDecodeError`, and the final string content that failed to parse.

    Note: This function does NOT handle multi-line block comments (`/* ... */`) or
    more complex JSON syntax errors beyond those explicitly listed (e.g., missing
    commas between elements, unescaped quotes within string values, single quotes
    around string values).

    Args:
        text (str): The text string containing JSON content.
        start_marker (str): Regex pattern indicating the start of the JSON content.
            It allows ```json or ``` possibly followed by whitespace. Defaults to match ```json
            or ``` followed by optional whitespace.
        end_marker (str): The marker indicating the end of the JSON content.

    Returns:
        List[Union[Dict[str, Any], json.JSONDecodeError]]: A list of parsed JSON
            objects or error tuples. Each error tuple contains a message, the original exception,
            and the processed string that failed parsing. If no JSON content is found,
            an empty list is returned.
    """
    # add re.MULTILINE flag to allow ^ to match start of lines
    json_pattern = f"{start_marker}(.*?){re.escape(end_marker)}"
    json_matches = re.finditer(json_pattern, text, re.DOTALL | re.MULTILINE)
    results: List[Union[Dict[str, Any], json.JSONDecodeError]] = []
    processed_json_for_error_reporting = ""

    for match in json_matches:
        json_str = match.group(1).strip()
        try:
            # 1. remove full-line and trailing comments carefully
            lines = json_str.splitlines()
            cleaned_lines = []
            for line in lines:
                stripped_line = line.strip()
                # skip lines that are entirely comments
                if stripped_line.startswith("//"):
                    continue

                # remove trailing comments, being careful about quotes
                in_quotes = False
                escaped = False
                comment_start_index = -1
                for i, char in enumerate(line):
                    if char == '"' and not escaped:
                        in_quotes = not in_quotes
                    elif char == "/" and not in_quotes:
                        # check if the next character is also '/'
                        if i + 1 < len(line) and line[i + 1] == "/":
                            comment_start_index = i
                            break  # found the start of a comment outside quotes
                    # handle escape character (only backslash matters for quotes)
                    escaped = char == "\\" and not escaped

                if comment_start_index != -1:
                    # remove comment and trailing whitespace before it
                    cleaned_line = line[:comment_start_index].rstrip()
                else:
                    cleaned_line = line  # no comment found on this line

                # only add non-empty lines after potential comment removal
                if cleaned_line.strip():
                    cleaned_lines.append(cleaned_line)

            json_str_no_comments = "\n".join(cleaned_lines)

            # 1.5 attempt to fix single-quoted keys (common LLM error)
            # use fixed-width lookbehind. Match whitespace outside lookbehind.
            # pattern breakdown:
            # (?<=[{,])  - Positive lookbehind for { or , (fixed width)
            # (\s*)      - Capture group 1: any whitespace after { or ,
            # '([^']+)'  - Capture group 2: the single-quoted key
            # (\s*:)     - Capture group 3: any whitespace followed by the colon
            json_str_fixed_keys = re.sub(
                r"(?<=[{,])(\s*)'([^']+)'(\s*:)", r'\1"\2"\3', json_str_no_comments
            )
            # also handle the case where the single-quoted key is the *first* key in the object
            # pattern breakdown:
            # ({)        - Capture group 1: the opening brace
            # (\s*)      - Capture group 2: any whitespace after {
            # '([^']+)'  - Capture group 3: the single-quoted key
            # (\s*:)     - Capture group 4: any whitespace followed by the colon
            json_str_fixed_keys = re.sub(
                r"({)(\s*)'([^']+)'(\s*:)", r'\1\2"\3"\4', json_str_fixed_keys
            )

            # 2. attempt to fix trailing commas before parsing using lookahead
            json_str_fixed_commas = re.sub(r",\s*(?=[\}\]])", "", json_str_fixed_keys)

            # 3. remove ASCII control characters (except tab, newline, carriage return)
            json_str_cleaned_ctrl = re.sub(
                r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", json_str_fixed_commas
            )

            # 3.5 remove potential BOM (\ufeff) at the start
            if json_str_cleaned_ctrl.startswith("\ufeff"):
                json_str_cleaned = json_str_cleaned_ctrl[1:]
            else:
                json_str_cleaned = json_str_cleaned_ctrl

            # store the version we are about to parse for potential error reporting
            processed_json_for_error_reporting = json_str_cleaned

            # 4. attempt to parse the cleaned JSON string
            if not processed_json_for_error_reporting.strip():
                continue  # skip empty strings resulting from comment removal etc.

            parsed_json = json.loads(processed_json_for_error_reporting)
            results.append(parsed_json)
        except json.JSONDecodeError as e:
            # if parsing fails, append the enhanced error tuple
            results.append(e)

    return results
