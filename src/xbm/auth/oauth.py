"""OAuth 2.0 authentication for X API using PKCE flow.

This module implements OAuth 2.0 Authorization Code Flow with PKCE for X API authentication.
It handles the complete OAuth flow including:
- Authorization URL generation with PKCE
- Local callback server for authorization code
- Token management (storage, refresh)
- Client initialization with proper OAuth 2.0 credentials
"""
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import parse_qs, urlparse
import json
import sys
import os
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
from threading import Thread
import time

import tweepy
from tweepy import OAuth2UserHandler
from tweepy.errors import TweepyException

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handler for OAuth 2.0 callback.

    This handler receives the authorization code from X's OAuth service
    after the user authorizes the application. It stores the callback URL
    which contains the authorization code needed to obtain the access token.
    """
    callback_url = None

    def do_GET(self):
        """Handle GET request from OAuth callback.

        Stores the full callback URL and returns a success message to the user.
        The callback URL contains the authorization code needed for the OAuth flow.
        """
        OAuthCallbackHandler.callback_url = f"http://localhost:8000{self.path}"
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Authorization successful! You can close this window.")

    def log_message(self, format, *args):
        """Suppress logging."""
        pass

class XAuth:
    """X OAuth 2.0 authentication handler using PKCE flow.

    This class manages the OAuth 2.0 Authorization Code Flow with PKCE for X API.
    It handles:
    - OAuth 2.0 authorization with PKCE
    - Token management (storage, refresh)
    - Client initialization
    - Secure storage of credentials

    The PKCE flow is required for X API v2 endpoints that need user context,
    such as bookmarks. This implementation includes automatic token refresh
    when the access token expires.
    """

    @classmethod
    def from_env(cls) -> 'XAuth':
        """Create XAuth instance from environment variables.

        Returns:
            XAuth: XAuth instance

        Raises:
            ValueError: If environment variables are not set
        """
        client_id = os.environ.get("X_CLIENT_ID")
        client_secret = os.environ.get("X_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError("X_CLIENT_ID and X_CLIENT_SECRET environment variables must be set")

        return cls(client_id, client_secret)

    def __init__(self, client_id: str, client_secret: str):
        """Initialize XAuth.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = "http://localhost:8000"  # Match Twitter Developer Portal setting

        # Allow insecure transport for local development
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

        # Ensure .xbm directory exists
        self.auth_dir = Path(".xbm")
        self.auth_dir.mkdir(exist_ok=True)

        # Initialize OAuth2 handler with Twitter's required scopes
        self._auth = OAuth2UserHandler(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=self.redirect_uri,
            scope=["offline.access", "bookmark.read", "tweet.read", "users.read"]
        )

    def _start_callback_server(self) -> HTTPServer:
        """Start local server to handle OAuth callback.

        Returns:
            HTTPServer: The callback server
        """
        server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        return server

    def get_auth_url(self) -> str:
        """Get the authorization URL for Twitter OAuth."""
        auth_url = self._auth.get_authorization_url()
        # State is stored internally by OAuth2UserHandler
        return auth_url

    def authenticate(self) -> dict:
        """Complete OAuth 2.0 PKCE authentication flow.

        This method handles the complete OAuth 2.0 flow:
        1. Starts local callback server
        2. Generates and opens authorization URL
        3. Waits for user authorization
        4. Exchanges authorization code for tokens
        5. Stores tokens securely

        Returns:
            dict: OAuth token data including access and refresh tokens

        Raises:
            ValueError: If authorization fails
            TweepyException: For Tweepy-specific errors
            RuntimeError: For system-level errors
        """
        # Start callback server
        try:
            server = self._start_callback_server()
        except (socket.error, OSError) as e:
            raise RuntimeError(f"Failed to start callback server: {str(e)}")

        try:
            # Get and open authorization URL
            try:
                auth_url = self.get_auth_url()
            except TweepyException as e:
                raise TweepyException(f"Failed to get authorization URL: {str(e)}")

            print("\nPlease verify these settings in your Twitter Developer Portal:")
            print("1. OAuth 2.0 is enabled")
            print("2. Type of App is set to 'Native App'")
            print(f"3. Callback URL '{self.redirect_uri}' is added to allowed callback URLs")
            print("4. App has read permissions enabled\n")

            print("Opening browser for authorization...")
            print(f"If the browser doesn't open automatically, visit:\n{auth_url}\n")
            try:
                webbrowser.open(auth_url)
            except webbrowser.Error as e:
                print(f"Failed to open browser automatically: {str(e)}")
                print("Please visit the URL manually.")

            # Wait for callback
            print("Waiting for authorization...")
            start_time = time.time()
            while not OAuthCallbackHandler.callback_url:
                time.sleep(0.1)
                if time.time() - start_time > 300:  # 5 minute timeout
                    raise ValueError("Authorization timed out. Please try again and make sure to authorize the app.")

            # Get token using callback URL
            callback_url = OAuthCallbackHandler.callback_url
            if not callback_url:
                raise ValueError("No callback URL received")

            if "error=" in callback_url:
                error_params = parse_qs(urlparse(callback_url).query)
                error = error_params.get("error", ["Unknown error"])[0]
                error_description = error_params.get("error_description", ["No description available"])[0]
                raise ValueError(f"Authorization failed: {error} - {error_description}")

            print("DEBUG: Received callback URL:", callback_url[:50] + "..." if callback_url else None)

            try:
                token = self._auth.fetch_token(callback_url)
            except TweepyException as e:
                raise TweepyException(f"Failed to fetch token: {str(e)}")
            except Exception as e:
                raise RuntimeError(f"Unexpected error fetching token: {str(e)}")

            print("DEBUG: Fetched token structure:", json.dumps({k: bool(v) for k, v in token.items()}))

            try:
                self._save_token(token)
            except (IOError, OSError) as e:
                raise RuntimeError(f"Failed to save token: {str(e)}")

            print("DEBUG: Token saved successfully")
            return token

        except Exception as e:
            # Re-raise known exceptions
            if isinstance(e, (ValueError, TweepyException, RuntimeError)):
                raise
            # Wrap unknown exceptions
            raise RuntimeError(f"Authentication failed: {str(e)}")

        finally:
            # Clean up
            try:
                server.shutdown()
                server.server_close()
            except Exception as e:
                print(f"Warning: Failed to clean up server: {str(e)}")

    def _refresh_token(self, token: dict) -> dict:
        """Refresh OAuth 2.0 access token using refresh token.

        When the access token expires, this method obtains a new one using
        the refresh token. This allows continuous access without requiring
        user re-authorization.

        Args:
            token: Current token data containing refresh_token

        Returns:
            dict: New token data with fresh access_token

        Raises:
            ValueError: If refresh token is missing or refresh fails
        """
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            raise ValueError("No refresh token available")

        print("DEBUG: Refreshing OAuth 2.0 token...")
        print("DEBUG: Current token structure:", json.dumps({k: bool(v) for k, v in token.items()}))
        try:
            # Create a new OAuth2UserHandler for refresh
            auth = OAuth2UserHandler(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=["offline.access", "bookmark.read", "tweet.read", "users.read"]
            )
            # Refresh the token
            print("DEBUG: Attempting token refresh with params:", {
                "url": "https://api.twitter.com/2/oauth2/token",
                "refresh_token": refresh_token[:10] + "..." if refresh_token else None,
                "client_id_present": bool(self.client_id),
                "client_secret_present": bool(self.client_secret)
            })
            new_token = auth.refresh_token(
                "https://api.twitter.com/2/oauth2/token",
                refresh_token=refresh_token,
                body=f"grant_type=refresh_token&client_id={self.client_id}&client_secret={self.client_secret}"
            )
            print("DEBUG: Token refreshed successfully")
            print("DEBUG: New token structure:", json.dumps({k: bool(v) for k, v in new_token.items()}))
            self._save_token(new_token)
            return new_token
        except Exception as e:
            print("DEBUG: Token refresh failed with error:", str(e))
            raise ValueError(f"Failed to refresh token: {str(e)}")

    def get_client(self) -> Any:
        """Get authenticated client for X API.

        This method initializes a Tweepy client with OAuth 2.0 PKCE credentials.
        It handles:
        - Loading stored tokens
        - Automatic token refresh if expired
        - Proper OAuth 2.0 client initialization

        Returns:
            Any: Authenticated Tweepy client

        Raises:
            ValueError: If no token found or token is invalid
            TweepyException: For Tweepy-specific errors
            RuntimeError: For system-level errors
        """
        try:
            token = self._load_token()
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to load token: {str(e)}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid token data: {str(e)}")

        if not token:
            raise ValueError("No token found. Please authenticate first.")

        print("DEBUG: Loaded token structure:", json.dumps({k: bool(v) for k, v in token.items()}))

        # Check if token is expired
        expires_at = token.get("expires_at", 0)
        if expires_at and time.time() >= expires_at:
            print("DEBUG: Token expired, refreshing...")
            try:
                token = self._refresh_token(token)
            except TweepyException as e:
                raise TweepyException(f"Failed to refresh token: {str(e)}")

        # Initialize client with OAuth 2.0 User Context
        try:
            # Create client with OAuth 2.0 PKCE using bearer token
            client = tweepy.Client(
                bearer_token=token.get("access_token"),  # Use access_token as bearer_token
                consumer_key=self.client_id,
                consumer_secret=self.client_secret,
                wait_on_rate_limit=True
            )

            # Verify the client is properly authenticated
            try:
                print("DEBUG: Attempting to verify client with get_bookmarks()...")
                # Try to make an authenticated request
                response = client.get_bookmarks()
                if not response:
                    raise ValueError("Failed to verify authentication: no response")
                print("DEBUG: Client verification successful:", response)
            except TweepyException as e:
                print("DEBUG: Initial verification failed:", str(e))
                # If verification fails, try refreshing the token
                print("DEBUG: Verification failed, refreshing token...")
                token = self._refresh_token(token)
                print("DEBUG: Creating new client with refreshed token...")
                # Create new client with refreshed token
                client = tweepy.Client(
                    bearer_token=token.get("access_token"),  # Use access_token as bearer_token
                    consumer_key=self.client_id,
                    consumer_secret=self.client_secret,
                    wait_on_rate_limit=True
                )
                # Try verification again
                print("DEBUG: Attempting verification with refreshed token...")
                response = client.get_bookmarks()
                if not response:
                    raise ValueError("Failed to verify authentication after token refresh")
                print("DEBUG: Client verification successful with refreshed token:", response)

            print("DEBUG: Client initialized and verified with OAuth 2.0 User Context")
            return client
        except TweepyException as e:
            print("DEBUG: Client initialization failed with TweepyException:", str(e))
            # If we get a 401 or 403, we need to re-authenticate
            if "401" in str(e) or "403" in str(e):
                print("DEBUG: Token is invalid or expired. Please re-authenticate using 'xbm auth'")
                # Delete the invalid token
                try:
                    (self.auth_dir / "token.json").unlink(missing_ok=True)
                except Exception as e:
                    print(f"Warning: Failed to delete invalid token: {str(e)}")
            raise TweepyException(f"Failed to initialize client: {str(e)}")
        except Exception as e:
            print("DEBUG: Client initialization failed with unexpected error:", str(e))
            raise RuntimeError(f"Unexpected error initializing client: {str(e)}")

    def get_client_from_env(self) -> Any:
        """Get authenticated client from environment.

        Returns:
            Any: Authenticated client

        Raises:
            ValueError: If token is not found
        """
        return self.get_client()

    def _save_state(self, state: str) -> None:
        """Save OAuth state securely.

        Args:
            state: OAuth state to save
        """
        state_file = self.auth_dir / "oauth_state"
        state_file.write_text(state)

    def _load_state(self) -> Optional[str]:
        """Load OAuth state.

        Returns:
            Optional[str]: Stored state or None if not found
        """
        state_file = self.auth_dir / "oauth_state"
        if not state_file.exists():
            return None
        return state_file.read_text().strip()

    def _save_token(self, token: dict) -> None:
        """Save token securely.

        Args:
            token: Token data to save
        """
        try:
            token_file = self.auth_dir / "token.json"
            token_file.write_text(json.dumps(token))
        except Exception as e:
            raise ValueError(f"Failed to save token: {str(e)}") from e

    def _load_token(self) -> Optional[Dict[str, Any]]:
        """Load token from storage.

        Returns:
            Optional[Dict[str, Any]]: Token data or None if not found

        Raises:
            ValueError: If token data is invalid
        """
        try:
            token_file = self.auth_dir / "token.json"
            if not token_file.exists():
                return None
            return json.loads(token_file.read_text())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid token data: {str(e)}") from e
        except Exception as e:
            raise ValueError(f"Failed to load token: {str(e)}") from e
