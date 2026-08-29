"""macOS metadata fixture generators."""

from io import BytesIO
import struct

from ds_store import DSStore, DSStoreEntry

from .base import BaseGenerator
from . import register


class _NonClosingBytesIO(BytesIO):
    """Keep the generated buffer readable after DSStore closes its handle."""

    def close(self) -> None:
        pass


@register
class MacOSGenerator(BaseGenerator):
    """Generate deterministic macOS DS_Store files."""

    @property
    def extensions(self) -> list[str]:
        return ["dsstore"]

    @property
    def sources(self) -> dict[str, str]:
        return {"dsstore": "library:ds-store==1.3.3"}

    @property
    def category(self) -> str:
        return "metadata"

    def generate(self, ext: str) -> bytes:
        if ext != "dsstore":
            raise KeyError(ext)
        buffer = _NonClosingBytesIO()
        entry = DSStoreEntry("hello.txt", "Iloc", "blob", struct.pack(">II", 0, 0))
        with DSStore.open(buffer, "w+", initial_entries=[entry]):
            pass
        return buffer.getvalue()
