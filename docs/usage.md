# XBM Usage Guide

## Installation

1. Install using pip:
   ```bash
   pip install xbm
   ```

2. Or install from source:
   ```bash
   git clone https://github.com/yourusername/xbm.git
   cd xbm
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   ```

## Configuration

1. Create a X Developer App:
   - Go to https://developer.twitter.com/
   - Create a new app or use an existing one
   - Get your Client ID and Client Secret
   - Add `http://localhost:8000` to your callback URLs

2. Set up environment variables:
   ```bash
   export X_CLIENT_ID="your_client_id"
   export X_CLIENT_SECRET="your_client_secret"
   ```

   Or create a `.env` file:
   ```
   X_CLIENT_ID=your_client_id
   X_CLIENT_SECRET=your_client_secret
   ```

## Basic Usage

1. Download bookmarks to markdown:
   ```bash
   xbm download --output-dir bookmarks/
   ```

2. Specify custom options:
   ```bash
   xbm download \
     --output-dir bookmarks/ \
     --media-dir media/ \
     --page-size 50 \
     --format "{date}-{author}-{id}.md"
   ```

## Advanced Usage

### Custom Output Format

You can customize the markdown format using templates:

```bash
xbm download --template custom.md.j2
```

Example template:
```markdown
# Tweet by @{{ author }}

{{ text }}

Posted: {{ created_at | format_date }}

{% if media %}
## Media
{% for item in media %}
- [{{ item.type }}]({{ item.url }})
{% endfor %}
{% endif %}

[Original Tweet]({{ url }})
```

### Incremental Updates

By default, XBM tracks the last downloaded bookmark and only downloads new ones:

```bash
# First run - downloads all bookmarks
xbm download --output-dir bookmarks/

# Later runs - only downloads new bookmarks
xbm download --output-dir bookmarks/
```

Force full download:
```bash
xbm download --output-dir bookmarks/ --force
```

### Media Handling

Control media downloads:

```bash
# Download all media
xbm download --download-media

# Skip media downloads
xbm download --no-media

# Only download specific types
xbm download --media-types photo,animated_gif
```

### Error Handling

Retry failed downloads:
```bash
xbm download --retry-failed
```

Skip problematic bookmarks:
```bash
xbm download --skip-errors
```

## Common Issues

1. Authentication Errors:
   - Check your Client ID and Secret
   - Ensure callback URL is configured
   - Try clearing stored tokens: `xbm auth clear`

2. Rate Limiting:
   - Use smaller page sizes: `--page-size 50`
   - Add delays: `--delay 1`
   - The tool automatically handles rate limits

3. Media Download Issues:
   - Check media directory permissions
   - Use `--skip-failed-media`
   - Try downloading media separately: `xbm download-media`

## Development

1. Set up development environment:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

2. Run tests:
   ```bash
   uv run pytest
   ```

3. Check code style:
   ```bash
   uv run black .
   uv run mypy src/
   ```
