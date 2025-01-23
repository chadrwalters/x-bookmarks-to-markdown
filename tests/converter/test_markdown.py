"""Tests for markdown converter module."""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from xbm.converter.markdown import MarkdownConverter
from tests.utils.test_helpers import create_mock_bookmark, assert_markdown_format

@pytest.fixture
def converter(clean_test_dir):
    """Create MarkdownConverter instance for testing."""
    return MarkdownConverter(output_dir=clean_test_dir)

def test_convert_bookmark_basic(converter):
    """Test converting basic bookmark without media."""
    bookmark = create_mock_bookmark()
    content = converter.convert_bookmark(bookmark)

    assert_markdown_format(content)
    assert "@test_user" in content
    assert "Test tweet" in content
    assert "2024-01-01" in content

def test_convert_bookmark_with_media(converter):
    """Test converting bookmark with media."""
    bookmark = create_mock_bookmark(
        media=[
            {"type": "photo", "url": "test.jpg"},
            {"type": "video", "url": "test.mp4"}
        ]
    )
    content = converter.convert_bookmark(bookmark)

    assert "## Media" in content
    assert "[photo](test.jpg)" in content
    assert "[video](test.mp4)" in content

def test_save_bookmark(converter, clean_test_dir):
    """Test saving bookmark to file."""
    bookmark = create_mock_bookmark()
    output_path = converter.save_bookmark(bookmark)

    assert output_path.exists()
    content = output_path.read_text()
    assert_markdown_format(content)

    # Check filename format
    assert output_path.name.startswith("20240101-000000")
    assert output_path.name.endswith(".md")
    assert "test_user" in output_path.name
    assert bookmark["id"] in output_path.name

def test_format_text(converter):
    """Test formatting tweet text."""
    text = "Hello @user! Check out #hashtag"
    formatted = converter._format_text(text)

    assert "[@user](https://twitter.com/user)" in formatted
    assert "[#hashtag](https://twitter.com/hashtag/hashtag)" in formatted

def test_custom_media_dir(clean_test_dir):
    """Test using custom media directory."""
    converter = MarkdownConverter(
        output_dir=clean_test_dir
    )
    assert converter.output_dir == clean_test_dir

def test_template_placeholder():
    """Test template functionality (placeholder)."""
    # Template functionality to be implemented
    pass
