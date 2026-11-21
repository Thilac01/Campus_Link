"""Device certificates used by the authenticated TLS transport."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


@dataclass(frozen=True, slots=True)
class DeviceIdentity:
    device_id: str
    display_name: str
    certificate_path: Path
    private_key_path: Path
    fingerprint: str

    @property
    def pairing_code(self) -> str:
        compact = self.fingerprint.replace(":", "")[:12]
        return "-".join(compact[index : index + 4] for index in range(0, 12, 4))


class IdentityStore:
    """Creates one long-lived device identity within an application data directory."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.metadata_path = directory / "identity.json"
        self.certificate_path = directory / "device-cert.pem"
        self.private_key_path = directory / "device-key.pem"

    def load_or_create(self, display_name: str) -> DeviceIdentity:
        if self._complete():
            return self._load()
        return self._create(display_name)

    def _complete(self) -> bool:
        return all(
            path.is_file()
            for path in (self.metadata_path, self.certificate_path, self.private_key_path)
        )

    def _load(self) -> DeviceIdentity:
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        certificate = x509.load_pem_x509_certificate(self.certificate_path.read_bytes())
        actual_fingerprint = certificate.fingerprint(hashes.SHA256()).hex().upper()
        if actual_fingerprint != metadata["fingerprint"]:
            raise ValueError("Device certificate fingerprint does not match identity metadata")
        return DeviceIdentity(
            device_id=metadata["device_id"],
            display_name=metadata["display_name"],
            certificate_path=self.certificate_path,
            private_key_path=self.private_key_path,
            fingerprint=actual_fingerprint,
        )

    def _create(self, display_name: str) -> DeviceIdentity:
        self.directory.mkdir(parents=True, exist_ok=True)
        private_key = ec.generate_private_key(ec.SECP256R1())
        device_id = str(uuid.uuid4())
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CampusLink local device"),
                x509.NameAttribute(NameOID.COMMON_NAME, device_id),
            ]
        )
        now = datetime.now(UTC)
        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=825))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(f"{device_id}.campuslink.local")]),
                critical=False,
            )
            .sign(private_key, hashes.SHA256())
        )
        self.private_key_path.write_bytes(
            private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        self.certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
        fingerprint = certificate.fingerprint(hashes.SHA256()).hex().upper()
        self.metadata_path.write_text(
            json.dumps(
                {
                    "device_id": device_id,
                    "display_name": display_name,
                    "fingerprint": fingerprint,
                    "created_at": now.isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        if os.name != "nt":
            os.chmod(self.private_key_path, 0o600)
        return self._load()


def certificate_fingerprint(certificate_der: bytes) -> str:
    """Return a stable uppercase SHA-256 fingerprint for a peer certificate."""
    return hashlib.sha256(certificate_der).hexdigest().upper()

