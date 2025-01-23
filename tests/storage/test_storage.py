"""Tests for storage manager module."""
import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from xbm.storage.manager import StorageManager

@pytest.fixture
def storage():
    """Create StorageManager instance for testing."""
    return StorageManager(base_dir=".xbm")

def test_save_state(storage, tmp_path):
    """Test saving sync state."""
    storage.base_dir = tmp_path
    storage.state_file = tmp_path / "state.json"

    storage.save_state("test_id")

    assert storage.state_file.exists()
    with storage.state_file.open() as f:
        state = json.load(f)
        assert state == {"last_sync_id": "test_id"}

def test_load_state_not_exists(storage):
    """Test loading state when file doesn't exist."""
    with patch.object(Path, "exists", return_value=False):
        assert storage.load_state() is None

def test_load_state_exists(storage):
    """Test loading existing state."""
    mock_state = {"last_sync_id": "test_id"}
    mock_file = mock_open(read_data=json.dumps(mock_state))

    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.open", mock_file):
            last_id = storage.load_state()
            assert last_id == "test_id"

def test_write_json_atomic(storage, tmp_path):
    """Test atomic JSON writing."""
    test_file = tmp_path / "test.json"
    test_data = {"key": "value"}

    storage._write_json(test_file, test_data)

    assert test_file.exists()
    with test_file.open() as f:
        data = json.load(f)
        assert data == test_data

def test_read_json_invalid(storage):
    """Test reading invalid JSON."""
    mock_file = mock_open(read_data="invalid json")

    with patch("pathlib.Path.open", mock_file):
        with pytest.raises(json.JSONDecodeError):
            storage._read_json(Path("test.json"))
