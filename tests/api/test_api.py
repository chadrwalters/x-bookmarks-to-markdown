"""Tests for API client module."""
from unittest.mock import MagicMock, patch

import pytest
import tweepy
from tweepy import Response

from xbm.api.client import BookmarkClient

@pytest.fixture
def mock_client():
    """Create mock Tweepy client."""
    return MagicMock(spec=tweepy.Client)

@pytest.fixture
def bookmark_client(mock_client):
    """Create BookmarkClient instance for testing."""
    return BookmarkClient(mock_client)

def test_get_bookmarks_single_page(bookmark_client, mock_client):
    """Test getting bookmarks with single page."""
    # Mock response with no next token
    mock_response = MagicMock(spec=Response)
    mock_response.meta = {}
    mock_client.get_bookmarks.return_value = mock_response

    responses = list(bookmark_client.get_bookmarks())

    assert len(responses) == 1
    assert responses[0] == mock_response
    mock_client.get_bookmarks.assert_called_once()

def test_get_bookmarks_pagination(bookmark_client, mock_client):
    """Test getting bookmarks with pagination."""
    # Mock responses with pagination
    mock_response1 = MagicMock(spec=Response)
    mock_response1.meta = {"next_token": "token1"}

    mock_response2 = MagicMock(spec=Response)
    mock_response2.meta = {}

    mock_client.get_bookmarks.side_effect = [mock_response1, mock_response2]

    responses = list(bookmark_client.get_bookmarks())

    assert len(responses) == 2
    assert responses[0] == mock_response1
    assert responses[1] == mock_response2
    assert mock_client.get_bookmarks.call_count == 2

def test_get_bookmarks_retry_success(bookmark_client, mock_client):
    """Test successful retry after failure."""
    mock_response = MagicMock(spec=Response)
    mock_response.meta = {}

    mock_client.get_bookmarks.side_effect = [
        tweepy.TweepyException("Rate limit"),
        mock_response
    ]

    responses = list(bookmark_client.get_bookmarks())

    assert len(responses) == 1
    assert responses[0] == mock_response
    assert mock_client.get_bookmarks.call_count == 2

def test_get_bookmarks_retry_failure(bookmark_client, mock_client):
    """Test retry exhaustion."""
    mock_client.get_bookmarks.side_effect = tweepy.TweepyException("Rate limit")

    with pytest.raises(tweepy.TweepyException):
        list(bookmark_client.get_bookmarks())

    assert mock_client.get_bookmarks.call_count == 3  # Initial + 2 retries
