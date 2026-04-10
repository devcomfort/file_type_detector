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


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_pdf(fixtures_dir):
    """Return path to sample PDF file."""
    return fixtures_dir / "sample.pdf"


@pytest.fixture
def sample_json(fixtures_dir):
    """Return path to sample JSON file."""
    return fixtures_dir / "sample.json"


@pytest.fixture
def sample_txt(fixtures_dir):
    """Return path to sample text file."""
    return fixtures_dir / "sample.txt"


@pytest.fixture
def sample_md(fixtures_dir):
    """Return path to sample Markdown file."""
    return fixtures_dir / "sample.md"


@pytest.fixture
def sample_py(fixtures_dir):
    """Return path to sample Python file."""
    return fixtures_dir / "sample.py"


@pytest.fixture
def sample_xml(fixtures_dir):
    """Return path to sample XML file."""
    return fixtures_dir / "sample.xml"


@pytest.fixture
def sample_csv(fixtures_dir):
    """Return path to sample CSV file."""
    return fixtures_dir / "sample.csv"


@pytest.fixture
def sample_pptx(fixtures_dir):
    """Return path to sample PowerPoint 2007+ file."""
    return fixtures_dir / "sample.pptx"


@pytest.fixture
def sample_ppt(fixtures_dir):
    """Return path to sample PowerPoint 97-2003 file."""
    return fixtures_dir / "sample.ppt"


@pytest.fixture
def sample_docx(fixtures_dir):
    """Return path to sample Word 2007+ file."""
    return fixtures_dir / "sample.docx"


@pytest.fixture
def sample_doc(fixtures_dir):
    """Return path to sample Word 97-2003 file."""
    return fixtures_dir / "sample.doc"


@pytest.fixture
def sample_xlsx(fixtures_dir):
    """Return path to sample Excel 2007+ file."""
    return fixtures_dir / "sample.xlsx"


@pytest.fixture
def sample_xls(fixtures_dir):
    """Return path to sample Excel 97-2003 file."""
    return fixtures_dir / "sample.xls"


@pytest.fixture
def sample_hwp(fixtures_dir):
    """Return path to sample HWP (Hangul Word Processor) file."""
    return fixtures_dir / "sample.hwp"


@pytest.fixture
def sample_hwpx(fixtures_dir):
    """Return path to sample HWPX (Hangul Word Processor XML) file."""
    return fixtures_dir / "sample.hwpx"


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
