"""Pytest configuration and fixtures for file type inference tests.

Provides essential fixtures for path resolution and temporary files.
Canonical fixture truth lives in ``tests/truth/canonical_fixtures.json``
and is consumed by the individual strategy test modules.
"""

import tempfile
import pytest
from pathlib import Path


FIXTURES_DIR = Path(__file__).parent / "fixtures"
TRUTH_DIR = Path(__file__).parent / "truth"


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory.

    Returns
    -------
    Path
        Absolute path to the ``tests/fixtures/`` directory.
    """
    return FIXTURES_DIR


def sample_path(ext):
    """Resolve a sample fixture path by extension.

    Parameters
    ----------
    ext : str
        File extension **without** leading dot (e.g. ``'pdf'``, ``'json'``).

    Returns
    -------
    Path
        Path to ``sample.{ext}`` in the fixtures directory.
    """
    return FIXTURES_DIR / f"sample.{ext}"


def fixture_path(ext: str) -> Path:
    """Resolve a canonical fixture file by extension (without dot).

    Parameters
    ----------
    ext : str
        File extension **without** leading dot (e.g. ``'pdf'``, ``'json'``).

    Returns
    -------
    Path
        Absolute path to ``sample.{ext}`` in the fixtures directory.
    """
    return FIXTURES_DIR / f"sample.{ext}"


def fixture_path_from_name(filename: str) -> Path:
    """Resolve a canonical fixture file by full filename.

    Parameters
    ----------
    filename : str
        Full filename (e.g. ``'sample.pdf'``, ``'sample.py'``).

    Returns
    -------
    Path
        Absolute path to the fixture file in the fixtures directory.
    """
    return FIXTURES_DIR / filename


def load_canonical_fixtures():
    """Load canonical fixture truth from ``tests/truth/canonical_fixtures.json``.

    Returns
    -------
    dict
        Parsed JSON contents of the canonical fixtures truth file.
    """
    import json

    return json.loads((TRUTH_DIR / "canonical_fixtures.json").read_text())


def load_tool_snapshots():
    """Load tool snapshots from ``tests/truth/tool_snapshots.json``.

    Returns
    -------
    dict
        Parsed JSON contents of the tool snapshots file.
    """
    import json

    return json.loads((TRUTH_DIR / "tool_snapshots.json").read_text())


@pytest.fixture
def sample_pdf(fixtures_dir):
    return sample_path("pdf")


@pytest.fixture
def sample_json(fixtures_dir):
    return sample_path("json")


@pytest.fixture
def sample_txt(fixtures_dir):
    return sample_path("txt")


@pytest.fixture
def sample_py(fixtures_dir):
    return sample_path("py")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files.

    Yields
    ------
    Path
        Path to a temporary directory that is cleaned up after the test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a minimal text file for testing.

    Returns
    -------
    Path
        Path to a ``test.txt`` file containing ``"This is a test file."``.
    """
    file_path = temp_dir / "test.txt"
    file_path.write_text("This is a test file.")
    return file_path


@pytest.fixture
def sample_pdf_file(temp_dir):
    """Create a minimal PDF file for testing.

    Returns
    -------
    Path
        Path to a minimal valid PDF file.
    """
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
    file_path = temp_dir / "test.pdf"
    file_path.write_bytes(pdf_content)
    return file_path


@pytest.fixture
def sample_python_file(temp_dir):
    """Create a minimal Python file for testing.

    Returns
    -------
    Path
        Path to a ``test.py`` file containing a simple print statement.
    """
    file_path = temp_dir / "test.py"
    file_path.write_text('print("Hello, World!")')
    return file_path


@pytest.fixture
def sample_json_file(temp_dir):
    """Create a minimal JSON file for testing.

    Returns
    -------
    Path
        Path to a ``test.json`` file containing ``{"key": "value"}``.
    """
    file_path = temp_dir / "test.json"
    file_path.write_text('{"key": "value"}')
    return file_path


@pytest.fixture
def temp_dir_path(temp_dir):
    """Return a directory path (not a file) for testing ValueError.

    Returns
    -------
    Path
        The temporary directory itself.
    """
    return temp_dir


def pytest_addoption(parser):
    """Register custom CLI options for pytest.

    Parameters
    ----------
    parser : pytest.Parser
        The pytest parser instance.
    """
    parser.addoption(
        "--fixture-dir",
        action="store",
        default=None,
        help="Additional directory containing sample.* fixture files.",
    )


@pytest.fixture
def all_sample_files(fixtures_dir, pytestconfig):
    """Collect all sample fixture files from the default and optional custom directory.

    This fixture auto-discovers ``sample.*`` files, enabling tests to run
    against any file placed in the fixtures directory without code changes.

    Parameters
    ----------
    fixtures_dir : Path
        Default fixtures directory.
    pytestconfig : pytest.Config
        Pytest configuration for reading ``--fixture-dir`` option.

    Returns
    -------
    list[Path]
        Sorted list of all discovered sample fixture files.
    """
    files = sorted(fixtures_dir.glob("sample.*"))

    extra_dir = pytestconfig.getoption("--fixture-dir", default=None)
    if extra_dir:
        extra_path = Path(extra_dir)
        if extra_path.is_dir():
            files.extend(sorted(extra_path.glob("sample.*")))

    return files