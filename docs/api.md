# XBM API Documentation

## Authentication Module

### XAuth

The `XAuth` class handles OAuth2 authentication with the X API.

```python
from xbm.auth.oauth import XAuth

auth = XAuth(
    client_id="your_client_id",
    client_secret="your_client_secret",
    callback_port=8000
)
```

#### Methods

- `get_auth_url() -> str`
  - Get the authorization URL for user authentication
  - Returns: Authorization URL string

- `fetch_token(code: str) -> dict`
  - Fetch access token using authorization code
  - Args:
    - code: Authorization code from callback
  - Returns: Token data including access_token

- `get_client() -> tweepy.Client`
  - Get authenticated Tweepy client
  - Returns: Authenticated client
  - Raises: ValueError if no valid token is found

## API Client Module

### BookmarkClient

The `BookmarkClient` class handles interaction with X's bookmark API.

```python
from xbm.api.client import BookmarkClient

client = BookmarkClient(
    tweepy_client,
    page_size=100,
    max_retries=2
)
```

#### Methods

- `get_bookmarks(pagination_token: Optional[str] = None) -> Generator[Response, None, None]`
  - Get user's bookmarks with pagination
  - Args:
    - pagination_token: Token for pagination
  - Yields: Tweepy response containing bookmarks
  - Raises: tweepy.TweepyException on API failure

## Storage Module

### StorageManager

The `StorageManager` class handles state and file operations.

```python
from xbm.storage.manager import StorageManager

storage = StorageManager(base_dir=".xbm")
```

#### Methods

- `save_state(last_sync_id: str) -> None`
  - Save sync state
  - Args:
    - last_sync_id: ID of last processed bookmark

- `load_state() -> Optional[str]`
  - Load sync state
  - Returns: Last sync ID if found, None otherwise

## Error Handling

All modules use standard Python exceptions with descriptive messages. Common exceptions:

- `ValueError`: Invalid input or state
- `tweepy.TweepyException`: API errors
- `FileNotFoundError`: Missing files
- `json.JSONDecodeError`: Invalid JSON data

## Configuration

Environment variables:
- `X_CLIENT_ID`: X API client ID
- `X_CLIENT_SECRET`: X API client secret

File locations:
- Auth tokens: `.xbm/auth.json`
- State data: `.xbm/state.json`
- Media files: `.xbm/media/`
