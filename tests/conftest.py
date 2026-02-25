import pytest
import tempfile
import os
from unittest.mock import Mock, patch

@pytest.fixture
def temp_dir():
    """Temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def mock_stats():
    """Mock BackupRunStatistics."""
    stats = Mock()
    stats.size = 1000
    stats.dumptime = 10.0
    stats.uploadtime = 5.0
    stats.retained_copies = ['file1', 'file2']
    return stats