"""Client for interacting with X API."""
from typing import List, Optional, Dict, Any
import tweepy

class Response:
    """Simple response object to match Tweepy's Response format."""
    def __init__(self, data: Any):
        self.data = data

class BookmarkClient:
    """Client for X API bookmark operations."""

    def __init__(self, client: tweepy.Client):
        """Initialize client.

        Args:
            client: Authenticated Tweepy Client instance
        """
        self.client = client

    async def get_bookmarks(self, page_size: int = 100, since_id: Optional[str] = None) -> List[tweepy.Response]:
        """Get bookmarks from X API.

        Args:
            page_size: Number of bookmarks to fetch per page
            since_id: Only return bookmarks after this ID

        Returns:
            List[tweepy.Response]: List of bookmark responses
        """
        responses = []
        try:
            response = self.client.get_bookmarks(
                max_results=page_size,
                expansions=[
                    "author_id",
                    "attachments.media_keys"
                ],
                tweet_fields=[
                    "created_at",
                    "text",
                    "attachments"
                ],
                media_fields=[
                    "type",
                    "url",
                    "preview_image_url"
                ],
                user_fields=[
                    "name",
                    "username"
                ]
            )
            if response:
                responses.append(response)
        except Exception as e:
            raise ValueError(f"Failed to fetch bookmarks: {str(e)}") from e

        return responses
