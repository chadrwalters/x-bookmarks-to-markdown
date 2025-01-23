# X Bookmarks to Markdown

A Python command-line utility that downloads X (Twitter) bookmarks and converts them to markdown files.

## Features

- OAuth 2.0 authentication with X API
- Download and convert bookmarks to markdown
- Support for media downloads (images, videos, GIFs)
- Configurable input/output directories
- Progress tracking and resumable downloads

## Requirements

- Python 3.9 or higher
- X (Twitter) Developer Account with API access

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Configuration

1. Create a X Developer App at https://developer.twitter.com/
2. Set up your environment variables:
   ```bash
   export X_CLIENT_ID="your_client_id"
   export X_CLIENT_SECRET="your_client_secret"
   ```

## Usage

Basic usage:
```bash
x-bookmarks-to-markdown --output-dir path/to/output
```

For more options:
```bash
x-bookmarks-to-markdown --help
```

## Development

1. Clone the repository
2. Set up development environment:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```
3. Run tests:
   ```bash
   uv run pytest
   ```

## License

MIT
