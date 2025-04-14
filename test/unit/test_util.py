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
    assert result[0]["key"] == "value"


def test_parse_jsons_custom_markers():
    """Test parse_jsons with custom start and end markers."""
    text = """
    Some text
    <json>
    {"key": "value"}
    </json>
    More text
    """
    result = parse_jsons(text, start_marker="<json>", end_marker="</json>")
    assert len(result) == 1
    assert result[0]["key"] == "value"


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
    assert result[0]["person"]["name"] == "John"
    assert result[0]["person"]["address"]["city"] == "New York"


def test_parse_jsons_invalid():
    """Test parse_jsons with invalid JSON content."""
    text = """
    ```json
    {"key": "value", "invalid": }
    ```
    """
    with pytest.raises(json.JSONDecodeError):
        parse_jsons(text)


def test_parse_jsons_empty():
    """Test parse_jsons with no JSON content."""
    text = "Some text without JSON markers"
    result = parse_jsons(text)
    assert len(result) == 0
