# X Bookmarks to Markdown Converter
## Technical Architecture Document

### System Architecture Overview

This simplified architecture is designed to fulfill the core requirements of authenticating with X (Twitter) and converting bookmarks to Markdown. It focuses on straightforward implementation without advanced state management or storage integrations.

```bash
x-bookmarks-to-markdown/
├── src/
│   ├── __init__.py
│   ├── auth/           # Authentication handling
│   ├── api/            # X API interaction
│   ├── storage/        # File and state management
│   ├── converter/      # Markdown conversion
│   ├── utils/          # Shared utilities (logging, config, error handling)
│   └── cli.py          # Command-line interface
├── tests/
├── pyproject.toml
└── requirements.txt
```

### Core Components

1. Authentication Module (auth/)
   • Handles OAuth 2.0 authentication via Tweepy.
   • Supports a simple local server callback on port 8000 or a manual PIN entry flow (no advanced browser detection).
   • Stores tokens in a minimal JSON file or user-configured path.

2. API Client (api/)
   • Wraps Tweepy client to retrieve bookmarks.
   • Handles pagination with basic page-size configuration (default: 100).
   • Implements minimal retry for API failures.
   • Skips advanced caching or rate limiting (no circuit breakers).

3. Storage Manager (storage/)
   • Persists the last_sync_id in a single JSON file, enabling resumed sync.
   • Saves markdown files to user-specified output_dir.
   • No iCloud or Google Drive specialization—just standard file I/O.
   • Basic file operations (create, read, write) with minimal error handling.

4. Markdown Converter (converter/)
   • Converts bookmark data into markdown format.
   • References media via links without comprehensive downloading logic (optional or minimal downloads).
   • Maintains a lightweight approach to metadata: date, username, link, message, and optional media fields.

5. CLI Interface (cli.py)
   • Exposes a single command that accepts --input-dir and --output-dir as options (defaults can be used).
   • Basic progress and console messaging for how many bookmarks were processed.
   • Simple usage instructions and environment variable support.

### Data Flow

1. User Authentication
   • The user initiates OAuth 2.0 flow, either via a local server (port 8000) or PIN-based approach in headless mode.
   • Auth tokens are stored locally in a JSON file.

2. Bookmark Retrieval
   • The CLI triggers the API client to fetch bookmarks from X using Tweepy.
   • Pagination is handled by a straightforward loop, collecting up to 100 bookmarks at a time.
   • Minimal error handling implements retries; problematic bookmarks are logged then skipped.

3. Storage & State Tracking
   • The last_sync_id is recorded in a JSON file to indicate progress.
   • For each new bookmark, the converter outputs a markdown file (or appends to an existing file) in the user-specified directory.

4. Markdown Conversion
   • Takes raw tweet text, user info, timestamp, and media info.
   • Produces a markdown document with basic sections (title, date, text, media links).
   • Media downloads are optional; references are included as URLs by default.

### Security Considerations

• Minimal token storage in JSON (no advanced encryption or keyring fallback).
• OAuth 2.0 ensures secure authentication with X API.
• HTTPS is used for API calls; no unencrypted channels.
• Log messages avoid printing sensitive tokens.

### Error Handling Strategy

• Simple logging to console or file for recoverable errors.
• Retry a limited number of times for API calls.
• Skipped items are noted; no advanced fallback or circuit breaker logic.

### Configuration Management

• Default environment variables for token/config paths.
• Basic JSON config file handling for user preferences.
• Minimal approach: user either runs with defaults or sets directory paths with CLI options.

### Testing Strategy

• Unit tests for bookmark fetching, markdown conversion, and CLI parameter parsing.
• Mock API responses for consistent testing.
• Simple end-to-end test to confirm bookmarks convert correctly into markdown.

### Performance Considerations

• Efficiently processes up to 3000 bookmarks in under 30 minutes.
• Straightforward pagination with no advanced caching or concurrency.

### Future Extensibility

• Additional export formats (e.g., HTML, PDF).
• More comprehensive error recovery and concurrency.
• Secure token encryption and refresh.
• Integration with iCloud, Google Drive, or other cloud providers.
