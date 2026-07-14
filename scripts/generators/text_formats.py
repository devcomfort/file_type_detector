"""Text format generators."""

from .base import BaseGenerator
from . import register


@register
class TextFormatGenerator(BaseGenerator):
    """Generates minimal valid text format files."""

    @property
    def extensions(self) -> list[str]:
        return [
            "txt", "text", "md", "markdown", "rst", "rtf", "tex", "sty",
            "bib", "asc", "eml", "patch", "diff", "vtt", "webvtt", "srt",
            "ics", "m3u", "m3u8", "reg", "plist", "bplist", "lock",
            "pem", "pub", "gpg", "torrent", "vcard", "sum", "url",
            "aux", "dm", "dmigd", "brf", "bfm", "rdf", "sgml", "pgp",
        ]

    @property
    def sources(self) -> dict[str, str]:
        return {ext: "synthetic:Minimal valid format content" for ext in self.extensions}

    @property
    def category(self) -> str:
        return "text"

    def generate(self, ext: str) -> bytes:
        generators = {
            "txt": self._txt,
            "text": self._txt,
            "md": self._md,
            "markdown": self._md,
            "rst": self._rst,
            "rtf": self._rtf,
            "tex": self._tex,
            "sty": self._sty,
            "bib": self._bib,
            "asc": self._asc,
            "eml": self._eml,
            "patch": self._patch,
            "diff": self._diff,
            "vtt": self._vtt,
            "webvtt": self._vtt,
            "srt": self._srt,
            "ics": self._ics,
            "m3u": self._m3u,
            "m3u8": self._m3u,
            "reg": self._reg,
            "plist": self._plist,
            "bplist": self._bplist,
            "lock": self._lock,
            "pem": self._pem,
            "pub": self._pub,
            "gpg": self._gpg,
            "torrent": self._torrent,
            "vcard": self._vcard,
            "sum": self._sum,
            "url": self._url,
            "aux": self._aux,
            "dm": self._dm,
            "dmigd": self._dm,
            "brf": self._brf,
            "bfm": self._brf,
            "rdf": self._rdf,
            "sgml": self._sgml,
            "pgp": self._pgp,
        }
        return generators[ext]().encode("utf-8")

    def _txt(self) -> str:
        return "Hello, World!\n"

    def _md(self) -> str:
        return "# Sample\n\nThis is a sample Markdown file.\n"

    def _rst(self) -> str:
        return "Sample\n======\n\nThis is a sample reStructuredText file.\n"

    def _rtf(self) -> str:
        return r"{\rtf1\ansi\deff0{\fonttbl{\f0 Times New Roman;}}Hello, World!}"

    def _tex(self) -> str:
        return "\\documentclass{article}\n\\begin{document}\nHello, World!\n\\end{document}\n"

    def _sty(self) -> str:
        return "\\ProvidesPackage{sample}[2024/01/01 Sample package]\n"

    def _bib(self) -> str:
        return "@article{sample,\n  author = {John Doe},\n  title = {Sample},\n  year = {2024}\n}\n"

    def _asc(self) -> str:
        return "-----BEGIN PGP SIGNATURE-----\n\niQEcBAEBAgAGBQJl7Z7aAAoJEHbK\n-----END PGP SIGNATURE-----\n"

    def _eml(self) -> str:
        return "From: sender@example.com\nTo: recipient@example.com\nSubject: Hello\n\nHello, World!\n"

    def _patch(self) -> str:
        return "--- a/original.txt\n+++ b/modified.txt\n@@ -1 +1 @@\n-Hello\n+Hello, World!\n"

    def _diff(self) -> str:
        return "--- a/original.txt\n+++ b/modified.txt\n@@ -1 +1 @@\n-Hello\n+Hello, World!\n"

    def _vtt(self) -> str:
        return "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nHello, World!\n"

    def _srt(self) -> str:
        return "1\n00:00:01,000 --> 00:00:04,000\nHello, World!\n\n"

    def _ics(self) -> str:
        return "BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nSUMMARY:Sample\nEND:VEVENT\nEND:VCALENDAR\n"

    def _m3u(self) -> str:
        return "#EXTM3U\n#EXTINF:60,Sample\nsample.mp3\n"

    def _reg(self) -> str:
        return "Windows Registry Editor Version 5.00\n\n[HKEY_CURRENT_USER\\Software\\Sample]\n"

    def _plist(self) -> str:
        return '<?xml version="1.0"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>Name</key><string>Sample</string></dict></plist>'

    def _bplist(self) -> str:
        return "bplist00" + "\x00" * 20

    def _lock(self) -> str:
        return "# This file is automatically @generated.\nversion = 3\n"

    def _pem(self) -> str:
        return "-----BEGIN CERTIFICATE-----\nMIIBkTCB+wIJALRiMLAh0V3MMA0GCSqGSIb3DQEBCwUAMBExDzANBgNVBAMMBnNh\nbXBsZTAeFw0yNDAxMDEwMDAwMDBaFw0yNTAxMDEwMDAwMDBaMBExDzANBgNVBAMM\n-----END CERTIFICATE-----\n"

    def _pub(self) -> str:
        return "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC sample@host\n"

    def _gpg(self) -> str:
        return "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nmQENBF0=\n-----END PGP PUBLIC KEY BLOCK-----\n"

    def _torrent(self) -> str:
        return "d8:announce35:http://tracker.example.com/announce4:infod6:lengthi12e4:name8:hello.txtd12:piece lengthi32768e6:pieces20:abcdefghijklmnopqrst"

    def _vcard(self) -> str:
        return "BEGIN:VCARD\nVERSION:3.0\nFN:Sample User\nEMAIL:sample@example.com\nEND:VCARD\n"

    def _sum(self) -> str:
        return "d41d8cd98f00b204e9800998ecf8427e  sample.txt\n"

    def _url(self) -> str:
        return "[InternetShortcut]\nURL=https://example.com\n"

    def _aux(self) -> str:
        return "\\relax\n\\@writefile{toc}{\\contentsline {section}{\\numberline {1}Sample}{1}}\n"

    def _dm(self) -> str:
        return "/mob/sample\n\tdesc = \"Sample\"\n"

    def _brf(self) -> str:
        return "Hello, World!\nThis is a sample BRF file.\n"

    def _rdf(self) -> str:
        return '<?xml version="1.0"?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about="http://example.org/sample"/></rdf:RDF>'

    def _sgml(self) -> str:
        return "<!DOCTYPE sample PUBLIC \"-//Sample//EN\" \"sample.dtd\"><sample>Hello</sample>"

    def _pgp(self) -> str:
        return "-----BEGIN PGP MESSAGE-----\n\nhqAN BridgE=\n-----END PGP MESSAGE-----\n"
