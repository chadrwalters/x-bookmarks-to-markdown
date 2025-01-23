# X Bookmarks to Markdown Converter (x-bookmarks-to-markdown)
## Product Requirements Document (PRD) - V1

### Overview
A Python command-line utility that downloads X (Twitter) bookmarks and converts them to markdown files using Tweepy. The tool focuses on simplicity, reliability, and ease of use.

### Target Users
- Individual X users who want to archive their bookmarks
- Researchers and analysts who need to process X content
- Users who prefer markdown-based note-taking systems

### Core Features

#### 1. Authentication & Setup
- OAuth 2.0 authentication flow using Tweepy
  - Primary: Local server callback (ports 8000-8010)
  - Fallback: Manual PIN entry for headless environments
- Token Storage
  - Location: `~/.xbookmarks/auth.json` (or user-chosen config directory)
  - Store tokens securely, using minimal functionality (no advanced token refresh handling)

#### 2. Bookmark Synchronization
- Sync State Management
  - Minimal: only track the last_sync_id in a single JSON file
  - No advanced incremental or partial completion tracking

- Pagination Handling
  - Automatic handling of pagination tokens
  - Progress indication for large bookmark sets
  - Configurable page size (default: 100 bookmarks)

- Failure Recovery
  - Simple retry on API failures
  - Logs and skips problematic bookmarks

#### 3. Media Handling
- Download Strategy
  - Sequential download of media items
  - Simple retry logic (e.g., 2 attempts)
  - Skips previously downloaded media if present

- Supported Media Types
  - Images: jpg, png, gif
  - Videos: mp4
  - Animated GIFs

- Failed Media Handling
  - Logs failed downloads
  - Continues processing remaining items
  - Placeholder links in markdown for failed media

#### 4. Storage & Organization
- Organized directory structure for markdown and media files
- Support for standard paths and user-defined folders (input_dir, output_dir); minimal path handling

### Technical Requirements

#### Configuration
- Required environment variables for authentication tokens
- Optional variables for input/output directory locations
- Basic JSON config file for user preferences

#### Performance Requirements
- Initial Sync: < 30 minutes for up to 3000 bookmarks
- Incremental or repeated Sync: ~5 minutes or less for smaller sets
- Media Downloads: 30-second timeout per item, ~100MB size limit

#### Security Requirements
- Minimal token storage with basic encryption or secure writing
- HTTPS for API calls
- No plaintext credentials in logs

### Limitations & Constraints
- Single user support only
- Fixed markdown format
- No concurrency features
- API-only access (no web scraping)

### Out of Scope for V1
- Multi-user support
- Custom markdown formats
- Comment downloading
- Web interface
- Advanced filtering
- Alternative export formats

### Dependencies
- Python 3.9+
- tweepy
- click for CLI
- keyring (optional or minimal usage)
- Modern web browser for authentication

### Testing & Documentation
- Basic unit tests for core logic
- Integration testing for bookmark retrieval and markdown conversion
- Simple README with setup steps and usage examples
