"""Shared test configuration and fixtures."""
import os
from pathlib import Path
from typing import Generator

import pytest
from _pytest.monkeypatch import MonkeyPatch

@pytest.fixture
def test_dir(tmp_path: Path) -> Path:
    """Create and return a temporary test directory.

    Args:
        tmp_path: Pytest fixture providing temporary directory

    Returns:
        Path: Path to temporary test directory
    """
    return tmp_path

@pytest.fixture
def mock_env(monkeypatch: MonkeyPatch) -> None:
    """Set up mock environment variables for testing.

    Args:
        monkeypatch: Pytest fixture for modifying environment
    """
    monkeypatch.setenv("X_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("X_CLIENT_SECRET", "test_client_secret")

@pytest.fixture
def clean_test_dir(test_dir: Path) -> Generator[Path, None, None]:
    """Create a clean test directory and clean up after test.

    Args:
        test_dir: Temporary test directory

    Yields:
        Path: Path to clean test directory
    """
    # Create test directory
    os.makedirs(test_dir, exist_ok=True)

    yield test_dir

    # Clean up after test
    for item in test_dir.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            for subitem in item.iterdir():
                subitem.unlink()
            item.rmdir()
    test_dir.rmdir()
