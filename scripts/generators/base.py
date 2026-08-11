"""Base class for file fixture generators."""

from abc import ABC, abstractmethod
from pathlib import Path

_CASE_VARIANT_EXTENSIONS = frozenset({"CBL", "COB", "CPY", "F90", "P", "R", "S"})


def fixture_filename(ext: str) -> str:
    """Return a fixture name that is unique on case-insensitive filesystems."""
    if ext in _CASE_VARIANT_EXTENSIONS:
        return f"sample.uppercase.{ext}"
    return f"sample.{ext}"


class BaseGenerator(ABC):
    """Abstract base class for fixture file generators.

    Each concrete generator creates minimal valid files for a specific
    file format that Magika and libmagic can detect.
    """

    @property
    @abstractmethod
    def extensions(self) -> list[str]:
        """List of file extensions this generator produces (without dot)."""
        ...

    @property
    def category(self) -> str:
        """Category name for grouping in CLI output."""
        return "unknown"

    @property
    def sources(self) -> dict[str, str]:
        """Map each extension to its source attribution string.

        Returns
        -------
        dict[str, str]
            Mapping from extension (without dot) to a description of
            how the fixture was created.  Values use one of these prefixes:

            - ``synthetic:`` – crafted from format specification magic bytes
            - ``library:`` – generated via a Python library (named inline)
            - ``download:`` – fetched from an external URL (named inline)
        """
        return {}

    @abstractmethod
    def generate(self, ext: str) -> bytes:
        """Generate file content for the given extension.

        Parameters
        ----------
        ext : str
            File extension without dot (e.g., ``'png'``).

        Returns
        -------
        bytes
            Minimal valid file content.
        """
        ...

    def create_fixture(
        self, output_dir: Path, ext: str, force: bool = False
    ) -> Path | None:
        """Create a fixture file in the output directory.

        Parameters
        ----------
        output_dir : Path
            Directory to write the fixture file.
        ext : str
            File extension without dot.
        force : bool
            Overwrite existing files.

        Returns
        -------
        Path | None
            Path to created file, or None if skipped.
        """
        path = output_dir / fixture_filename(ext)
        if path.exists() and not force:
            return None

        content = self.generate(ext)
        path.write_bytes(content)
        return path
