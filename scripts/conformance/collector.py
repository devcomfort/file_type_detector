"""Collect backend observations in fresh Python subprocesses."""

from __future__ import annotations

import argparse
import json
import os
import hashlib
import platform
import subprocess
import sys
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from typing import Any, Iterator

from scripts.conformance.evaluator import evaluate_output, semantic_output
from scripts.conformance.inventory import load_verified_inventory
from scripts.conformance.types import InventoryRecord


class CollectionValidationError(ValueError):
    """Raised when no reviewed records are available to collect."""


@contextmanager
def stage_probe(record: InventoryRecord, *, root: Path) -> Iterator[Path]:
    """Copy a reviewed fixture to a temporary path with its declared suffix."""
    with TemporaryDirectory(prefix="filetype-conformance-") as directory:
        if record.probe_filename:
            probe = Path(directory, record.probe_filename)
        else:
            probe = Path(directory, f"probe{record.probe_extension}")
        copyfile(root / record.fixture.path, probe)
        if _file_digest(probe) != record.fixture.sha256:
            raise ValueError(
                f"{record.id} staged probe digest does not match reviewed digest"
            )
        yield probe


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_observation(
    record: InventoryRecord,
    *,
    backend: str,
    root: Path,
    runner_label: str,
) -> dict[str, object]:
    """Collect one backend result without substituting another backend."""
    platform_info = _platform_info(runner_label)
    runtime_info = _runtime_info()
    try:
        inferencer = _inferencer_for_backend(backend)
        with stage_probe(record, root=root) as probe:
            result = inferencer.infer(probe)
    except Exception as error:
        return _error_observation(
            record=record,
            backend=backend,
            platform_info=platform_info,
            runtime_info=runtime_info,
            error=error,
        )

    raw_output = {
        "mime_types": list(result.mime_types),
        "extensions": list(result.extensions),
    }
    semantic = semantic_output(
        mime_types=result.mime_types,
        extensions=result.extensions,
    )
    status = "no_result" if not any(raw_output.values()) else "ok"
    return {
        "inventory_id": record.id,
        "backend": backend,
        "platform": platform_info,
        "runtime": runtime_info,
        "raw_output": raw_output,
        "semantic_output": semantic,
        "status": status,
        "error": None,
        "evaluation": evaluate_output(
            semantic=semantic,
            ground_truth=record.ground_truth,
            status=status,
            probe_name=probe.name if "probe" in locals() else (record.probe_filename or None),
        ),
    }


def collect_inventory(
    *,
    candidates_path: Path,
    inventory_path: Path,
    root: Path,
    runner_label: str,
) -> dict[str, object]:
    """Collect one fresh-process observation per authoritative record/backend."""
    records = load_verified_inventory(
        candidates_path,
        inventory_path,
        root=root,
    )
    if not records:
        raise CollectionValidationError("authoritative inventory is empty")
    observations: list[dict[str, object]] = []
    for record in records:
        for backend in record.backends:
            observations.append(
                _collect_in_worker(
                    candidates_path=candidates_path,
                    inventory_path=inventory_path,
                    root=root,
                    runner_label=runner_label,
                    inventory_id=record.id,
                    backend=backend,
                )
            )
    return {
        "schema_version": 1,
        "inventory_sha256": _file_digest(inventory_path),
        "observations": observations,
    }


def _collect_in_worker(
    *,
    candidates_path: Path,
    inventory_path: Path,
    root: Path,
    runner_label: str,
    inventory_id: str,
    backend: str,
) -> dict[str, object]:
    command = [
        sys.executable,
        "-m",
        "scripts.conformance.collector",
        "worker",
        "--candidates",
        str(candidates_path.resolve()),
        "--inventory",
        str(inventory_path.resolve()),
        "--root",
        str(root.resolve()),
        "--runner-label",
        runner_label,
        "--inventory-id",
        inventory_id,
        "--backend",
        backend,
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode == 0:
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            return payload

    return _error_observation(
        record_id=inventory_id,
        backend=backend,
        platform_info=_platform_info(runner_label),
        runtime_info=_runtime_info(),
        error=RuntimeError(
            f"Worker exited with {completed.returncode}: {completed.stderr.strip()}"
        ),
    )


def _error_observation(
    *,
    backend: str,
    platform_info: dict[str, str],
    runtime_info: dict[str, str | None],
    error: Exception,
    record: InventoryRecord | None = None,
    record_id: str | None = None,
) -> dict[str, object]:
    """Serialize a visible failure without treating it as a detection result."""
    inventory_id = record.id if record is not None else record_id
    if inventory_id is None:
        raise ValueError("An error observation requires an inventory ID")
    ground_truth = record.ground_truth if record is not None else None
    empty_output: dict[str, list[str]] = {"mime_types": [], "extensions": []}
    return {
        "inventory_id": inventory_id,
        "backend": backend,
        "platform": platform_info,
        "runtime": runtime_info,
        "raw_output": None,
        "semantic_output": None,
        "status": "error",
        "error": {"type": type(error).__name__, "message": str(error)},
        "evaluation": evaluate_output(
            semantic=empty_output,
            ground_truth=ground_truth
            if ground_truth is not None
            else _empty_ground_truth(),
            status="error",
        ),
    }


def _empty_ground_truth() -> Any:
    from scripts.conformance.types import GroundTruth

    return GroundTruth(mimes=(), extensions=())


def _inferencer_for_backend(backend: str) -> Any:
    if backend == "lexical":
        from filetype_detector.strategies.lexical_inferencer import LexicalInferencer

        return LexicalInferencer()
    if backend == "magic":
        from filetype_detector.strategies.magic_inferencer import MagicInferencer

        return MagicInferencer()
    if backend == "magika":
        from filetype_detector.strategies.magika_inferencer import MagikaInferencer

        return MagikaInferencer()
    if backend == "hybrid":
        from filetype_detector.strategies.hybrid_inferencer import HybridInferencer

        return HybridInferencer()
    raise ValueError(f"Unsupported backend: {backend}")


def _platform_info(runner_label: str) -> dict[str, str]:
    return {
        "os": platform.system(),
        "architecture": platform.machine(),
        "runner_label": runner_label,
    }


def _runtime_info() -> dict[str, str | None]:
    magika_module, magika_model = _magika_versions()
    return {
        "python": platform.python_version(),
        "filetype_detector": _package_version("filetype-detector"),
        "python_magic": _package_version("python-magic"),
        "libmagic": _libmagic_version(),
        "libmagic_distribution": os.getenv("LIBMAGIC_DISTRIBUTION") or None,
        "magika": magika_module or _package_version("magika"),
        "magika_model": magika_model,
    }


def _package_version(distribution: str) -> str | None:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


def _libmagic_version() -> str | None:
    try:
        import magic

        return str(magic.version())
    except Exception:
        return None


def _magika_versions() -> tuple[str | None, str | None]:
    try:
        from magika import Magika

        detector = Magika()
        return (
            _magika_metadata(detector, "get_module_version"),
            _magika_metadata(detector, "get_model_version"),
        )
    except Exception:
        return None, None


def _magika_metadata(detector: Any, attribute: str) -> str | None:
    getter = getattr(detector, attribute, None)
    if not callable(getter):
        return None
    try:
        return str(getter())
    except Exception:
        return None


def _runner_label(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("runner label must be non-empty")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command_name in ("collect", "worker"):
        command = commands.add_parser(command_name)
        command.add_argument("--candidates", type=Path, required=True)
        command.add_argument("--inventory", type=Path, required=True)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--runner-label", type=_runner_label, required=True)
        if command_name == "worker":
            command.add_argument("--inventory-id", required=True)
            command.add_argument(
                "--backend",
                choices=("lexical", "magic", "magika", "hybrid"),
                required=True,
            )
        else:
            command.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a collector command."""
    parser = _parser()
    arguments = parser.parse_args(argv)
    if arguments.command == "worker":
        records = load_verified_inventory(
            arguments.candidates,
            arguments.inventory,
            root=arguments.root,
        )
        record = next(
            (item for item in records if item.id == arguments.inventory_id),
            None,
        )
        if record is None:
            raise ValueError(f"Unknown inventory ID: {arguments.inventory_id}")
        if arguments.backend not in record.backends:
            raise ValueError(
                f"{arguments.inventory_id} does not include backend {arguments.backend}"
            )
        print(
            json.dumps(
                collect_observation(
                    record,
                    backend=arguments.backend,
                    root=arguments.root,
                    runner_label=arguments.runner_label,
                ),
                sort_keys=True,
            )
        )
        return 0

    try:
        payload = collect_inventory(
            candidates_path=arguments.candidates,
            inventory_path=arguments.inventory,
            root=arguments.root,
            runner_label=arguments.runner_label,
        )
    except CollectionValidationError as error:
        parser.error(str(error))
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
