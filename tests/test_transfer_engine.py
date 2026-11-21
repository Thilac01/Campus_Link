import hashlib
import threading

import pytest

from campuslink.transfers.engine import ResumableCopy, TransferCancelled


def test_streaming_copy_is_hash_verified_and_atomic(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes((b"CampusLink" * 20_000) + b"end")
    destination = tmp_path / "received.bin"
    result = ResumableCopy(64 * 1024).copy(source, destination)
    assert destination.read_bytes() == source.read_bytes()
    assert result.sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
    assert not list(tmp_path.glob("*.campuslink-part"))


def test_cancelled_copy_can_resume(tmp_path):
    source = tmp_path / "large.bin"
    source.write_bytes(b"x" * (512 * 1024))
    destination = tmp_path / "received.bin"
    cancel = threading.Event()

    def progress(transferred, total, speed):
        del total, speed
        if transferred >= 128 * 1024:
            cancel.set()

    with pytest.raises(TransferCancelled):
        ResumableCopy(64 * 1024).copy(
            source, destination, progress=progress, cancel=cancel
        )
    result = ResumableCopy(64 * 1024).copy(source, destination)
    assert result.resumed_from >= 128 * 1024
    assert destination.read_bytes() == source.read_bytes()
