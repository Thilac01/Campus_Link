"""Qt-safe bridge to the asynchronous peer transport."""

from __future__ import annotations

import asyncio
import logging
import uuid

from PySide6.QtCore import QThread, Signal

from campuslink.identity.device import DeviceIdentity
from campuslink.identity.trust import TrustStore
from campuslink.network.protocol import MessageType, ProtocolMessage
from campuslink.network.secure_transport import AuthenticatedPeer, PeerClient, PeerServer


class NetworkWorker(QThread):
    listening = Signal(int)
    incoming_chat = Signal(str, str, str, str)
    send_completed = Signal(str, bool, str)
    network_error = Signal(str)

    def __init__(self, identity: DeviceIdentity, trust: TrustStore) -> None:
        super().__init__()
        self.identity = identity
        self.trust = trust
        self._loop: asyncio.AbstractEventLoop | None = None
        self._server: PeerServer | None = None

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._start())
            self._loop.run_forever()
        except Exception as exc:
            logging.exception("Network worker failed")
            self.network_error.emit(str(exc))
        finally:
            if self._server is not None:
                self._loop.run_until_complete(self._server.close())
            self._loop.close()
            self._loop = None

    async def _start(self) -> None:
        self._server = PeerServer(
            self.identity,
            self.trust,
            self._handle_message,
            host="0.0.0.0",  # noqa: S104 - user-enabled LAN listener.
            port=0,
        )
        port = await self._server.start()
        self.listening.emit(port)

    async def _handle_message(
        self, peer: AuthenticatedPeer, message: ProtocolMessage
    ) -> dict[str, object]:
        if message.message_type is not MessageType.CHAT_MESSAGE:
            return {"status": "unsupported"}
        body = message.payload.get("body")
        if not isinstance(body, str) or not body.strip() or len(body) > 65_536:
            return {"status": "rejected"}
        self.incoming_chat.emit(peer.device_id, peer.display_name, message.message_id, body)
        return {"status": "delivered"}

    def send_chat(self, host: str, port: int, body: str, message_id: str | None = None) -> str:
        identifier = message_id or str(uuid.uuid4())
        if self._loop is None:
            self.send_completed.emit(identifier, False, "Network service is not ready")
            return identifier
        future = asyncio.run_coroutine_threadsafe(
            self._send(host, port, body, identifier), self._loop
        )
        future.add_done_callback(lambda completed: completed.exception())
        return identifier

    async def _send(self, host: str, port: int, body: str, message_id: str) -> None:
        try:
            message = ProtocolMessage(MessageType.CHAT_MESSAGE, message_id, {"body": body})
            _, response = await PeerClient(self.identity, self.trust).request(host, port, message)
            delivered = response.payload.get("status") == "delivered"
            detail = "Delivered" if delivered else str(response.payload.get("status", "Rejected"))
            self.send_completed.emit(message_id, delivered, detail)
        except Exception as exc:
            logging.exception("Message delivery failed")
            self.send_completed.emit(message_id, False, str(exc))

    def stop(self) -> None:
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        self.wait(5_000)
