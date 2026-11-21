"""Streaming file copy engine shared by future peer bulk transports."""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_CHUNK_SIZE = 1024 * 1024
ProgressCallback = Callable[[int, int, float], None]


class TransferCancelled(RuntimeError):
    pass


class SourceChangedError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class TransferManifest:
    transfer_id: str
    source_path: str
    destination_path: str
    source_size: int
    source_mtime_ns: int
    chunk_size: int


@dataclass(frozen=True, slots=True)
class TransferResult:
    transfer_id: str
    bytes_copied: int
    sha256: str
    resumed_from: int
    elapsed_seconds: float


class ResumableCopy:
    """Copy one file with bounded memory, durable offset state, and atomic finalization."""

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE) -> None:
        if chunk_size < 64 * 1024 or chunk_size > 16 * 1024 * 1024:
            raise ValueError("Chunk size must be between 64 KiB and 16 MiB")
        self.chunk_size = chunk_size

    def copy(
        self,
        source: Path,
        destination: Path,
        *,
        progress: ProgressCallback | None = None,
        cancel: threading.Event | None = None,
        pause: threading.Event | None = None,
    ) -> TransferResult:
        source = source.resolve(strict=True)
        destination = destination.resolve(strict=False)
        if not source.is_file():
            raise ValueError("Source must be a regular file")
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_name(f".{destination.name}.campuslink-part")
        state_path = partial.with_suffix(partial.suffix + ".json")
        manifest = self._manifest(source, destination, state_path)
        resumed_from = self._resume_offset(source, partial, manifest)
        started = time.monotonic()
        transferred = resumed_from

        mode = "r+b" if partial.exists() else "w+b"
        try:
            with source.open("rb", buffering=self.chunk_size) as source_file, partial.open(
                mode, buffering=self.chunk_size
            ) as destination_file:
                source_file.seek(resumed_from)
                destination_file.seek(resumed_from)
                while transferred < manifest.source_size:
                    if cancel and cancel.is_set():
                        raise TransferCancelled(
                            "Transfer cancelled; partial data retained for resume"
                        )
                    while pause and pause.is_set():
                        if cancel and cancel.is_set():
                            raise TransferCancelled(
                                "Transfer cancelled; partial data retained for resume"
                            )
                        time.sleep(0.1)
                    chunk = source_file.read(self.chunk_size)
                    if not chunk:
                        break
                    destination_file.write(chunk)
                    transferred += len(chunk)
                    destination_file.flush()
                    self._write_state(state_path, manifest, transferred)
                    if progress:
                        elapsed = max(time.monotonic() - started, 0.001)
                        progress(
                            transferred,
                            manifest.source_size,
                            (transferred - resumed_from) / elapsed,
                        )
                os.fsync(destination_file.fileno())

            current = source.stat()
            if (
                current.st_size != manifest.source_size
                or current.st_mtime_ns != manifest.source_mtime_ns
            ):
                raise SourceChangedError("Source changed during transfer")
            if transferred != manifest.source_size:
                raise OSError("Source ended before its declared size")
            digest = _sha256(partial, self.chunk_size)
            os.replace(partial, destination)
            state_path.unlink(missing_ok=True)
            return TransferResult(
                transfer_id=manifest.transfer_id,
                bytes_copied=transferred,
                sha256=digest,
                resumed_from=resumed_from,
                elapsed_seconds=time.monotonic() - started,
            )
        except Exception:
            self._write_state(state_path, manifest, transferred)
            raise

    def _manifest(
        self, source: Path, destination: Path, state_path: Path
    ) -> TransferManifest:
        stat = source.stat()
        if state_path.exists():
            document = json.loads(state_path.read_text(encoding="utf-8"))
            stored = TransferManifest(**document["manifest"])
            expected = (str(source), str(destination), stat.st_size, stat.st_mtime_ns)
            actual = (
                stored.source_path,
                stored.destination_path,
                stored.source_size,
                stored.source_mtime_ns,
            )
            if actual != expected:
                raise SourceChangedError("Existing partial transfer does not match the source")
            return stored
        return TransferManifest(
            transfer_id=str(uuid.uuid4()),
            source_path=str(source),
            destination_path=str(destination),
            source_size=stat.st_size,
            source_mtime_ns=stat.st_mtime_ns,
            chunk_size=self.chunk_size,
        )

    @staticmethod
    def _resume_offset(source: Path, partial: Path, manifest: TransferManifest) -> int:
        del source
        if not partial.exists():
            return 0
        size = partial.stat().st_size
        if size > manifest.source_size:
            raise SourceChangedError("Partial file is larger than the source")
        return size

    @staticmethod
    def _write_state(
        path: Path, manifest: TransferManifest, transferred: int
    ) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps({"manifest": asdict(manifest), "transferred": transferred}, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, path)


def _sha256(path: Path, chunk_size: int) -> str:
    digest = hashlib.sha256()
    with path.open("rb", buffering=chunk_size) as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
