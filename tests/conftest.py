"""Pytest configuration and fixtures for file type inference tests."""

import tempfile
import pytest
from pathlib import Path
from loguru import logger
import sys


# Configure loguru for tests
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for each test."""
    logger.info("=" * 80)
    yield
    logger.info("=" * 80)


def pytest_runtest_setup(item):
    """Log before each test starts."""
    logger.info(f"🧪 Starting test: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """Log after each test completes."""
    logger.success(f"✅ Completed test: {item.name}")


def pytest_runtest_call(item):
    """Log when test is being called."""
    logger.debug(f"🔍 Running test: {item.name}")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file for testing."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("This is a test file.")
    return file_path


@pytest.fixture
def sample_pdf_file(temp_dir):
    """Create a minimal PDF file for testing."""
    # Minimal valid PDF content
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
    file_path = temp_dir / "test.pdf"
    file_path.write_bytes(pdf_content)
    return file_path


@pytest.fixture
def sample_python_file(temp_dir):
    """Create a sample Python file for testing."""
    file_path = temp_dir / "test.py"
    file_path.write_text('print("Hello, World!")')
    return file_path


@pytest.fixture
def sample_json_file(temp_dir):
    """Create a sample JSON file for testing."""
    file_path = temp_dir / "test.json"
    file_path.write_text('{"key": "value"}')
    return file_path


@pytest.fixture
def sample_empty_file(temp_dir):
    """Create an empty file for testing."""
    file_path = temp_dir / "empty"
    file_path.touch()
    return file_path


@pytest.fixture
def temp_dir_path(temp_dir):
    """Return a directory path (not a file) for testing ValueError."""
    return temp_dir
