"""Tests for media handler."""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from xbm.converter.media import MediaHandler

@pytest.fixture
def media_handler(clean_test_dir):
    """Create media handler for testing."""
    return MediaHandler(media_dir=clean_test_dir)

@pytest.mark.asyncio
async def test_download_media_basic(media_handler):
    """Test basic media download."""
    media_items = [
        {"type": "photo", "url": "http://example.com/test.jpg"}
    ]

    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.read = AsyncMock()
    mock_response.read.return_value = b"test content"
    mock_response.close = AsyncMock()

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.__aenter__.return_value = mock_session

    with patch("aiohttp.ClientSession", return_value=mock_session):
        paths = await media_handler.download_media(media_items)
        assert len(paths) == 1
        assert paths[0].exists()
        assert paths[0].read_bytes() == b"test content"

@pytest.mark.asyncio
async def test_download_media_with_filter(clean_test_dir):
    """Test media download with type filter."""
    handler = MediaHandler(
        media_dir=clean_test_dir,
        allowed_types={"photo"}
    )

    media_items = [
        {"type": "photo", "url": "http://example.com/test.jpg"},
        {"type": "video", "url": "http://example.com/test.mp4"}
    ]

    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.read = AsyncMock()
    mock_response.read.return_value = b"test content"
    mock_response.close = AsyncMock()

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.__aenter__.return_value = mock_session

    with patch("aiohttp.ClientSession", return_value=mock_session):
        paths = await handler.download_media(media_items)
        assert len(paths) == 1
        assert paths[0].exists()
        assert paths[0].read_bytes() == b"test content"

@pytest.mark.asyncio
async def test_download_media_retry(media_handler):
    """Test media download with retry."""
    media_items = [
        {"type": "photo", "url": "http://example.com/test.jpg"}
    ]

    mock_error_response = AsyncMock()
    mock_error_response.raise_for_status = AsyncMock(side_effect=aiohttp.ClientError())
    mock_error_response.close = AsyncMock()

    mock_success_response = AsyncMock()
    mock_success_response.raise_for_status = AsyncMock()
    mock_success_response.read = AsyncMock()
    mock_success_response.read.return_value = b"test content"
    mock_success_response.close = AsyncMock()

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(side_effect=[
        mock_error_response,
        mock_success_response
    ])
    mock_session.__aenter__.return_value = mock_session

    with patch("aiohttp.ClientSession", return_value=mock_session):
        paths = await media_handler.download_media(media_items)
        assert len(paths) == 1
        assert paths[0].exists()
        assert paths[0].read_bytes() == b"test content"

@pytest.mark.asyncio
async def test_download_media_failure(media_handler):
    """Test media download failure."""
    media_items = [
        {"type": "photo", "url": "http://example.com/test.jpg"}
    ]

    mock_error_response = AsyncMock()
    mock_error_response.raise_for_status = AsyncMock(side_effect=aiohttp.ClientError())
    mock_error_response.read = AsyncMock()
    mock_error_response.close = AsyncMock()

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(side_effect=[mock_error_response] * (media_handler.max_retries + 1))
    mock_session.__aenter__.return_value = mock_session

    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(aiohttp.ClientError):
            await media_handler.download_media(media_items)
        assert mock_session.get.call_count == media_handler.max_retries + 1

def test_generate_filename(media_handler):
    """Test filename generation."""
    url = "http://example.com/test.jpg"
    filename = media_handler._generate_filename(url)
    assert filename.endswith(".jpg")
    assert len(filename) > 4

def test_should_download(media_handler):
    """Test download filtering."""
    # No filter
    assert media_handler._should_download({"type": "photo"})
    assert media_handler._should_download({"type": "video"})

    # With filter
    handler = MediaHandler(
        media_dir=media_handler.media_dir,
        allowed_types={"photo"}
    )
    assert handler._should_download({"type": "photo"})
    assert not handler._should_download({"type": "video"})
