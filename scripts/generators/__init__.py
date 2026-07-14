"""Registry of all fixture generators."""

from .base import BaseGenerator


_generators: dict[str, type[BaseGenerator]] = {}


def register(cls: type[BaseGenerator]) -> type[BaseGenerator]:
    """Decorator to register a generator class."""
    _generators[cls.__name__] = cls
    return cls


def get_generator(name: str) -> type[BaseGenerator]:
    """Get a generator class by name."""
    return _generators[name]


def list_generators() -> dict[str, type[BaseGenerator]]:
    """Return all registered generators."""
    return dict(_generators)


def list_extensions() -> dict[str, list[str]]:
    """Return all extensions grouped by category."""
    result: dict[str, list[str]] = {}
    for cls in _generators.values():
        instance = cls()
        cat = instance.category
        result.setdefault(cat, []).extend(instance.extensions)
    return result


def list_sources() -> dict[str, str]:
    """Return source attribution for all extensions."""
    result: dict[str, str] = {}
    for cls in _generators.values():
        instance = cls()
        result.update(instance.sources)
    return result


from . import (  # noqa: E402, F401
    images,
    audio,
    video,
    archives,
    fonts,
    executables,
    documents,
    data_formats,
    text_formats,
    code_formats,
    certificates,
    downloads,
)
