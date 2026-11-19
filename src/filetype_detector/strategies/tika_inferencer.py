"""Provides Apache Tika-based inferencer implementation.

Unlike libmagic, a pinned Tika build returns identical MIME and extension labels
on Linux, macOS, and Windows. Detection runs in a long-lived JVM process that
this class starts lazily on the first :meth:`detect` call and keeps for reuse,
so the JVM startup cost is paid once.
"""

import base64
import hashlib
import os
import subprocess
import threading
import urllib.request
from pathlib import Path
from typing import Self

from ..core import BaseInferencer, FileType

TIKA_VERSION = "3.3.3"
"""Pinned Apache Tika version; identical labels require an identical JAR."""

TIKA_SHA512 = (
    "3c6e62e864e32af234832ec6d928bbc58692d3ddd60564cd8c80dee7e161653d6efc"
    "ba373b6cc9468c778010bea92bdee5ca75ab24f01923480bec1b29b573fd"
)
"""SHA-512 of the pinned ``tika-app-3.3.3.jar`` from Maven Central."""

TIKA_URL = (
    "https://repo.maven.apache.org/maven2/org/apache/tika/tika-app/"
    f"{TIKA_VERSION}/tika-app-{TIKA_VERSION}.jar"
)
"""Maven Central URL for the pinned JAR."""

_ENV_JAR = "TIKA_JAR"
_DEFAULT_JAR = Path.home() / ".cache" / "filetype-detector" / f"tika-app-{TIKA_VERSION}.jar"
_PROBE = Path(__file__).with_name("TikaDetect.java")

_JAVA_OPTIONS = (
    "-Dfile.encoding=UTF-8",
    "-Duser.language=en",
    "-Duser.country=US",
    "-Duser.timezone=UTC",
)


class TikaInferencer(BaseInferencer):
    """Infers file type using Apache Tika.

    Detects MIME type from file content (with the real filename as a hint) and
    maps it to extensions using Tika's built-in MIME repository, so results do
    not depend on the OS MIME database.

    Parameters
    ----------
    jar_path : Path | str, optional
        Path to ``tika-app-<version>.jar``. When omitted, the ``TIKA_JAR``
        environment variable is used, then ``~/.cache/filetype-detector/``.
        The JAR is verified against the pinned SHA-512 before first use.

    Raises
    ------
    FileNotFoundError
        Raised on first :meth:`detect` when no verified JAR is found. Call
        :meth:`download_jar` or set ``TIKA_JAR`` first.
    RuntimeError
        Raised when Java is not available or the JAR fails verification.

    Examples
    --------
    >>> inferencer = TikaInferencer()
    >>> ft = inferencer.detect('document.pdf')
    >>> '.pdf' in ft.extensions
    True

    Notes
    -----
    Requires Java 11+ on ``PATH``. The JAR is downloaded once via
    :meth:`download_jar` and reused; nothing is downloaded at import time.
    """

    def __init__(self, jar_path: Path | str | None = None) -> None:
        env_value = os.environ.get(_ENV_JAR)
        resolved = jar_path or (env_value if env_value else _DEFAULT_JAR)
        self._jar = Path(resolved)
        self._process: subprocess.Popen | None = None
        self._lock = threading.Lock()

    @staticmethod
    def default_jar_path() -> Path:
        """Return the default JAR location inside the user cache directory."""
        return _DEFAULT_JAR

    @classmethod
    def download_jar(cls, jar_path: Path | str | None = None) -> Path:
        """Download the pinned Tika JAR and verify its SHA-512.

        Parameters
        ----------
        jar_path : Path | str, optional
            Destination path. Defaults to :meth:`default_jar_path`.

        Returns
        -------
        Path
            Path of the verified JAR.
        """
        target = Path(jar_path) if jar_path else _DEFAULT_JAR
        if target.exists():
            if cls._digest(target) != TIKA_SHA512:
                raise ValueError(
                    f"Existing JAR has unexpected SHA-512; refusing to overwrite: {target}"
                )
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".download")
        try:
            urllib.request.urlretrieve(TIKA_URL, tmp)
            if cls._digest(tmp) != TIKA_SHA512:
                tmp.unlink(missing_ok=True)
                raise ValueError("Downloaded JAR failed SHA-512 verification")
            os.replace(tmp, target)
        finally:
            tmp.unlink(missing_ok=True)
        return target

    @staticmethod
    def _digest(path: Path) -> str:
        return hashlib.sha512(path.read_bytes()).hexdigest()

    def _verify_jar(self) -> Path:
        if not self._jar.exists():
            raise FileNotFoundError(
                f"Tika JAR not found at {self._jar}. "
                f"Run {type(self).__name__}.download_jar() or set {_ENV_JAR}."
            )
        if self._digest(self._jar) != TIKA_SHA512:
            raise ValueError(
                f"Tika JAR SHA-512 mismatch (expected pinned "
                f"{TIKA_VERSION} build): {self._jar}"
            )
        return self._jar

    def _ensure_process(self) -> subprocess.Popen:
        if self._process is not None and self._process.poll() is None:
            return self._process
        jar = self._verify_jar()
        command = ["java", *_JAVA_OPTIONS, "--class-path", str(jar), str(_PROBE)]
        try:
            self._process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as e:
            raise RuntimeError(
                "Java not found on PATH; TikaInferencer requires Java 11+"
            ) from e
        return self._process

    def detect(self, file_path: Path | str) -> FileType:
        """Detect file type using Apache Tika.

        Parameters
        ----------
        file_path : Path | str
            The file path to analyze.

        Returns
        -------
        FileType
            FileType instance containing Tika's MIME type and bundled extensions.

        Raises
        ------
        FileNotFoundError
            Raised when the file or the verified JAR does not exist.
        ValueError
            Raised when the path is not a file or the JAR fails verification.
        RuntimeError
            Raised when Java is unavailable, the probe exits, or Tika reports
            a detection error.
        """
        path_obj = self._validate_path(file_path)
        with self._lock:
            process = self._ensure_process()
            assert process.stdin is not None and process.stdout is not None
            try:
                process.stdin.write(f"{path_obj}\n".encode())
                process.stdin.flush()
                raw = process.stdout.readline()
            except (BrokenPipeError, OSError) as e:
                self._process = None
                raise RuntimeError(f"Tika probe process failed: {e}") from e
        if not raw:
            self._process = None
            raise RuntimeError(
                "Tika probe exited unexpectedly; check java.stderr is enabled"
            )
        fields = raw.decode("utf-8").rstrip("\n").split("\t")
        if fields[0] != "ok":
            detail = (
                base64.b64decode(fields[1]).decode("utf-8", errors="replace")
                if len(fields) > 1
                else "unknown error"
            )
            raise RuntimeError(f"Tika failed to detect {path_obj}: {detail.strip()}")
        mime = base64.b64decode(fields[1]).decode("utf-8")
        extensions = base64.b64decode(fields[2]).decode("utf-8")
        return FileType(
            extensions=tuple(extensions.split(",")) if extensions else (),
            mime_types=(mime,) if mime else (),
        )

    def close(self) -> None:
        """Shut down the JVM process. Safe to call multiple times."""
        with self._lock:
            if self._process is not None:
                try:
                    if self._process.stdin is not None:
                        self._process.stdin.close()
                    self._process.wait(timeout=10)
                except (OSError, subprocess.TimeoutExpired):
                    self._process.kill()
                finally:
                    self._process = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
