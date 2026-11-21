from cryptography import x509
from cryptography.hazmat.primitives import hashes

from campuslink.identity.device import IdentityStore
from campuslink.identity.trust import IdentityChangedError, TrustedPeer, TrustStore


def test_device_identity_is_persistent(tmp_path):
    store = IdentityStore(tmp_path / "identity")
    first = store.load_or_create("Ada")
    second = store.load_or_create("Changed display name")
    assert first == second
    certificate = x509.load_pem_x509_certificate(first.certificate_path.read_bytes())
    assert certificate.fingerprint(hashes.SHA256()).hex().upper() == first.fingerprint
    assert len(first.pairing_code.split("-")) == 3


def test_trust_store_detects_identity_change(tmp_path):
    store = TrustStore(tmp_path / "trusted.json")
    store.trust(TrustedPeer("device-1", "Grace", "AAAA"))
    assert store.verify("device-1", "AAAA").display_name == "Grace"
    try:
        store.verify("device-1", "BBBB")
    except IdentityChangedError:
        pass
    else:
        raise AssertionError("identity change was accepted")
