"""Tests for authentication module."""
import os
from unittest.mock import MagicMock, patch

import pytest
from tweepy import OAuth2UserHandler

from xbm.auth.oauth import XAuth

@pytest.fixture(autouse=True)
def allow_insecure_transport():
    """Allow insecure transport for testing."""
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    yield
    del os.environ['OAUTHLIB_INSECURE_TRANSPORT']

@pytest.fixture
def auth():
    """Create XAuth instance for testing."""
    return XAuth(
        client_id="test_id",
        client_secret="test_secret"
    )

def test_get_auth_url(auth):
    """Test getting authorization URL."""
    mock_handler = MagicMock()
    expected_url = "https://twitter.com/i/oauth2/authorize"
    mock_handler.get_authorization_url.return_value = expected_url + "?response_type=code&client_id=test_id"

    with patch.object(auth, "_auth", mock_handler):
        url = auth.get_auth_url()
        assert expected_url in url
        assert "client_id=test_id" in url

def test_fetch_token_success(auth):
    """Test successful token fetch."""
    mock_handler = MagicMock()
    mock_handler.fetch_token.return_value = {"access_token": "test_token"}
    mock_handler._client = MagicMock()
    mock_handler._client.state = "test_state"

    with patch.object(auth, "_auth", mock_handler), \
         patch("keyring.set_password") as mock_save:
        token = auth.fetch_token("https://example.com/callback?code=test_code&state=test_state")

        mock_handler.fetch_token.assert_called_once_with("test_code")
        mock_save.assert_called_once()
        assert token == {"access_token": "test_token"}

def test_fetch_token_no_code(auth):
    """Test token fetch with missing code."""
    with pytest.raises(ValueError, match="No code found in URL"):
        auth.fetch_token("https://example.com/callback")

def test_fetch_token_state_mismatch(auth):
    """Test token fetch with state mismatch."""
    mock_handler = MagicMock()
    mock_handler._client = MagicMock()
    mock_handler._client.state = "correct_state"

    with patch.object(auth, "_auth", mock_handler):
        with pytest.raises(ValueError, match="State verification failed"):
            auth.fetch_token("https://example.com/callback?code=test_code&state=wrong_state")

def test_fetch_token_pkce_failure(auth):
    """Test token fetch with PKCE verification failure."""
    mock_handler = MagicMock()
    mock_handler._client = MagicMock()
    mock_handler._client.state = "test_state"
    mock_handler.fetch_token.side_effect = Exception("code_verifier missing")

    with patch.object(auth, "_auth", mock_handler):
        with pytest.raises(ValueError, match="PKCE verification failed"):
            auth.fetch_token("https://example.com/callback?code=test_code&state=test_state")

def test_get_client_no_token(auth):
    """Test getting client without token."""
    with patch("keyring.get_password", return_value=None):
        with pytest.raises(ValueError, match="No token found"):
            auth.get_client()

def test_get_client_with_token(auth):
    """Test getting client with token."""
    token_data = {"access_token": "test_token"}

    with patch("keyring.get_password", return_value='{"access_token": "test_token"}'), \
         patch("tweepy.Client") as mock_client:
        client = auth.get_client()
        assert client is not None
        mock_client.assert_called_once_with(
            bearer_token="test_token",
            consumer_key="test_id",
            consumer_secret="test_secret",
            wait_on_rate_limit=True
        )

def test_get_client_invalid_token(auth):
    """Test getting client with invalid token data."""
    with patch("keyring.get_password", return_value="invalid_json"):
        with pytest.raises(ValueError, match="No token found"):
            auth.get_client()
