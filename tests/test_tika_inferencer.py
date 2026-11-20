"""Unit tests for TikaInferencer JAR resolution and error handling.

These tests never spawn Java; they exercise path selection, SHA-512
verification, and missing-JAR error paths so Java-free environments still
cover the module.
"""

import os
import shutil
from pathlib import Path

import pytest

from filetype_detector.strategies import tika_inferencer
from filetype_detector.strategies.tika_inferencer import (
    TIKA_SHA512,
    TikaInferencer,
)


class TestManifestSync:
    """The packaged manifest must stay identical to the repo-root manifest."""

    def test_packaged_manifest_matches_root(self) -> None:
        strategies_dir = Path(tika_inferencer.__file__).resolve().parent
        repo_root = strategies_dir.parents[2]
        root_manifest = repo_root / "tika-manifest.json"
        if not root_manifest.is_file():
            pytest.skip("repo-root manifest absent (installed package)")
        packaged = strategies_dir / "tika_manifest.json"
        assert packaged.read_bytes() == root_manifest.read_bytes()


class TestJarResolution:
    """JAR discovery order: explicit arg > TIKA_JAR env > default cache path."""

    def test_explicit_jar_path_wins(self, tmp_path: Path, monkeypatch) -> None:
        jar = tmp_path / "custom.jar"
        jar.write_bytes(b"jar")
        monkeypatch.setenv("TIKA_JAR", str(tmp_path / "env.jar"))
        assert TikaInferencer(jar)._jar == jar

    def test_env_jar_used_when_no_arg(self, tmp_path: Path, monkeypatch) -> None:
        jar = tmp_path / "env.jar"
        monkeypatch.setenv("TIKA_JAR", str(jar))
        assert TikaInferencer()._jar == jar

    def test_default_path_used_without_env(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.delenv("TIKA_JAR", raising=False)
        inferencer = TikaInferencer()
        assert inferencer._jar == TikaInferencer.default_jar_path()


class TestJarVerification:
    """Missing or corrupted JARs must fail before Java is launched."""

    def test_missing_jar_raises_file_not_found(self, tmp_path: Path) -> None:
        probe = tmp_path / "probe.bin"
        probe.write_bytes(b"data")
        inferencer = TikaInferencer(tmp_path / "absent.jar")
        with pytest.raises(FileNotFoundError, match="Tika JAR not found"):
            inferencer.detect(probe)

    def test_sha_mismatch_raises_value_error(self, tmp_path: Path) -> None:
        jar = tmp_path / "bad.jar"
        jar.write_bytes(b"not-the-pinned-tika")
        inferencer = TikaInferencer(jar)
        probe = tmp_path / "probe.bin"
        probe.write_bytes(b"data")
        with pytest.raises(ValueError, match="SHA-512 mismatch"):
            inferencer.detect(probe)


class TestLifecycle:
    """Process management guarantees."""

    def test_close_is_idempotent_without_process(self) -> None:
        inferencer = TikaInferencer()
        inferencer.close()
        inferencer.close()

    def test_missing_java_raises_runtime_error(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        jar = tmp_path / "tika.jar"
        jar.write_bytes(b"jar")
        monkeypatch.setattr(
            TikaInferencer, "_digest", staticmethod(lambda p: TIKA_SHA512)
        )
        monkeypatch.setattr(
            shutil, "which", lambda name: None if name == "java" else name
        )
        monkeypatch.setenv("PATH", "")
        inferencer = TikaInferencer(jar)
        probe = tmp_path / "probe.bin"
        probe.write_bytes(b"data")
        with pytest.raises(RuntimeError, match="Java not found"):
            inferencer.detect(probe)


@pytest.mark.skipif(
    shutil.which("java") is None,
    reason="java runtime not installed",
)
class TestRealTikaBackend:
    """Optional end-to-end checks; skipped when Java is absent."""

    def test_detect_pdf(self, tmp_path: Path) -> None:
        env_jar = os.environ.get("TIKA_JAR", "")
        jar = Path(env_jar) if env_jar else TikaInferencer.default_jar_path()
        if not jar.exists():
            pytest.skip("pinned Tika JAR not available")
        sample = tmp_path / "sample.pdf"
        sample.write_bytes(b"%PDF-1.4\n%fake minimal pdf\n")
        ft = TikaInferencer(jar).detect(sample)
        assert any("pdf" in mime for mime in ft.mime_types)
        assert ".pdf" in ft.extensions
