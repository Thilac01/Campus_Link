import struct

import pytest

from campuslink.network.protocol import (
    MAX_FRAME_SIZE,
    FrameDecoder,
    MessageType,
    ProtocolError,
    ProtocolMessage,
    encode_frame,
)


def test_fragmented_frame_is_reassembled():
    message = ProtocolMessage(MessageType.HELLO, "abc", {"name": "Ada"})
    encoded = encode_frame(message)
    decoder = FrameDecoder()
    assert decoder.feed(encoded[:3]) == []
    assert decoder.feed(encoded[3:]) == [message]


def test_multiple_frames_are_decoded():
    first = ProtocolMessage(MessageType.HEARTBEAT, "1", {})
    second = ProtocolMessage(MessageType.DISCONNECT, "2", {"reason": "shutdown"})
    assert FrameDecoder().feed(encode_frame(first) + encode_frame(second)) == [first, second]


def test_oversized_declared_frame_is_rejected():
    with pytest.raises(ProtocolError):
        FrameDecoder().feed(struct.pack("!I", MAX_FRAME_SIZE + 1))

