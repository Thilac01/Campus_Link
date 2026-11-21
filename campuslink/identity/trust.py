"""Explicit device trust records with identity-change detection."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TrustedPeer:
    device_id: str
    display_name: str
    fingerprint: str
    state: str = "trusted"


class IdentityChangedError(ValueError):
    pass


class TrustStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def all_peers(self) -> list[TrustedPeer]:
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []
        return [TrustedPeer(**item) for item in document if isinstance(item, dict)]

    def get(self, device_id: str) -> TrustedPeer | None:
        return next((peer for peer in self.all_peers() if peer.device_id == device_id), None)

    def trust(self, peer: TrustedPeer) -> None:
        peers = {item.device_id: item for item in self.all_peers()}
        existing = peers.get(peer.device_id)
        if existing and existing.fingerprint != peer.fingerprint:
            raise IdentityChangedError("The peer certificate changed; re-verification is required")
        peers[peer.device_id] = peer
        self._save(list(peers.values()))

    def verify(self, device_id: str, fingerprint: str) -> TrustedPeer:
        peer = self.get(device_id)
        if peer is None or peer.state != "trusted":
            raise PermissionError("Peer is not trusted")
        if peer.fingerprint != fingerprint:
            raise IdentityChangedError("The peer certificate changed; connection refused")
        return peer

    def block(self, device_id: str) -> None:
        peers = {item.device_id: item for item in self.all_peers()}
        existing = peers.get(device_id)
        if existing is None:
            raise KeyError(device_id)
        peers[device_id] = TrustedPeer(
            device_id=existing.device_id,
            display_name=existing.display_name,
            fingerprint=existing.fingerprint,
            state="blocked",
        )
        self._save(list(peers.values()))

    def _save(self, peers: list[TrustedPeer]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps([asdict(peer) for peer in peers], indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)
