"""Versioned, length-prefixed protocol primitives."""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

HEADER = struct.Struct("!I")
MAX_FRAME_SIZE = 4 * 1024 * 1024
PROTOCOL_VERSION = 1


class ProtocolError(ValueError):
    """A peer supplied an invalid protocol frame."""


class MessageType(StrEnum):
    HELLO = "HELLO"
    AUTH_REQUEST = "AUTH_REQUEST"
    AUTH_RESPONSE = "AUTH_RESPONSE"
    CHAT_MESSAGE = "CHAT_MESSAGE"
    CHAT_ACK = "CHAT_ACK"
    FILE_OFFER = "FILE_OFFER"
    FILE_ACCEPT = "FILE_ACCEPT"
    FILE_RESUME = "FILE_RESUME"
    FILE_COMPLETE = "FILE_COMPLETE"
    HEARTBEAT = "HEARTBEAT"
    DISCONNECT = "DISCONNECT"


@dataclass(frozen=True, slots=True)
class ProtocolMessage:
    message_type: MessageType
    message_id: str
    payload: dict[str, Any]
    version: int = PROTOCOL_VERSION


def encode_frame(message: ProtocolMessage) -> bytes:
    document = {
        "version": message.version, "type": message.message_type.value,
        "id": message.message_id, "payload": message.payload,
    }
    body = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(body) > MAX_FRAME_SIZE:
        raise ProtocolError("Frame exceeds maximum size")
    return HEADER.pack(len(body)) + body


class FrameDecoder:
    """Incrementally decode fragmented or coalesced TCP reads."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[ProtocolMessage]:
        self._buffer.extend(data)
        messages: list[ProtocolMessage] = []
        while len(self._buffer) >= HEADER.size:
            length = HEADER.unpack_from(self._buffer)[0]
            if length <= 0 or length > MAX_FRAME_SIZE:
                raise ProtocolError("Invalid frame length")
            frame_end = HEADER.size + length
            if len(self._buffer) < frame_end:
                break
            body = bytes(self._buffer[HEADER.size:frame_end])
            del self._buffer[:frame_end]
            messages.append(_decode_body(body))
        return messages


def _decode_body(body: bytes) -> ProtocolMessage:
    try:
        document = json.loads(body.decode("utf-8"))
        if not isinstance(document, dict) or not isinstance(document.get("payload"), dict):
            raise ProtocolError("Frame body must contain an object payload")
        version = int(document["version"])
        if version != PROTOCOL_VERSION:
            raise ProtocolError(f"Unsupported protocol version: {version}")
        message_id = document["id"]
        if not isinstance(message_id, str) or not message_id or len(message_id) > 128:
            raise ProtocolError("Invalid message identifier")
        return ProtocolMessage(
            message_type=MessageType(document["type"]), message_id=message_id,
            payload=document["payload"], version=version,
        )
    except ProtocolError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ProtocolError("Malformed protocol frame") from exc

