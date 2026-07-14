"""Tests for FileType with host-specific MIME configuration disabled.

``mimetypes.init(files=[])`` excludes host files, while built-in mappings still
follow the running Python version.
"""

import mimetypes

from filetype_detector.core import FileType

# Initialize mimetypes deterministically - no OS-specific files
mimetypes.init(files=[])


class TestNormalizeExtension:
    """Tests for FileType.normalize_extension static method."""

    def test_adds_dot_when_missing(self):
        """normalize_extension('pdf') == '.pdf'"""
        assert FileType.normalize_extension("pdf") == ".pdf"

    def test_preserves_dot_when_present(self):
        """normalize_extension('.pdf') == '.pdf'"""
        assert FileType.normalize_extension(".pdf") == ".pdf"

    def test_handles_empty_string(self):
        """normalize_extension('') == '.'"""
        assert FileType.normalize_extension("") == "."

    def test_handles_double_dot(self):
        """normalize_extension('..pdf') == '..pdf'"""
        assert FileType.normalize_extension("..pdf") == "..pdf"

    def test_handles_uppercase(self):
        """normalize_extension('PDF') == '.PDF'"""
        assert FileType.normalize_extension("PDF") == ".PDF"


class TestFromExtension:
    """Tests for FileType.from_extension class method."""

    def test_known_extension_pdf(self):
        """FileType.from_extension('.pdf').mime_types contains 'application/pdf'"""
        ft = FileType.from_extension(".pdf")
        assert "application/pdf" in ft.mime_types

    def test_known_extension_html(self):
        """FileType.from_extension('.html').mime_types contains 'text/html'"""
        ft = FileType.from_extension(".html")
        assert "text/html" in ft.mime_types

    def test_known_extension_json(self):
        """FileType.from_extension('.json').mime_types contains 'application/json'"""
        ft = FileType.from_extension(".json")
        assert "application/json" in ft.mime_types

    def test_unknown_extension_returns_empty_mime(self):
        """FileType.from_extension('.totallyunknown').mime_types == ()"""
        ft = FileType.from_extension(".totallyunknown")
        assert ft.mime_types == ()

    def test_extension_preserved_in_result(self):
        """FileType.from_extension('.pdf').extensions == ('.pdf',)"""
        ft = FileType.from_extension(".pdf")
        assert ft.extensions == (".pdf",)

    def test_deterministic_mimetypes(self):
        """Verify mimetypes.init(files=[]) ensures deterministic behavior"""
        ft_pdf = FileType.from_extension(".pdf")
        assert ft_pdf.mime_types == ("application/pdf",)

        ft_txt = FileType.from_extension(".txt")
        assert "text/plain" in ft_txt.mime_types

    def test_extension_without_dot(self):
        """FileType.from_extension('pdf') stores extension as-is (no normalization)"""
        ft = FileType.from_extension("pdf")
        assert ft.extensions == ("pdf",)
        assert ft.mime_types == ()


class TestFromMimetype:
    """Tests for FileType.from_mimetype class method."""

    def test_known_mime_pdf(self):
        """FileType.from_mimetype('application/pdf').extensions contains '.pdf'"""
        ft = FileType.from_mimetype("application/pdf")
        assert ".pdf" in ft.extensions

    def test_known_mime_jpeg(self):
        """FileType.from_mimetype('image/jpeg').extensions contains '.jpg'"""
        ft = FileType.from_mimetype("image/jpeg")
        assert ".jpg" in ft.extensions

    def test_unknown_mime_returns_empty_extensions(self):
        """FileType.from_mimetype('application/x-totallyunknown').extensions == ()"""
        ft = FileType.from_mimetype("application/x-totallyunknown")
        assert ft.extensions == ()

    def test_mime_preserved_in_result(self):
        """FileType.from_mimetype('application/pdf').mime_types == ('application/pdf',)"""
        ft = FileType.from_mimetype("application/pdf")
        assert ft.mime_types == ("application/pdf",)

    def test_multiple_extensions(self):
        """FileType.from_mimetype('image/jpeg') has multiple extensions (.jpg, .jpeg, etc.)"""
        ft = FileType.from_mimetype("image/jpeg")
        assert ".jpg" in ft.extensions
        assert ".jpeg" in ft.extensions
        assert len(ft.extensions) >= 2

    def test_text_plain_has_extensions(self):
        """FileType.from_mimetype('text/plain') returns known extensions"""
        ft = FileType.from_mimetype("text/plain")
        assert ".txt" in ft.extensions


class TestDeterministicBehavior:
    """Tests verifying deterministic behavior across mimetypes states."""

    def test_mimetypes_init_empty(self):
        """After mimetypes.init(files=[]), known mappings still work"""
        ft = FileType.from_extension(".pdf")
        assert ft.mime_types == ("application/pdf",)

        ft2 = FileType.from_mimetype("application/pdf")
        assert ".pdf" in ft2.extensions

    def test_uses_python_mime_table_without_os_files(self):
        """Mappings match the running Python standard library."""
        for ext in [".go", ".yaml", ".toml"]:
            mime, _ = mimetypes.guess_type(f"file{ext}", strict=False)
            expected_mime_types = (mime,) if mime else ()

            assert FileType.from_extension(ext).mime_types == expected_mime_types

    def test_mimetypes_reset(self):
        """After resetting mimetypes, results are consistent"""
        mimetypes.init(files=[])

        ft1 = FileType.from_extension(".json")
        ft2 = FileType.from_extension(".json")
        assert ft1.mime_types == ft2.mime_types
        assert ft1.mime_types == ("application/json",)

        ft3 = FileType.from_mimetype("application/json")
        ft4 = FileType.from_mimetype("application/json")
        assert ft3.extensions == ft4.extensions
        assert ".json" in ft3.extensions

    def test_unknown_extension_consistency(self):
        """Unknown extensions consistently return empty mime_types"""
        for ext in [".xyz123", ".unknown", ".fakeext"]:
            ft = FileType.from_extension(ext)
            assert ft.mime_types == ()
            assert ft.extensions == (ext,)

    def test_unknown_mimetype_consistency(self):
        """Unknown MIME types consistently return empty extensions"""
        for mime in [
            "application/x-unknown",
            "x-custom/type",
            "fake/mimetype",
        ]:
            ft = FileType.from_mimetype(mime)
            assert ft.extensions == ()
            assert ft.mime_types == (mime,)
