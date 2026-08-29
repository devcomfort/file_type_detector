"""Document format generators."""

import zipfile
from io import BytesIO

from ._deterministic import write_zip_str
from .base import BaseGenerator
from . import register


@register
class DocumentGenerator(BaseGenerator):
    """Generates minimal valid document files."""

    @property
    def extensions(self) -> list[str]:
        return [
            "pdf",
            "ps",
            "eps",
            "ai",
            "epub",
            "rtf",
            "tex",
            "sty",
            "odt",
            "ods",
            "odp",
            "dotx",
            "pptm",
            "docm",
            "xlsm",
            "xlsb",
            "vsdm",
            "vsdx",
            "vdw",
            "bdf",
            "dxf",
        ]

    @property
    def sources(self) -> dict[str, str]:
        return {
            "pdf": "synthetic:PDF magic header",
            "ps": "synthetic:PostScript header",
            "eps": "synthetic:EPS header",
            "ai": "synthetic:PDF magic (AI wraps PDF)",
            "epub": "library:zipfile",
            "rtf": "synthetic:RTF header",
            "tex": "synthetic:Minimal LaTeX document",
            "sty": "synthetic:Minimal LaTeX package",
            "odt": "library:zipfile",
            "ods": "library:zipfile",
            "odp": "library:zipfile",
            "dotx": "library:zipfile",
            "pptm": "library:zipfile",
            "docm": "library:zipfile",
            "xlsm": "library:zipfile",
            "xlsb": "library:zipfile",
            "vsdm": "library:zipfile",
            "vsdx": "library:zipfile",
            "vdw": "library:zipfile",
            "bdf": "synthetic:Minimal BDF font",
            "dxf": "library:ezdxf",
        }

    @property
    def category(self) -> str:
        return "document"

    def generate(self, ext: str) -> bytes:
        generators = {
            "pdf": self._create_pdf,
            "ps": self._create_ps,
            "eps": self._create_eps,
            "ai": self._create_ai,
            "epub": self._create_epub,
            "rtf": self._create_rtf,
            "tex": self._create_tex,
            "sty": self._create_sty,
            "odt": self._create_odt,
            "ods": self._create_ods,
            "odp": self._create_odp,
            "dotx": self._create_dotx,
            "pptm": self._create_pptm,
            "docm": self._create_docm,
            "xlsm": self._create_xlsm,
            "xlsb": self._create_xlsb,
            "vsdm": self._create_vsdm,
            "vsdx": self._create_vsdx,
            "vdw": self._create_vdw,
            "bdf": self._create_bdf,
            "dxf": self._create_dxf,
        }
        return generators[ext]()

    def _create_pdf(self) -> bytes:
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"

    def _create_ps(self) -> bytes:
        return b"%!PS-Adobe-3.0\n/Helvetica findfont 12 scalefont setfont\n100 700 moveto (Hello) show\nshowpage\n"

    def _create_eps(self) -> bytes:
        return b"%!PS-Adobe-3.0 EPSF-3.0\n%%BoundingBox: 0 0 100 100\n/Helvetica findfont 12 scalefont setfont\n10 10 moveto (Hello) show\nshowpage\n"

    def _create_ai(self) -> bytes:
        # Deterministic PDF structure with Illustrator markers and valid xref/trailer.
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        content = (
            b"BT /F1 12 Tf 72 720 Td (Illustrator-compatible sample) Tj ET\n"
        )
        objects.append(
            b"<< /Length "
            + str(len(content)).encode("ascii")
            + b" >>\nstream\n"
            + content
            + b"endstream"
        )
        output = bytearray(b"%PDF-1.5\n%Adobe_Illustrator_8.0\n")
        offsets = [0]
        for number, body in enumerate(objects, start=1):
            offsets.append(len(output))
            output.extend(f"{number} 0 obj\n".encode("ascii"))
            output.extend(body)
            output.extend(b"\nendobj\n")
        xref_offset = len(output)
        output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        output.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        output.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%Creator: Adobe Illustrator\n%%EOF\n".encode(
                "ascii"
            )
        )
        return bytes(output)

    def _create_epub(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf, "mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED
            )
            write_zip_str(
                zf,
                "META-INF/container.xml",
                '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
            )
        return buf.getvalue()

    def _create_rtf(self) -> bytes:
        return b"{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Times New Roman;}}Hello, World!}"

    def _create_tex(self) -> bytes:
        return b"\\documentclass{article}\n\\begin{document}\nHello, World!\n\\end{document}\n"

    def _create_sty(self) -> bytes:
        return b"\\ProvidesPackage{sample}[2024/01/01 Sample package]\n\\newcommand{\\hello}{Hello, World!}\n"

    def _create_odt(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "mimetype",
                "application/vnd.oasis.opendocument.text",
                compress_type=zipfile.ZIP_STORED,
            )
            write_zip_str(
                zf,
                "META-INF/manifest.xml",
                '<?xml version="1.0"?><manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"><manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/></manifest:manifest>',
            )
        return buf.getvalue()

    def _create_ods(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "mimetype",
                "application/vnd.oasis.opendocument.spreadsheet",
                compress_type=zipfile.ZIP_STORED,
            )
            write_zip_str(
                zf,
                "META-INF/manifest.xml",
                '<?xml version="1.0"?><manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"><manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/></manifest:manifest>',
            )
        return buf.getvalue()

    def _create_odp(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "mimetype",
                "application/vnd.oasis.opendocument.presentation",
                compress_type=zipfile.ZIP_STORED,
            )
            write_zip_str(
                zf,
                "META-INF/manifest.xml",
                '<?xml version="1.0"?><manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"><manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.presentation"/></manifest:manifest>',
            )
        return buf.getvalue()

    def _create_dotx(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "[Content_Types].xml",
                '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>',
            )
            write_zip_str(
                zf,
                "word/document.xml",
                '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello</w:t></w:r></w:p></w:body></w:document>',
            )
        return buf.getvalue()

    def _create_pptm(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "[Content_Types].xml",
                '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>',
            )
            write_zip_str(
                zf,
                "ppt/presentation.xml",
                '<?xml version="1.0"?><p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldIdLst><p:sldId id="256"/></p:sldIdLst></p:presentation>',
            )
        return buf.getvalue()

    def _create_docm(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "[Content_Types].xml",
                '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>',
            )
            write_zip_str(
                zf,
                "word/document.xml",
                '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello</w:t></w:r></w:p></w:body></w:document>',
            )
        return buf.getvalue()

    def _create_xlsm(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "[Content_Types].xml",
                '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>',
            )
            write_zip_str(
                zf,
                "xl/workbook.xml",
                '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>',
            )
        return buf.getvalue()

    def _create_xlsb(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "[Content_Types].xml",
                '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="bin" ContentType="application/vnd.ms-excel.sheet.binary.macroEnabled.main"/></Types>',
            )
            write_zip_str(zf, "xl/workbook.bin", b"\x00" * 20)
        return buf.getvalue()

    def _create_vsdm(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "[Content_Types].xml",
                '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>',
            )
            write_zip_str(
                zf,
                "visio/document.xml",
                '<?xml version="1.0"?><VisioDocument xmlns="http://schemas.microsoft.com/office/visio/2012/main"><DocumentSettings/></VisioDocument>',
            )
        return buf.getvalue()

    def _create_vsdx(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "[Content_Types].xml",
                '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>',
            )
            write_zip_str(
                zf,
                "visio/document.xml",
                '<?xml version="1.0"?><VisioDocument xmlns="http://schemas.microsoft.com/office/visio/2012/main"><DocumentSettings/></VisioDocument>',
            )
        return buf.getvalue()

    def _create_vdw(self) -> bytes:
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            write_zip_str(
                zf,
                "[Content_Types].xml",
                '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>',
            )
            write_zip_str(
                zf,
                "visio/document.xml",
                '<?xml version="1.0"?><VisioDocument xmlns="http://schemas.microsoft.com/office/visio/2012/main"><DocumentSettings/></VisioDocument>',
            )
        return buf.getvalue()

    def _create_bdf(self) -> bytes:
        return b"STARTFONT 2.1\nFONT sample\nSIZE 12 75 75\nFONTBOUNDINGBOX 8 12 0 -2\nENDFONT\n"

    def _create_dxf(self) -> bytes:
        import ezdxf
        import tempfile
        import os

        doc = ezdxf.new("R2010")
        msp = doc.modelspace()
        msp.add_line((0, 0), (1, 1))
        fd, tmp_path = tempfile.mkstemp(suffix=".dxf")
        os.close(fd)
        try:
            doc.saveas(tmp_path)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            os.unlink(tmp_path)
