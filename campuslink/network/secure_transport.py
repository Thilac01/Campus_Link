"""Pinned TLS 1.3 peer transport with challenge-response client authentication."""

from __future__ import annotations

import asyncio
import base64
import os
import ssl
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from campuslink.identity.device import DeviceIdentity, certificate_fingerprint
from campuslink.identity.trust import TrustStore
from campuslink.network.protocol import (
    HEADER,
    MAX_FRAME_SIZE,
    MessageType,
    ProtocolError,
    ProtocolMessage,
    encode_frame,
)


class AuthenticationError(PermissionError):
    pass


@dataclass(frozen=True, slots=True)
class AuthenticatedPeer:
    device_id: str
    display_name: str
    fingerprint: str


MessageHandler = Callable[[AuthenticatedPeer, ProtocolMessage], Awaitable[dict[str, object]]]


def _server_context(identity: DeviceIdentity) -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.load_cert_chain(identity.certificate_path, identity.private_key_path)
    return context


def _client_context() -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


async def _read_message(reader: asyncio.StreamReader) -> ProtocolMessage:
    header = await reader.readexactly(HEADER.size)
    length = HEADER.unpack(header)[0]
    if length <= 0 or length > MAX_FRAME_SIZE:
        raise ProtocolError("Invalid frame length")
    body = await reader.readexactly(length)
    from campuslink.network.protocol import FrameDecoder

    decoded = FrameDecoder().feed(header + body)
    if len(decoded) != 1:
        raise ProtocolError("Expected one protocol message")
    return decoded[0]


async def _write_message(writer: asyncio.StreamWriter, message: ProtocolMessage) -> None:
    writer.write(encode_frame(message))
    await writer.drain()


def _private_key(identity: DeviceIdentity) -> ec.EllipticCurvePrivateKey:
    key = serialization.load_pem_private_key(identity.private_key_path.read_bytes(), password=None)
    if not isinstance(key, ec.EllipticCurvePrivateKey):
        raise TypeError("CampusLink identity key must be elliptic-curve")
    return key


def _auth_payload(identity: DeviceIdentity, challenge: bytes) -> dict[str, object]:
    certificate_pem = identity.certificate_path.read_bytes()
    signature = _private_key(identity).sign(challenge, ec.ECDSA(hashes.SHA256()))
    return {
        "device_id": identity.device_id,
        "display_name": identity.display_name,
        "certificate": base64.b64encode(certificate_pem).decode("ascii"),
        "signature": base64.b64encode(signature).decode("ascii"),
    }


def _verify_auth(
    payload: dict[str, object], challenge: bytes, trust: TrustStore
) -> AuthenticatedPeer:
    try:
        device_id = str(payload["device_id"])
        display_name = str(payload["display_name"])
        certificate_pem = base64.b64decode(str(payload["certificate"]), validate=True)
        signature = base64.b64decode(str(payload["signature"]), validate=True)
        certificate = x509.load_pem_x509_certificate(certificate_pem)
        public_key = certificate.public_key()
        if not isinstance(public_key, ec.EllipticCurvePublicKey):
            raise AuthenticationError("Peer certificate must use an elliptic-curve key")
        public_key.verify(signature, challenge, ec.ECDSA(hashes.SHA256()))
        common_name = certificate.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0]
        if common_name.value != device_id:
            raise AuthenticationError("Certificate device identifier mismatch")
        fingerprint = certificate.fingerprint(hashes.SHA256()).hex().upper()
        trusted = trust.verify(device_id, fingerprint)
        if trusted.state != "trusted":
            raise AuthenticationError("Peer is blocked")
        return AuthenticatedPeer(device_id, display_name, fingerprint)
    except AuthenticationError:
        raise
    except Exception as exc:
        raise AuthenticationError("Peer challenge response is invalid") from exc


class PeerServer:
    def __init__(
        self,
        identity: DeviceIdentity,
        trust: TrustStore,
        handler: MessageHandler,
        host: str = "0.0.0.0",  # noqa: S104 - LAN peers must reach the opted-in listener.
        port: int = 0,
    ) -> None:
        self.identity = identity
        self.trust = trust
        self.handler = handler
        self.host = host
        self.port = port
        self._server: asyncio.Server | None = None

    async def start(self) -> int:
        self._server = await asyncio.start_server(
            self._handle_connection, self.host, self.port, ssl=_server_context(self.identity)
        )
        socket = self._server.sockets[0]
        self.port = int(socket.getsockname()[1])
        return self.port

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            client_challenge = os.urandom(32)
            server_challenge = ProtocolMessage(
                MessageType.AUTH_REQUEST,
                str(uuid.uuid4()),
                {"challenge": base64.b64encode(client_challenge).decode("ascii")},
            )
            await _write_message(writer, server_challenge)
            client_auth = await asyncio.wait_for(_read_message(reader), timeout=10)
            if client_auth.message_type is not MessageType.AUTH_RESPONSE:
                raise AuthenticationError("Expected AUTH_RESPONSE")
            peer = _verify_auth(client_auth.payload, client_challenge, self.trust)

            server_nonce = base64.b64decode(str(client_auth.payload["server_challenge"]))
            await _write_message(
                writer,
                ProtocolMessage(
                    MessageType.AUTH_RESPONSE,
                    str(uuid.uuid4()),
                    _auth_payload(self.identity, server_nonce),
                ),
            )
            message = await asyncio.wait_for(_read_message(reader), timeout=30)
            response_payload = await self.handler(peer, message)
            response_type = (
                MessageType.CHAT_ACK
                if message.message_type is MessageType.CHAT_MESSAGE
                else MessageType.HEARTBEAT
            )
            await _write_message(
                writer,
                ProtocolMessage(response_type, message.message_id, response_payload),
            )
        except (AuthenticationError, ProtocolError, TimeoutError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()


class PeerClient:
    def __init__(self, identity: DeviceIdentity, trust: TrustStore) -> None:
        self.identity = identity
        self.trust = trust

    async def request(
        self, host: str, port: int, message: ProtocolMessage
    ) -> tuple[AuthenticatedPeer, ProtocolMessage]:
        reader, writer = await asyncio.open_connection(
            host, port, ssl=_client_context(), server_hostname=None
        )
        try:
            ssl_object = writer.get_extra_info("ssl_object")
            peer_der = ssl_object.getpeercert(binary_form=True)
            pinned_fingerprint = certificate_fingerprint(peer_der)
            challenge_message = await asyncio.wait_for(_read_message(reader), timeout=10)
            if challenge_message.message_type is not MessageType.AUTH_REQUEST:
                raise AuthenticationError("Expected AUTH_REQUEST")
            challenge = base64.b64decode(str(challenge_message.payload["challenge"]))
            server_challenge = os.urandom(32)
            payload = _auth_payload(self.identity, challenge)
            payload["server_challenge"] = base64.b64encode(server_challenge).decode("ascii")
            await _write_message(
                writer,
                ProtocolMessage(MessageType.AUTH_RESPONSE, str(uuid.uuid4()), payload),
            )
            server_auth = await asyncio.wait_for(_read_message(reader), timeout=10)
            server_peer = _verify_auth(server_auth.payload, server_challenge, self.trust)
            if server_peer.fingerprint != pinned_fingerprint:
                raise AuthenticationError("TLS certificate does not match authenticated identity")
            await _write_message(writer, message)
            response = await asyncio.wait_for(_read_message(reader), timeout=30)
            return server_peer, response
        finally:
            writer.close()
            await writer.wait_closed()
