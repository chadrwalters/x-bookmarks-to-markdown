"""Test helper functions and utilities."""
import json
from pathlib import Path
from typing import Any, Dict

def create_mock_response(data: Dict[str, Any]) -> str:
    """Create a mock API response.

    Args:
        data: Response data to mock

    Returns:
        str: JSON string of mock response
    """
    return json.dumps(data)

def create_test_file(path: Path, content: str) -> None:
    """Create a test file with content.

    Args:
        path: Path to create file at
        content: Content to write to file
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

def create_mock_bookmark(
    id: str = "123",
    text: str = "Test tweet",
    author: str = "test_user",
    created_at: str = "2024-01-01T00:00:00Z",
    media: list = None
) -> Dict[str, Any]:
    """Create a mock bookmark response.

    Args:
        id: Tweet ID
        text: Tweet text
        author: Author username
        created_at: Creation timestamp
        media: List of media items

    Returns:
        Dict[str, Any]: Mock bookmark data
    """
    return {
        "id": id,
        "text": text,
        "author": {
            "username": author,
            "id": f"user_{id}"
        },
        "created_at": created_at,
        "media": media or []
    }

def assert_markdown_format(content: str) -> None:
    """Assert that content follows markdown format rules.

    Args:
        content: Markdown content to validate

    Raises:
        AssertionError: If content doesn't follow markdown rules
    """
    # Basic markdown rules
    assert content.startswith("#"), "Markdown should start with a heading"
    assert "\n\n" in content, "Markdown should have proper spacing"
    assert not content.endswith("\n\n"), "Markdown shouldn't end with blank lines"

    # Check for common markdown elements
    lines = content.split("\n")
    for line in lines:
        if line.startswith("#"):
            assert len(line.split()) > 1, "Headings should have content"
        if line.startswith("- "):
            assert len(line.split()) > 1, "List items should have content"
        if "]()" in line:
            assert False, "Links should have URLs"
