"""Manual secure pairing and one-to-one chat workspace."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from campuslink.app.network_worker import NetworkWorker
from campuslink.database.store import Database
from campuslink.identity.device import DeviceIdentity
from campuslink.identity.trust import TrustedPeer, TrustStore


class ChatPage(QWidget):
    def __init__(
        self,
        database: Database,
        identity: DeviceIdentity,
        trust: TrustStore,
        network: NetworkWorker,
    ) -> None:
        super().__init__()
        self.database = database
        self.identity = identity
        self.trust = trust
        self.network = network
        self.pending_peer: dict[str, tuple[str, str]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        title = QLabel("Secure chat")
        title.setObjectName("pageTitle")
        self.listener = QLabel("Starting secure listener…")
        self.listener.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(self.listener)
        layout.addWidget(self._pairing_card())

        self.messages = QListWidget()
        self.messages.setWordWrap(True)
        layout.addWidget(self.messages, 1)

        compose = QHBoxLayout()
        self.message = QLineEdit()
        self.message.setPlaceholderText("Write a message")
        self.message.setMaxLength(65_536)
        self.message.returnPressed.connect(self._send)
        send = QPushButton("Send")
        send.setObjectName("primary")
        send.clicked.connect(self._send)
        compose.addWidget(self.message, 1)
        compose.addWidget(send)
        layout.addLayout(compose)

        network.listening.connect(self._listener_ready)
        network.incoming_chat.connect(self._incoming)
        network.send_completed.connect(self._send_finished)
        network.network_error.connect(self._network_error)

    def _pairing_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        outer = QVBoxLayout(card)
        own = QLabel(
            f"Your device ID: {self.identity.device_id}\n"
            f"Verification code: {self.identity.pairing_code}"
        )
        own.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        outer.addWidget(own)

        form = QFormLayout()
        self.peer_name = QLineEdit()
        self.peer_name.setPlaceholderText("Peer display name")
        self.peer_id = QLineEdit()
        self.peer_id.setPlaceholderText("Peer device ID")
        self.peer_fingerprint = QLineEdit()
        self.peer_fingerprint.setPlaceholderText("Full certificate fingerprint")
        self.host = QLineEdit("127.0.0.1")
        self.port = QSpinBox()
        self.port.setRange(1, 65_535)
        self.port.setValue(49_631)
        form.addRow("Name", self.peer_name)
        form.addRow("Device ID", self.peer_id)
        form.addRow("Fingerprint", self.peer_fingerprint)
        form.addRow("Host", self.host)
        form.addRow("Port", self.port)
        outer.addLayout(form)
        trust_button = QPushButton("Trust verified peer")
        trust_button.clicked.connect(self._trust_peer)
        outer.addWidget(trust_button)
        return card

    def _listener_ready(self, port: int) -> None:
        self.listener.setText(f"Listening securely on port {port}")

    def _trust_peer(self) -> None:
        try:
            peer = TrustedPeer(
                device_id=self.peer_id.text().strip(),
                display_name=self.peer_name.text().strip() or "Trusted peer",
                fingerprint=self.peer_fingerprint.text().replace(":", "").strip().upper(),
            )
            if not peer.device_id or len(peer.fingerprint) != 64:
                raise ValueError("Enter a device ID and full 64-character SHA-256 fingerprint")
            self.trust.trust(peer)
            self._load_history()
        except Exception as exc:
            QMessageBox.warning(self, "Peer not trusted", str(exc))
            return
        QMessageBox.information(
            self,
            "Peer trusted",
            "Verify the displayed pairing code with the peer through a trusted channel "
            "before chatting.",
        )

    def _load_history(self) -> None:
        self.messages.clear()
        for record in self.database.chat_history(self.peer_id.text().strip()):
            prefix = "You" if record.direction == "outgoing" else self.peer_name.text().strip()
            self.messages.addItem(f"{prefix}: {record.body}  · {record.status}")

    def _send(self) -> None:
        body = self.message.text().strip()
        peer_id = self.peer_id.text().strip()
        peer = self.trust.get(peer_id)
        if not body or peer is None or peer.state != "trusted":
            QMessageBox.warning(self, "Cannot send", "Trust the selected peer and enter a message.")
            return
        message_id = self.database.save_chat_message(
            peer_id, peer.display_name, "outgoing", body, "queued"
        )
        self.pending_peer[message_id] = (peer_id, peer.display_name)
        self.messages.addItem(f"You: {body}  · queued")
        self.message.clear()
        self.network.send_chat(self.host.text().strip(), self.port.value(), body, message_id)

    def _incoming(self, device_id: str, name: str, message_id: str, body: str) -> None:
        self.database.save_chat_message(
            device_id, name, "incoming", body, "delivered", message_id
        )
        self.messages.addItem(f"{name}: {body}  · delivered")
        self.messages.scrollToBottom()

    def _send_finished(self, message_id: str, delivered: bool, detail: str) -> None:
        self.database.update_message_status(message_id, "delivered" if delivered else "failed")
        self._load_history()
        if not delivered:
            QMessageBox.warning(self, "Message not delivered", detail)

    def _network_error(self, detail: str) -> None:
        self.listener.setText(f"Network unavailable: {detail}")
