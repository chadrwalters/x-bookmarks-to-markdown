"""Markdown converter for X bookmarks."""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import re

class MarkdownConverter:
    """Converts X bookmarks to markdown format."""

    def __init__(
        self,
        output_dir: str | Path,
        template: Optional[str] = None
    ):
        """Initialize markdown converter.

        Args:
            output_dir: Directory to save markdown files
            template: Custom markdown template (default: None)
        """
        self.output_dir = Path(output_dir)
        self.template = template

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert_bookmark(self, bookmark: Dict[str, Any]) -> str:
        """Convert bookmark to markdown.

        Args:
            bookmark: Bookmark data from API

        Returns:
            str: Markdown formatted content
        """
        # Extract data
        text = self._format_text(bookmark["text"])
        author = bookmark["author"]["username"]
        created_at = datetime.fromisoformat(bookmark["created_at"].replace("Z", "+00:00"))
        media = bookmark.get("media", [])

        # Format markdown
        content = [
            f"# Tweet by @{author}",
            "",
            text,
            "",
            f"Posted: {created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        ]

        # Add media section if present
        if media:
            content.extend([
                "",
                "## Media"
            ])
            for item in media:
                media_type = item["type"]
                url = item.get("url") or item.get("preview_image_url")
                if url:
                    content.append(f"- [{media_type}]({url})")

        # Add original tweet link
        content.extend([
            "",
            f"[Original Tweet](https://twitter.com/{author}/status/{bookmark['id']})"
        ])

        return "\n".join(content)

    def save_bookmark(self, bookmark: Dict[str, Any], media_handler: Optional['MediaHandler'] = None) -> Path:
        """Save bookmark to markdown file.

        Args:
            bookmark: Bookmark data
            media_handler: Optional media handler for downloading media

        Returns:
            Path: Path to saved file
        """
        markdown = self.convert_bookmark(bookmark)
        filepath = self._generate_filename(bookmark)

        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(markdown)

        return filepath

    def _format_text(self, text: str) -> str:
        """Format tweet text with markdown syntax.

        Args:
            text: Raw tweet text

        Returns:
            str: Formatted text
        """
        # Convert mentions and hashtags to links
        text = re.sub(
            r'@(\w+)',
            lambda m: f'[@{m.group(1)}](https://twitter.com/{m.group(1)})',
            text
        )
        text = re.sub(
            r'#(\w+)',
            lambda m: f'[#{m.group(1)}](https://twitter.com/hashtag/{m.group(1)})',
            text
        )

        return text

    def _generate_filename(self, bookmark: Dict[str, Any]) -> Path:
        """Generate filename for bookmark.

        Args:
            bookmark: Bookmark data

        Returns:
            Path: Generated filename
        """
        created_at = datetime.fromisoformat(bookmark["created_at"].replace("Z", "+00:00"))
        date_str = created_at.strftime("%Y%m%d-%H%M%S")
        author = bookmark["author"]["username"]
        bookmark_id = bookmark["id"]

        filename = f"{date_str}-{author}-{bookmark_id}.md"
        return self.output_dir / filename
