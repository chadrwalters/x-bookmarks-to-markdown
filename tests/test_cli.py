"""Tests for command-line interface."""
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import click
import pytest
from click.testing import CliRunner
import tweepy
import asyncio

from xbm.cli import auth, cli, download

@pytest.fixture(autouse=True)
def allow_insecure_transport():
    """Allow insecure transport for testing."""
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    yield
    del os.environ['OAUTHLIB_INSECURE_TRANSPORT']

@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()

@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("X_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("X_CLIENT_SECRET", "test_client_secret")
    return {
        "X_CLIENT_ID": "test_client_id",
        "X_CLIENT_SECRET": "test_client_secret"
    }

@pytest.fixture
def mock_bookmarks():
    """Create mock bookmarks response."""
    mock_bookmark = MagicMock()
    mock_bookmark._json = {
        "id": "123",
        "text": "Test tweet",
        "author": {"username": "test_user"},
        "created_at": "2024-01-01T00:00:00.000Z"
    }
    mock_bookmark.id = "123"
    mock_bookmark.text = "Test tweet"
    mock_bookmark.author = MagicMock()
    mock_bookmark.author.username = "test_user"
    mock_bookmark.created_at = "2024-01-01T00:00:00.000Z"

    mock_response = MagicMock(spec=tweepy.Response)
    mock_response.data = [mock_bookmark]
    mock_response.meta = {}

    # Ensure data is set correctly
    assert mock_response.data is not None
    assert len(mock_response.data) == 1
    assert mock_response.data[0] == mock_bookmark
    assert mock_response.data[0]._json == mock_bookmark._json

    return mock_response, mock_bookmark

@pytest.fixture
def mock_async_run():
    """Mock asyncio.run to handle coroutines."""
    async def mock_run(coro):
        return await coro
    return mock_run

def test_download_missing_credentials(runner, monkeypatch):
    """Test download command without credentials."""
    monkeypatch.delenv("X_CLIENT_ID", raising=False)
    monkeypatch.delenv("X_CLIENT_SECRET", raising=False)
    result = runner.invoke(download)
    assert result.exit_code == 1
    assert "Error: X_CLIENT_ID and X_CLIENT_SECRET environment variables must be set" in result.output

_mock_converter = MagicMock()
mock_save_bookmark = MagicMock()
_mock_converter.save_bookmark = mock_save_bookmark

class MockMarkdownConverter:
    def __init__(self, output_dir, template=None):
        print(f"\nMarkdownConverter called with output_dir: {output_dir}, template: {template}")
        self.output_dir = output_dir
        self.template = template
        self._mock_save_bookmark = MagicMock()

    def save_bookmark(self, tweet_data, media_handler):
        print(f"Calling save_bookmark with tweet_data: {tweet_data}, media_handler: {media_handler}")
        return self._mock_save_bookmark(tweet_data, media_handler)

    @property
    def mock_save_bookmark(self):
        return self._mock_save_bookmark

def test_download_basic(runner, mock_env, clean_test_dir, mock_bookmarks):
    """Test basic download command."""
    mock_response, mock_bookmark = mock_bookmarks
    print(f"\nMock response data: {mock_response.data}")
    print(f"Mock bookmark: {mock_bookmark}")
    print(f"Mock bookmark _json: {mock_bookmark._json}")

    async def mock_get_bookmarks(*args, **kwargs):
        print(f"\nInside mock_get_bookmarks")
        print(f"Mock response data: {mock_response.data}")
        print(f"Mock bookmark: {mock_bookmark}")
        print(f"Mock bookmark _json: {mock_bookmark._json}")
        assert mock_response.data is not None
        assert len(mock_response.data) == 1
        assert mock_response.data[0] == mock_bookmark
        assert mock_response.data[0]._json == mock_bookmark._json
        return [mock_response]

    mock_client = AsyncMock()
    mock_client.get_bookmarks = mock_get_bookmarks

    mock_auth = MagicMock()
    mock_auth.get_client_from_env.return_value = mock_client

    mock_markdown_converter = MockMarkdownConverter(str(clean_test_dir))

    with patch("xbm.auth.oauth.XAuth.from_env", return_value=mock_auth), \
         patch("xbm.storage.manager.StorageManager.load_state", return_value={}), \
         patch("xbm.storage.manager.StorageManager.save_state") as mock_save_state, \
         patch("xbm.cli.MarkdownConverter", return_value=mock_markdown_converter), \
         patch("asyncio.run", new=lambda x: asyncio.get_event_loop().run_until_complete(x)), \
         patch.dict(os.environ, mock_env, clear=True):
        with runner.isolated_filesystem():
            result = runner.invoke(download, ["--output-dir", str(clean_test_dir), "--no-media"], catch_exceptions=False)
            print(f"\nResult output: {result.output}")
            print(f"Mock save_bookmark call count: {mock_markdown_converter.mock_save_bookmark.call_count}")
            assert mock_markdown_converter.mock_save_bookmark.call_count == 1
            assert result.exit_code == 0

def test_download_with_media(runner, mock_env, clean_test_dir, mock_bookmarks):
    """Test download command with media."""
    mock_response, mock_bookmark = mock_bookmarks
    mock_bookmark._json = {
        "id": "123",
        "text": "Test tweet",
        "author": {"username": "test_user"},
        "created_at": "2024-01-01T00:00:00.000Z",
        "media": [{"type": "photo", "url": "test.jpg"}]
    }
    mock_response.data = [mock_bookmark]

    async def mock_get_bookmarks(*args, **kwargs):
        return [mock_response]

    mock_client = AsyncMock()
    mock_client.get_bookmarks = mock_get_bookmarks

    mock_auth = MagicMock()
    mock_auth.get_client_from_env.return_value = mock_client

    mock_media_handler = MagicMock()
    mock_media_handler.download_media = AsyncMock(return_value=[Path("test.jpg")])

    mock_markdown_converter = MockMarkdownConverter(str(clean_test_dir))

    with patch("xbm.auth.oauth.XAuth.from_env", return_value=mock_auth), \
         patch("xbm.storage.manager.StorageManager.load_state", return_value={}), \
         patch("xbm.storage.manager.StorageManager.save_state") as mock_save_state, \
         patch("xbm.cli.MarkdownConverter", return_value=mock_markdown_converter), \
         patch("xbm.converter.media.MediaHandler", return_value=mock_media_handler), \
         patch("asyncio.run", new=lambda x: asyncio.get_event_loop().run_until_complete(x)), \
         patch.dict(os.environ, mock_env, clear=True):
        with runner.isolated_filesystem():
            result = runner.invoke(download, [
                "--output-dir", str(clean_test_dir),
                "--download-media"
            ], catch_exceptions=False)
            print(f"\nResult output: {result.output}")
            print(f"Mock save_bookmark call count: {mock_markdown_converter.mock_save_bookmark.call_count}")
            assert mock_markdown_converter.mock_save_bookmark.call_count == 1
            assert result.exit_code == 0

def test_download_skip_errors(runner, mock_env, clean_test_dir, mock_bookmarks):
    """Test download command with error skipping."""
    mock_response, mock_bookmark = mock_bookmarks
    mock_response.data = [mock_bookmark]

    async def mock_get_bookmarks(*args, **kwargs):
        return [mock_response]

    mock_client = AsyncMock()
    mock_client.get_bookmarks = mock_get_bookmarks

    mock_auth = MagicMock()
    mock_auth.get_client_from_env.return_value = mock_client

    mock_markdown_converter = MockMarkdownConverter(str(clean_test_dir))
    mock_markdown_converter.mock_save_bookmark.side_effect = Exception("Test error")

    with patch("xbm.auth.oauth.XAuth.from_env", return_value=mock_auth), \
         patch("xbm.storage.manager.StorageManager.load_state", return_value={}), \
         patch("xbm.storage.manager.StorageManager.save_state") as mock_save_state, \
         patch("xbm.cli.MarkdownConverter", return_value=mock_markdown_converter), \
         patch("asyncio.run", new=lambda x: asyncio.get_event_loop().run_until_complete(x)), \
         patch.dict(os.environ, mock_env, clear=True):
        with runner.isolated_filesystem():
            result = runner.invoke(download, [
                "--output-dir", str(clean_test_dir),
                "--skip-errors",
                "--no-media"
            ], catch_exceptions=False)
            print(f"\nResult output: {result.output}")
            print(f"Mock save_bookmark call count: {mock_markdown_converter.mock_save_bookmark.call_count}")
            assert mock_markdown_converter.mock_save_bookmark.call_count == 1
            assert result.exit_code == 0

def test_auth_command(runner, mock_env):
    """Test auth command."""
    expected_url = "https://twitter.com/i/oauth2/authorize"
    mock_handler = MagicMock()
    mock_handler.get_authorization_url.return_value = expected_url + "?response_type=code&client_id=test_client_id&state=test_state"
    mock_handler._client = MagicMock()
    mock_handler._client.state = "test_state"
    mock_handler.fetch_token.return_value = {"access_token": "test_token"}

    mock_auth = MagicMock()
    mock_auth._auth = mock_handler
    mock_auth.get_auth_url.return_value = mock_handler.get_authorization_url.return_value
    mock_auth.fetch_token.return_value = mock_handler.fetch_token.return_value

    with patch("xbm.auth.oauth.XAuth.from_env", return_value=mock_auth), \
         patch("keyring.set_password") as mock_save, \
         patch.dict(os.environ, mock_env, clear=True):
        result = runner.invoke(auth, input="http://localhost:8000/?code=test_code&state=test_state\n", catch_exceptions=False)

        assert result.exit_code == 0
        assert "Please visit this URL" in result.output
        assert expected_url in result.output
        assert "Authentication successful" in result.output
        mock_auth.fetch_token.assert_called_once_with("http://localhost:8000/?code=test_code&state=test_state")

def test_auth_command_state_mismatch(runner, mock_env):
    """Test auth command with state mismatch."""
    expected_url = "https://twitter.com/i/oauth2/authorize"
    mock_handler = MagicMock()
    mock_handler.get_authorization_url.return_value = expected_url + "?response_type=code&client_id=test_client_id&state=test_state"
    mock_handler._client = MagicMock()
    mock_handler._client.state = "test_state"
    mock_handler.fetch_token.side_effect = ValueError("State verification failed")

    mock_auth = MagicMock()
    mock_auth._auth = mock_handler
    mock_auth.get_auth_url.return_value = mock_handler.get_authorization_url.return_value
    mock_auth.fetch_token.side_effect = ValueError("State verification failed")

    with patch("xbm.auth.oauth.XAuth.from_env", return_value=mock_auth), \
         patch("keyring.set_password") as mock_save, \
         patch.dict(os.environ, mock_env, clear=True):
        result = runner.invoke(auth, input="http://localhost:8000/?code=test_code&state=wrong_state\n", catch_exceptions=False)

        assert result.exit_code == 1
        assert "Please visit this URL" in result.output
        assert expected_url in result.output
        assert "Error: State verification failed" in result.output
        mock_auth.fetch_token.assert_called_once_with("http://localhost:8000/?code=test_code&state=wrong_state")
