import json

import pytest

from app.core.common.util import parse_jsons


def test_parse_jsons_basic():
    """Test basic functionality of parse_jsons with default markers."""
    text = """
    Some text
    ```json
    {"key": "value"}
    ```
    More text
    """
    result = parse_jsons(text)
    assert len(result) == 1
    assert not isinstance(result[0], json.JSONDecodeError)
    assert result[0]["key"] == "value"


def test_parse_jsons_custom_markers():
    """Test parse_jsons with custom start and end markers, including comments and trailing comma."""
    text = """
    <shallow_thinking>
        Understanding: The user instructs me to call the `query_system_status()` function.  
        Input processing: There is no additional input information, which complies with the requirement that the `query_system_status()` function does not need parameters.  
        Action: I will generate a `<function_call>` to invoke the `query_system_status()` function as instructed.
    </shallow_thinking>
    <action>
        <function_call>
        {
            "name": "query_system_status",
            "call_objective": "Obtain the current system status for subsequent task decomposition.",
            "args": {}
        }
        </function_call>
    </action>

    More text.

    <function_call>
    {"another_call": "test",} // Trailing comma removed
    </function_call>
    """  # noqa: E501
    result = parse_jsons(
        text, start_marker=r"^\s*<function_call>\s*", end_marker="</function_call>"
    )
    assert len(result) == 2
    assert isinstance(result[0], dict)
    assert result[0]["name"] == "query_system_status"
    assert isinstance(result[1], dict)
    assert result[1]["another_call"] == "test"


def test_parse_jsons_multiple():
    """Test parse_jsons with multiple JSON blocks."""
    text = """
    ```json
    {"id": 1, "name": "first"}
    ```
    Some text in between
    ```json
    {"id": 2, "name": "second"}
    ```
    """
    result = parse_jsons(text)
    assert len(result) == 2
    assert not isinstance(result[0], json.JSONDecodeError)
    assert not isinstance(result[1], json.JSONDecodeError)
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2
    assert result[0]["name"] == "first"
    assert result[1]["name"] == "second"


def test_parse_jsons_nested():
    """Test parse_jsons with nested JSON structures."""
    text = """
    ```json
    {
        "person": {
            "name": "John",
            "age": 30,
            "address": {
                "city": "New York",
                "country": "USA"
            }
        }
    }
    ```
    """
    result = parse_jsons(text)
    assert len(result) == 1
    assert not isinstance(result[0], json.JSONDecodeError)
    assert result[0]["person"]["name"] == "John"
    assert result[0]["person"]["address"]["city"] == "New York"


def test_parse_jsons_invalid_syntax():
    """Test parse_jsons with invalid JSON syntax (missing closing brace)."""
    text = """
    ```json
    {"invalid": "json" // Missing closing brace
    ```
    """
    result = parse_jsons(text)
    assert len(result) == 1
    # expecting an error original_exception
    assert isinstance(result[0], json.JSONDecodeError)


def test_parse_jsons_no_language_identifier():
    """Test parsing JSON block without the 'json' language identifier."""
    text = """
    ```
    {
        "name": "John Doe", // Example comment
        "age": 30,
        "city": "New York" // Another comment
    }
    ```
    """
    result = parse_jsons(text)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert result[0] == {"name": "John Doe", "age": 30, "city": "New York"}


def test_parse_jsons_trailing_comments_and_comma():
    """Test parsing with various trailing comments and a trailing comma."""
    text = """
    ```json
    {
        "url": "http://example.com", // Trailing comment (removed)
        "comment": "This // should remain as it's inside a string", // Trailing comment (removed)
        // Full line comment (removed)
        "valid": true, // Trailing comment (removed)
        "data": [
            1, // Trailing comment (removed)
            2 // Trailing comment (removed)
        ], // Trailing comma after array (removed by fixer)
        "last": "value" // No trailing comma needed here
    }
    ```
    """
    result = parse_jsons(text)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    expected = {
        "url": "http://example.com",
        "comment": "This // should remain as it's inside a string",
        "valid": True,
        "data": [1, 2],
        "last": "value",
    }
    assert result[0] == expected


def test_parse_jsons_llm_errors_single_quotes_value():
    """Test common LLM errors: single quotes for value, missing comma (expect failure)."""
    # note: Single quoted keys are fixed, but single quoted values and missing commas are not.
    text = """
    ```json
    {
        'name': "Alice", // Fixed
        "age": 30 // Missing comma before next key
        "city": 'Bob's Town', // Invalid single quotes for value
        "valid": true, // Trailing comma fixed
    }
    ```
    """
    result = parse_jsons(text)
    assert len(result) == 1
    assert isinstance(result[0], json.JSONDecodeError)  # expect error tuple


def test_parse_jsons_comment_in_string():
    """Test that '//' inside a string literal is preserved."""
    text = """
    ```json
    {
        "url": "http://example.com/path", // This trailing comment is removed correctly
        "script": "var x = '//not_a_comment';", // This should be preserved
        "valid": true
    }
    ```
    """
    result = parse_jsons(text)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert result[0]["script"] == "var x = '//not_a_comment';"
    assert result[0]["url"] == "http://example.com/path"
    assert result[0]["valid"] is True


def test_parse_jsons_first_key_single_quoted():
    """Test fixing single quotes when it's the first key."""
    text = """
    ```json
    {
        'first_key': "value1", // Single quotes for the very first key
        "second_key": "value2"
    }
    ```
    """
    result = parse_jsons(text)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert result[0] == {"first_key": "value1", "second_key": "value2"}


def test_parse_jsons_mixed_valid_invalid():
    """Test handling of multiple blocks where one is invalid."""
    text = """
    ```json
    {"valid": true}
    ```
    ```json
    {"invalid": "json,"} // comment, but still valid JSON string value
    ```
    """
    # this case was previously marked as failing, but {"invalid": "json,"} is valid JSON.
    # the comment removal works correctly.
    result = parse_jsons(text)
    assert len(result) == 2
    assert isinstance(result[0], dict)
    assert result[0] == {"valid": True}
    assert isinstance(result[1], dict)
    assert result[1] == {"invalid": "json,"}


def test_parse_jsons_python_code_block():
    """Test handling of Python code block with JSON-like content."""
    text = """
<function_call>
{
    "name": "execute_code",
    "call_objective": "计算每种住宿类型的平均评分，并找出平均评分最高的住宿类型。",
    "args": {
        "code": "parsed_data = {'酒店': [5, 5, 4, 3, 2], '汽车旅馆': [5, 3, 2, 1, 0], '出租房屋': [4, 3, 4, 5, 5, 4, 3, 3, 3, 1], '露营地': [4, 5, 3, 4, 1]}\\n\\naverage_ratings = {}\\nfor acc_type, ratings in parsed_data.items():\\n    if ratings:\\n        average_ratings[acc_type] = sum(ratings) / len(ratings)\\n    else:\\n        average_ratings[acc_type] = 0.0 # Handle cases with no ratings\\n\\nhighest_avg_type = None\\nmax_avg_rating = -1\\n\\nfor acc_type, avg_rating in average_ratings.items():\\n    if avg_rating > max_avg_rating:\\n        max_avg_rating = avg_rating\\n        highest_avg_type = acc_type\\n\\nprint(\\\"每种住宿类型的平均评分：\\\")\\nfor acc_type, avg_rating in average_ratings.items():\\n    print(\\\"  {}: {:.2f}\\\".format(acc_type, avg_rating))\\n\\nprint(\\\"\\\\n平均评分最高的住宿类型是：{} (平均评分: {:.2f})\\\".format(highest_avg_type, max_avg_rating))\\n"
    }
}
</function_call>
    """  # noqa: E501
    result = parse_jsons(text, start_marker="<function_call>", end_marker="</function_call>")
    assert len(result) == 1


def test_parse_jsons_empty():
    """Test parse_jsons with no JSON content."""
    text = "Some text without JSON markers"
    result = parse_jsons(text)
    assert len(result) == 0


@pytest.fixture
def complex_code_payload():
    """Fixture to provide a complex code payload for testing."""
    return """
def process_data(data):
    # This is a comment inside the code
    if "special_key" in data:
        print(f"Found special key with value: {data['special_key']}")
    return {"status": "processed", "items": len(data)}
"""


def test_default_placeholder_markers(complex_code_payload):
    """Tests the default placeholder markers `__PAYLOAD_START__` and `__PAYLOAD_END__`."""
    text = f"""
    ```json
    {{
        "action": "execute_code",
        "code": __PAYLOAD_START__{complex_code_payload}__PAYLOAD_END__
    }}
    ```
    """
    result = parse_jsons(text)  # Use default markers
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert result[0]["action"] == "execute_code"
    assert result[0]["code"] == complex_code_payload


def test_custom_placeholder_markers():
    """Tests using custom placeholder markers for a different type of content."""
    html_content = "<div class='main'>\n  <h1>Title</h1>\n</div>"
    text = f"""
    ```
    {{
        "type": "html",
        "template": __HTML__{html_content}__END_HTML__
    }}
    ```
    """
    result = parse_jsons(
        text,
        placeholder_start_marker="__HTML__",
        placeholder_end_marker="__END_HTML__",
    )
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert result[0]["type"] == "html"
    assert result[0]["template"] == html_content


def test_placeholder_in_array(complex_code_payload):
    """Tests a placeholder block appearing inside a JSON array."""
    sql_query = "SELECT * FROM users WHERE country = 'US';"
    text = f"""
    ```
    {{
        "steps": [
            {{ "type": "sql", "query": __PAYLOAD_START__{sql_query}__PAYLOAD_END__ }},
            {{ "type": "python", "code": __PAYLOAD_START__{complex_code_payload}__PAYLOAD_END__ }}
        ]
    }}
    ```
    """
    result = parse_jsons(text)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert len(result[0]["steps"]) == 2
    assert result[0]["steps"][0]["type"] == "sql"
    assert result[0]["steps"][0]["query"] == sql_query
    assert result[0]["steps"][1]["type"] == "python"
    assert result[0]["steps"][1]["code"] == complex_code_payload


def test_multiple_placeholders_in_one_json():
    """Tests multiple, different placeholder blocks in the same JSON object."""
    text = """
    ```
    {
        "code": __PAYLOAD_START__print("hello")__PAYLOAD_END__,
        "explanation": __PAYLOAD_START__This is a multi-line
explanation.__PAYLOAD_END__
    }
    ```
    """
    result = parse_jsons(text)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert result[0]["code"] == 'print("hello")'
    assert result[0]["explanation"] == "This is a multi-line\nexplanation."
