"""Media handler for X bookmarks."""
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse
import os

import aiohttp
import asyncio

class MediaHandler:
    """Handles downloading and managing media files."""

    def __init__(
        self,
        media_dir: Path,
        max_retries: int = 2,
        timeout: int = 30,
        allowed_types: Optional[Set[str]] = None
    ):
        """Initialize media handler.

        Args:
            media_dir: Directory to save media files
            max_retries: Maximum number of retry attempts (default: 2)
            timeout: Download timeout in seconds (default: 30)
            allowed_types: Set of allowed media types (default: None = all)
        """
        self.media_dir = Path(media_dir)
        self.max_retries = max_retries
        self.timeout = timeout
        self.allowed_types = allowed_types

        # Create media directory
        self.media_dir.mkdir(parents=True, exist_ok=True)

        # Track failed downloads
        self.failed_downloads: List[Tuple[str, str]] = []

    async def download_media(self, media_items: List[Dict[str, str]]) -> List[Optional[Path]]:
        """Download media items.

        Args:
            media_items: List of media items to download

        Returns:
            List[Optional[Path]]: List of paths to downloaded files

        Raises:
            aiohttp.ClientError: If download fails after retries
        """
        if not media_items:
            return []

        paths = []
        async with aiohttp.ClientSession() as session:
            for item in media_items:
                if not self._should_download(item):
                    continue

                url = item.get("url")
                if not url:
                    raise ValueError("No URL found in media item")

                path = await self._download_item(session, url)
                paths.append(path)

        return paths

    def _should_download(self, item: Dict[str, str]) -> bool:
        """Check if media item should be downloaded.

        Args:
            item: Media item data

        Returns:
            bool: True if should download
        """
        if not self.allowed_types:
            return True

        return item.get("type", "") in self.allowed_types

    async def _download_item(self, session: aiohttp.ClientSession, url: str) -> Optional[Path]:
        """Download a single media item."""
        for attempt in range(self.max_retries + 1):
            try:
                response = await session.get(url, timeout=self.timeout)
                await response.raise_for_status()
                content = await response.read()

                filename = self._generate_filename(url, content)
                filepath = self.media_dir / filename

                filepath.parent.mkdir(parents=True, exist_ok=True)
                filepath.write_bytes(content)

                return filepath
            except aiohttp.ClientError as e:
                if attempt == self.max_retries:
                    raise e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            finally:
                if 'response' in locals():
                    await response.close()
        return None

    def _generate_filename(self, url: str, content: Optional[bytes] = None) -> str:
        """Generate filename for media URL.

        Args:
            url: Media URL
            content: Optional media content for hash generation

        Returns:
            str: Generated filename
        """
        parsed_url = urlparse(url)
        original_filename = os.path.basename(parsed_url.path)
        name, ext = os.path.splitext(original_filename)

        if not ext and content:
            mime_type = mimetypes.guess_type(url)[0]
            if mime_type:
                ext = mimetypes.guess_extension(mime_type) or ""

        if content:
            name = hashlib.sha256(content).hexdigest()[:16]

        return f"{name}{ext}"
