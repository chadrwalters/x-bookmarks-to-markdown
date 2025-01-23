"""Tests for test helper functions."""
import json
import pytest

from .test_helpers import (
    create_mock_response,
    create_test_file,
    create_mock_bookmark,
    assert_markdown_format
)

def test_create_mock_response():
    """Test creating mock API response."""
    data = {"key": "value"}
    response = create_mock_response(data)
    assert json.loads(response) == data

def test_create_test_file(clean_test_dir):
    """Test creating test file."""
    test_file = clean_test_dir / "test.txt"
    content = "test content"
    create_test_file(test_file, content)

    assert test_file.exists()
    assert test_file.read_text() == content

def test_create_mock_bookmark():
    """Test creating mock bookmark data."""
    # Test with defaults
    bookmark = create_mock_bookmark()
    assert bookmark["id"] == "123"
    assert bookmark["text"] == "Test tweet"
    assert bookmark["author"]["username"] == "test_user"

    # Test with custom values
    custom = create_mock_bookmark(
        id="456",
        text="Custom tweet",
        author="custom_user",
        media=[{"type": "photo", "url": "test.jpg"}]
    )
    assert custom["id"] == "456"
    assert custom["text"] == "Custom tweet"
    assert custom["author"]["username"] == "custom_user"
    assert len(custom["media"]) == 1

def test_assert_markdown_format():
    """Test markdown format validation."""
    # Valid markdown
    valid = """# Title\n\nContent paragraph\n\n- List item"""
    assert_markdown_format(valid)

    # Invalid markdown - no heading
    with pytest.raises(AssertionError):
        assert_markdown_format("Just content")

    # Invalid markdown - no spacing
    with pytest.raises(AssertionError):
        assert_markdown_format("# Title\nContent")

    # Invalid markdown - empty heading
    with pytest.raises(AssertionError):
        assert_markdown_format("#\n\nContent")

    # Invalid markdown - empty list item
    with pytest.raises(AssertionError):
        assert_markdown_format("# Title\n\n- ")

    # Invalid markdown - empty link
    with pytest.raises(AssertionError):
        assert_markdown_format("# Title\n\n[link]()")
